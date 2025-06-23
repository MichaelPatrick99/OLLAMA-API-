"""Router for text generation endpoints with authentication."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any

from database.connection import get_db
from database.models import User
from models.schemas import GenerateRequest, ErrorResponse
from services.ollama_service import OllamaService
from auth.dependencies import (
    get_current_active_user, 
    require_generate_access,
    get_optional_user
)
from auth.services import UsageService
from auth.schemas import UsageLogCreate


router = APIRouter(prefix="/api", tags=["generation"])


def get_ollama_service() -> OllamaService:
    """Dependency to get the Ollama service."""
    return OllamaService()


@router.post(
    "/generate",
    summary="Generate text from a prompt",
    description="Generate text from a prompt using the specified model. Requires authentication.",
    response_description="Generated text",
    responses={
        200: {"description": "Successful response"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def generate_text(
    request: Request,
    generate_request: GenerateRequest,
    current_user: User = Depends(require_generate_access),
    ollama_service: OllamaService = Depends(get_ollama_service),
    db: Session = Depends(get_db)
):
    """Generate text from a prompt.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Required Permission**: `generate:write` 
    
    **Allowed Roles**: 
    - Admin (full access)
    - Developer (full access) 
    - User (full access)
    - Read-Only (❌ no access)
    
    Args:
        request: FastAPI request object
        generate_request: The generation request
        current_user: Currently authenticated user
        ollama_service: The Ollama service
        db: Database session
        
    Returns:
        Generated text (streaming or non-streaming)
    """
    try:
        if generate_request.stream:
            # For streaming responses, we'll track usage after completion
            response = StreamingResponse(
                ollama_service.stream_generate(
                    generate_request.prompt, 
                    generate_request.model, 
                    generate_request.options
                ),
                media_type="text/plain"
            )
            
            # Store user info in response for potential usage tracking
            response.headers["X-User-ID"] = str(current_user.id)
            response.headers["X-Model-Used"] = generate_request.model
            
            return response
        else:
            # Non-streaming response
            result = await ollama_service.generate(
                generate_request.prompt, 
                generate_request.model, 
                generate_request.options
            )
            
            # Track usage for non-streaming
            await _track_generation_usage(
                request=request,
                user=current_user,
                model=generate_request.model,
                prompt=generate_request.prompt,
                response=result.get("response", ""),
                status_code=200,
                db=db
            )
            
            return JSONResponse(result)
            
    except Exception as e:
        # Track failed requests too
        await _track_generation_usage(
            request=request,
            user=current_user,
            model=generate_request.model,
            prompt=generate_request.prompt,
            response="",
            status_code=500,
            db=db
        )
        raise e


@router.get(
    "/generate/models",
    summary="List available models for generation",
    description="Get list of models available for text generation. Requires read access.",
    responses={
        200: {"description": "List of available models"},
        401: {"description": "Authentication required"},
        500: {"description": "Server error"}
    }
)
async def list_generation_models(
    current_user: User = Depends(get_current_active_user),
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """List available models for text generation.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Required Permission**: Basic user access
    
    **Allowed Roles**: All authenticated users
    
    Args:
        current_user: Currently authenticated user
        ollama_service: The Ollama service
        
    Returns:
        List of available models
    """
    models = await ollama_service.list_models()
    
    # Filter or modify model list based on user role if needed
    if current_user.role == "read_only":
        # Read-only users might have limited model access
        # This is where you could implement model-level permissions
        pass
    
    return models


@router.get(
    "/generate/usage",
    summary="Get generation usage statistics",
    description="Get usage statistics for text generation for the current user",
    responses={
        200: {"description": "Usage statistics"},
        401: {"description": "Authentication required"}
    }
)
async def get_generation_usage(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get generation usage statistics for the current user.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    Args:
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Generation usage statistics
    """
    usage_service = UsageService(db)
    
    # Get usage stats filtered to generation endpoints
    stats = usage_service.get_user_usage_stats(current_user.id)
    
    # Filter to generation-related usage
    generation_stats = {
        "total_generations": stats.requests_by_endpoint.get("/api/generate", 0),
        "total_tokens_generated": stats.total_tokens,
        "average_response_time": stats.average_response_time,
        "success_rate": _calculate_success_rate(stats.requests_by_status)
    }
    
    return generation_stats


async def _track_generation_usage(
    request: Request,
    user: User,
    model: str,
    prompt: str,
    response: str,
    status_code: int,
    db: Session
) -> None:
    """Track usage for generation requests.
    
    Args:
        request: FastAPI request object
        user: User making the request
        model: Model used
        prompt: Input prompt
        response: Generated response
        status_code: HTTP status code
        db: Database session
    """
    try:
        usage_service = UsageService(db)
        
        # Estimate tokens (this could be more sophisticated)
        prompt_tokens = len(prompt.split()) if prompt else 0
        completion_tokens = len(response.split()) if response else 0
        
        # Get API key ID if request was made with API key
        api_key_id = None
        if hasattr(request.state, 'api_key'):
            api_key_id = request.state.api_key.id
        
        usage_data = UsageLogCreate(
            endpoint="/api/generate",
            method="POST",
            model_used=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            status_code=status_code,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        usage_service.log_usage(
            usage_data=usage_data,
            user_id=user.id,
            api_key_id=api_key_id
        )
        
    except Exception as e:
        # Don't fail the request if usage tracking fails
        print(f"Failed to track usage: {str(e)}")


def _calculate_success_rate(requests_by_status: dict) -> float:
    """Calculate success rate from status code distribution.
    
    Args:
        requests_by_status: Dictionary of status codes and counts
        
    Returns:
        Success rate as percentage
    """
    total_requests = sum(requests_by_status.values())
    if total_requests == 0:
        return 0.0
    
    successful_requests = sum(
        count for status, count in requests_by_status.items()
        if status.startswith('2')  # 2xx status codes
    )
    
    return (successful_requests / total_requests) * 100