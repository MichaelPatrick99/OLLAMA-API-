"""Router for chat endpoints with authentication."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from database.connection import get_db
from database.models import User
from models.schemas import ChatRequest, ChatMessage, ErrorResponse
from services.ollama_service import OllamaService
from auth.dependencies import (
    get_current_active_user, 
    require_chat_access,
    get_optional_user
)
from auth.services import UsageService
from auth.schemas import UsageLogCreate


router = APIRouter(prefix="/api", tags=["chat"])


def get_ollama_service() -> OllamaService:
    """Dependency to get the Ollama service."""
    return OllamaService()


@router.post(
    "/chat",
    summary="Chat completion",
    description="Generate a chat completion for the given messages. Requires authentication.",
    response_description="Chat completion",
    responses={
        200: {"description": "Successful response"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def chat_completion(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(require_chat_access),
    ollama_service: OllamaService = Depends(get_ollama_service),
    db: Session = Depends(get_db)
):
    """Generate a chat completion.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Required Permission**: `chat:write`
    
    **Allowed Roles**: 
    - Admin (full access)
    - Developer (full access) 
    - User (full access)
    - Read-Only (❌ no access)
    
    **Features**:
    - Multi-turn conversations with message history
    - System prompts for behavior control
    - Streaming and non-streaming responses
    - Usage tracking and analytics
    
    Args:
        request: FastAPI request object
        chat_request: The chat request with messages
        current_user: Currently authenticated user
        ollama_service: The Ollama service
        db: Database session
        
    Returns:
        Chat completion (streaming or non-streaming)
    """
    # Validate message format and content
    _validate_chat_messages(chat_request.messages, current_user)
    
    # Convert Pydantic models to dictionaries for the API
    messages = [msg.dict() for msg in chat_request.messages]
    
    try:
        if chat_request.stream:
            # Streaming response
            response = StreamingResponse(
                ollama_service.stream_chat(
                    messages, 
                    chat_request.model, 
                    chat_request.options
                ),
                media_type="text/plain"
            )
            
            # Add headers for tracking
            response.headers["X-User-ID"] = str(current_user.id)
            response.headers["X-Model-Used"] = chat_request.model
            response.headers["X-Message-Count"] = str(len(messages))
            
            return response
        else:
            # Non-streaming response
            result = await ollama_service.chat(
                messages, 
                chat_request.model, 
                chat_request.options
            )
            
            # Track usage for non-streaming
            await _track_chat_usage(
                request=request,
                user=current_user,
                model=chat_request.model,
                messages=messages,
                response=result.get("message", {}).get("content", ""),
                status_code=200,
                db=db
            )
            
            return JSONResponse(result)
            
    except Exception as e:
        # Track failed requests
        await _track_chat_usage(
            request=request,
            user=current_user,
            model=chat_request.model,
            messages=messages,
            response="",
            status_code=500,
            db=db
        )
        raise e


@router.get(
    "/chat/models",
    summary="List available chat models",
    description="Get list of models available for chat completion. Requires read access.",
    responses={
        200: {"description": "List of available chat models"},
        401: {"description": "Authentication required"},
        500: {"description": "Server error"}
    }
)
async def list_chat_models(
    current_user: User = Depends(get_current_active_user),
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """List available models for chat completion.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Required Permission**: Basic user access
    
    **Allowed Roles**: All authenticated users
    
    Args:
        current_user: Currently authenticated user
        ollama_service: The Ollama service
        
    Returns:
        List of available chat models with capabilities
    """
    models = await ollama_service.list_models()
    
    # Add chat-specific information to models
    if "models" in models:
        for model in models["models"]:
            # Add chat capabilities info
            model["supports_chat"] = True
            model["supports_system_prompts"] = True
            model["max_context_length"] = _get_model_context_length(model.get("name", ""))
            
            # Role-based model filtering could be added here
            if current_user.role == "read_only":
                model["rate_limited"] = True
    
    return models


@router.get(
    "/chat/usage",
    summary="Get chat usage statistics",
    description="Get usage statistics for chat completion for the current user",
    responses={
        200: {"description": "Chat usage statistics"},
        401: {"description": "Authentication required"}
    }
)
async def get_chat_usage(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get chat usage statistics for the current user.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    Args:
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Chat usage statistics
    """
    usage_service = UsageService(db)
    stats = usage_service.get_user_usage_stats(current_user.id)
    
    # Filter to chat-related usage
    chat_stats = {
        "total_conversations": stats.requests_by_endpoint.get("/api/chat", 0),
        "total_messages_processed": stats.total_tokens,  # Approximation
        "average_response_time": stats.average_response_time,
        "success_rate": _calculate_success_rate(stats.requests_by_status),
        "popular_models": _get_popular_models_from_stats(stats),
        "usage_trend": "stable"  # Could implement trend analysis
    }
    
    return chat_stats


@router.post(
    "/chat/validate",
    summary="Validate chat messages",
    description="Validate chat message format and content without generating a response",
    responses={
        200: {"description": "Messages are valid"},
        400: {"description": "Invalid message format"},
        401: {"description": "Authentication required"}
    }
)
async def validate_chat_messages(
    messages: List[ChatMessage],
    current_user: User = Depends(get_current_active_user)
):
    """Validate chat messages format and content.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Use Case**: Validate messages before sending to avoid errors and rate limit usage.
    
    Args:
        messages: List of chat messages to validate
        current_user: Currently authenticated user
        
    Returns:
        Validation results
    """
    try:
        _validate_chat_messages(messages, current_user)
        
        validation_result = {
            "valid": True,
            "message_count": len(messages),
            "estimated_tokens": sum(_estimate_message_tokens(msg.content) for msg in messages),
            "has_system_message": any(msg.role == "system" for msg in messages),
            "conversation_length": len([msg for msg in messages if msg.role in ["user", "assistant"]])
        }
        
        return validation_result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _validate_chat_messages(messages: List[ChatMessage], user: User) -> None:
    """Validate chat messages format and content.
    
    Args:
        messages: List of chat messages
        user: Current user
        
    Raises:
        ValueError: If messages are invalid
    """
    if not messages:
        raise ValueError("At least one message is required")
    
    if len(messages) > 100:  # Configurable limit
        raise ValueError("Too many messages in conversation (max 100)")
    
    # Check for valid roles
    valid_roles = {"system", "user", "assistant"}
    for msg in messages:
        if msg.role not in valid_roles:
            raise ValueError(f"Invalid message role: {msg.role}")
        
        if not msg.content or not msg.content.strip():
            raise ValueError("Message content cannot be empty")
        
        if len(msg.content) > 10000:  # Configurable limit
            raise ValueError("Message content too long (max 10000 characters)")
    
    # Ensure conversation starts with user or system message
    if messages[0].role not in ["user", "system"]:
        raise ValueError("Conversation must start with a user or system message")
    
    # Check for alternating user/assistant pattern (optional validation)
    user_assistant_messages = [msg for msg in messages if msg.role in ["user", "assistant"]]
    for i, msg in enumerate(user_assistant_messages):
        expected_role = "user" if i % 2 == 0 else "assistant"
        if msg.role != expected_role:
            # This is a warning, not an error - conversations don't always alternate perfectly
            pass


async def _track_chat_usage(
    request: Request,
    user: User,
    model: str,
    messages: List[dict],
    response: str,
    status_code: int,
    db: Session
) -> None:
    """Track usage for chat requests.
    
    Args:
        request: FastAPI request object
        user: User making the request
        model: Model used
        messages: Chat messages
        response: Generated response
        status_code: HTTP status code
        db: Database session
    """
    try:
        usage_service = UsageService(db)
        
        # Calculate tokens
        prompt_tokens = sum(_estimate_message_tokens(msg.get("content", "")) for msg in messages)
        completion_tokens = _estimate_message_tokens(response)
        
        # Get API key ID if request was made with API key
        api_key_id = None
        if hasattr(request.state, 'api_key'):
            api_key_id = request.state.api_key.id
        
        usage_data = UsageLogCreate(
            endpoint="/api/chat",
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
        print(f"Failed to track chat usage: {str(e)}")


def _estimate_message_tokens(content: str) -> int:
    """Estimate tokens in a message.
    
    Args:
        content: Message content
        
    Returns:
        Estimated token count
    """
    if not content:
        return 0
    return len(content.split()) + len(content) // 4  # Rough estimation


def _get_model_context_length(model_name: str) -> int:
    """Get the context length for a model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Context length in tokens
    """
    # This would ideally come from the model's metadata
    model_contexts = {
        "llama3:8b": 8192,
        "llama3:70b": 8192,
        "codellama": 16384,
        "mistral": 8192
    }
    
    return model_contexts.get(model_name, 4096)  # Default


def _calculate_success_rate(requests_by_status: dict) -> float:
    """Calculate success rate from status code distribution."""
    total_requests = sum(requests_by_status.values())
    if total_requests == 0:
        return 0.0
    
    successful_requests = sum(
        count for status, count in requests_by_status.items()
        if status.startswith('2')
    )
    
    return (successful_requests / total_requests) * 100


def _get_popular_models_from_stats(stats) -> List[str]:
    """Extract popular models from usage statistics."""
    # This would need to be implemented based on your usage log structure
    # For now, return a placeholder
    return ["llama3:8b", "mistral"]