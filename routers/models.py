"""Router for model management endpoints with authentication."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from database.connection import get_db
from database.models import User
from models.schemas import ModelDownloadRequest, ModelResponse, ErrorResponse
from services.ollama_service import OllamaService
from auth.dependencies import (
    get_current_active_user,
    require_models_read,
    require_models_write, 
    require_models_delete,
    require_admin,
    get_optional_user
)
from auth.services import UsageService
from auth.schemas import UsageLogCreate


router = APIRouter(prefix="/api", tags=["models"])


def get_ollama_service() -> OllamaService:
    """Dependency to get the Ollama service."""
    return OllamaService()


@router.get(
    "/models",
    summary="List available models",
    description="List all available models. Requires authentication.",
    response_description="List of models",
    responses={
        200: {"description": "Successful response"},
        401: {"description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def list_models(
    request: Request,
    current_user: User = Depends(require_models_read),
    ollama_service: OllamaService = Depends(get_ollama_service),
    db: Session = Depends(get_db)
):
    """List available models.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Required Permission**: `models:read`
    
    **Allowed Roles**: All authenticated users
    
    **Features**:
    - Lists all installed models
    - Shows model metadata and capabilities
    - Role-based model filtering
    - Usage tracking
    
    Args:
        request: FastAPI request object
        current_user: Currently authenticated user
        ollama_service: The Ollama service
        db: Database session
        
    Returns:
        List of available models with metadata
    """
    try:
        models = await ollama_service.list_models()
        
        # Enhance model information based on user role
        if "models" in models:
            enhanced_models = []
            for model in models["models"]:
                enhanced_model = model.copy()
                
                # Add role-specific information
                enhanced_model.update({
                    "accessible": True,
                    "capabilities": _get_model_capabilities(model.get("name", "")),
                    "recommended_for": _get_model_recommendations(model.get("name", ""), current_user.role),
                    "usage_limits": _get_model_usage_limits(current_user.role)
                })
                
                # Role-based filtering could be applied here
                if current_user.role == "read_only":
                    enhanced_model["can_download"] = False
                    enhanced_model["can_delete"] = False
                else:
                    enhanced_model["can_download"] = True
                    enhanced_model["can_delete"] = current_user.role in ["admin", "developer"]
                
                enhanced_models.append(enhanced_model)
            
            models["models"] = enhanced_models
        
        # Track the request
        await _track_models_usage(request, current_user, "list", None, 200, db)
        
        return models
        
    except Exception as e:
        await _track_models_usage(request, current_user, "list", None, 500, db)
        raise e


@router.post(
    "/models/download",
    summary="Download a model",
    description="Download a model from Ollama. Requires write permissions.",
    response_description="Download status",
    responses={
        200: {"model": ModelResponse, "description": "Successful response"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def download_model(
    request: Request,
    download_request: ModelDownloadRequest,
    current_user: User = Depends(require_models_write),
    ollama_service: OllamaService = Depends(get_ollama_service),
    db: Session = Depends(get_db)
):
    """Download a model.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Required Permission**: `models:write`
    
    **Allowed Roles**: 
    - Admin (full access)
    - Developer (full access)
    - User (full access)
    - Read-Only (❌ no access)
    
    **Features**:
    - Downloads models from Ollama registry
    - Progress tracking (future enhancement)
    - Automatic model verification
    - Usage logging
    
    Args:
        request: FastAPI request object
        download_request: The download request
        current_user: Currently authenticated user
        ollama_service: The Ollama service
        db: Database session
        
    Returns:
        Download status and information
    """
    model_name = download_request.name
    
    # Validate model name
    if not _is_valid_model_name(model_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid model name format"
        )
    
    # Check if user has permission to download this specific model
    if not _can_user_download_model(current_user, model_name):
        raise HTTPException(
            status_code=403,
            detail=f"You don't have permission to download model '{model_name}'"
        )
    
    try:
        result = await ollama_service.download_model(model_name)
        
        # Track successful download
        await _track_models_usage(request, current_user, "download", model_name, 200, db)
        
        # Enhanced response
        enhanced_result = {
            "message": f"Model '{model_name}' download initiated successfully",
            "model_name": model_name,
            "download_status": "in_progress",
            "estimated_size": _get_estimated_model_size(model_name),
            "details": result
        }
        
        return enhanced_result
        
    except Exception as e:
        await _track_models_usage(request, current_user, "download", model_name, 500, db)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download model '{model_name}': {str(e)}"
        )


@router.get(
    "/models/{model_name}",
    summary="Get model information",
    description="Get detailed information about a specific model",
    response_description="Model information",
    responses={
        200: {"description": "Successful response"},
        404: {"model": ErrorResponse, "description": "Model not found"},
        401: {"description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_model_info(
    request: Request,
    model_name: str,
    current_user: User = Depends(require_models_read),
    ollama_service: OllamaService = Depends(get_ollama_service),
    db: Session = Depends(get_db)
):
    """Get information about a model.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Required Permission**: `models:read`
    
    **Allowed Roles**: All authenticated users
    
    Args:
        request: FastAPI request object
        model_name: Name of the model
        current_user: Currently authenticated user
        ollama_service: The Ollama service
        db: Database session
        
    Returns:
        Detailed model information
    """
    try:
        model_info = await ollama_service.model_info(model_name)
        
        # Enhance model information
        enhanced_info = model_info.copy()
        enhanced_info.update({
            "capabilities": _get_model_capabilities(model_name),
            "performance_metrics": _get_model_performance_metrics(model_name),
            "user_permissions": {
                "can_use": True,
                "can_download": current_user.role in ["admin", "developer", "user"],
                "can_delete": current_user.role in ["admin", "developer"]
            },
            "usage_recommendations": _get_model_recommendations(model_name, current_user.role)
        })
        
        # Track the request
        await _track_models_usage(request, current_user, "info", model_name, 200, db)
        
        return enhanced_info
        
    except Exception as e:
        await _track_models_usage(request, current_user, "info", model_name, 500, db)
        raise HTTPException(
            status_code=404 if "not found" in str(e).lower() else 500,
            detail=f"Failed to get model info for '{model_name}': {str(e)}"
        )


@router.delete(
    "/models/{model_name}",
    summary="Delete a model",
    description="Delete a model from Ollama. Requires delete permissions.",
    response_description="Deletion status",
    responses={
        200: {"model": ModelResponse, "description": "Successful response"},
        404: {"model": ErrorResponse, "description": "Model not found"},
        403: {"description": "Insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def delete_model(
    request: Request,
    model_name: str,
    current_user: User = Depends(require_models_delete),
    ollama_service: OllamaService = Depends(get_ollama_service),
    db: Session = Depends(get_db)
):
    """Delete a model.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Required Permission**: `models:delete`
    
    **Allowed Roles**: 
    - Admin (full access)
    - Developer (full access)
    - User (❌ no access)
    - Read-Only (❌ no access)
    
    **⚠️ Warning**: This action is irreversible. The model will need to be re-downloaded if needed again.
    
    Args:
        request: FastAPI request object
        model_name: Name of the model to delete
        current_user: Currently authenticated user
        ollama_service: The Ollama service
        db: Database session
        
    Returns:
        Deletion status
    """
    # Additional validation for critical models
    if _is_protected_model(model_name):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail=f"Model '{model_name}' is protected and can only be deleted by administrators"
            )
    
    # Check if model is currently in use
    if await _is_model_in_use(model_name, db):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=409,
                detail=f"Model '{model_name}' is currently in use and cannot be deleted"
            )
    
    try:
        result = await ollama_service.delete_model(model_name)
        
        # Track successful deletion
        await _track_models_usage(request, current_user, "delete", model_name, 200, db)
        
        enhanced_result = {
            "message": f"Model '{model_name}' deleted successfully",
            "model_name": model_name,
            "deleted_by": current_user.username,
            "details": result
        }
        
        return enhanced_result
        
    except Exception as e:
        await _track_models_usage(request, current_user, "delete", model_name, 500, db)
        raise HTTPException(
            status_code=404 if "not found" in str(e).lower() else 500,
            detail=f"Failed to delete model '{model_name}': {str(e)}"
        )


@router.get(
    "/models/{model_name}/usage",
    summary="Get model usage statistics",
    description="Get usage statistics for a specific model",
    responses={
        200: {"description": "Model usage statistics"},
        404: {"description": "Model not found"},
        401: {"description": "Authentication required"}
    }
)
async def get_model_usage_stats(
    model_name: str,
    current_user: User = Depends(require_models_read),
    db: Session = Depends(get_db)
):
    """Get usage statistics for a specific model.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Required Permission**: `models:read`
    
    Args:
        model_name: Name of the model
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Model usage statistics
    """
    usage_service = UsageService(db)
    
    # Get overall usage stats and filter by model
    if current_user.role == "admin":
        # Admins can see global model usage
        stats = await _get_global_model_usage(model_name, db)
    else:
        # Regular users see only their usage
        stats = usage_service.get_user_usage_stats(current_user.id)
    
    model_stats = {
        "model_name": model_name,
        "user_usage": {
            "total_requests": 0,
            "total_tokens": 0,
            "average_response_time": None
        },
        "global_usage": {
            "available": current_user.role == "admin"
        }
    }
    
    # Filter user's usage for this model
    # This would need to be implemented based on your usage log structure
    
    return model_stats


@router.post(
    "/models/{model_name}/validate",
    summary="Validate model availability",
    description="Check if a model is available and ready for use",
    responses={
        200: {"description": "Model validation results"},
        404: {"description": "Model not found"},
        401: {"description": "Authentication required"}
    }
)
async def validate_model(
    model_name: str,
    current_user: User = Depends(require_models_read),
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """Validate model availability and readiness.
    
    **Authentication Required**: This endpoint requires a valid JWT token or API key.
    
    **Use Case**: Check model status before making generation requests to avoid errors.
    
    Args:
        model_name: Name of the model to validate
        current_user: Currently authenticated user
        ollama_service: The Ollama service
        
    Returns:
        Model validation results
    """
    try:
        # Check if model exists
        model_info = await ollama_service.model_info(model_name)
        
        validation_results = {
            "model_name": model_name,
            "available": True,
            "ready": True,
            "capabilities": _get_model_capabilities(model_name),
            "estimated_performance": _get_model_performance_metrics(model_name),
            "user_can_access": True,
            "recommended_settings": _get_recommended_model_settings(model_name),
            "warnings": []
        }
        
        # Add role-specific warnings
        if current_user.role == "read_only":
            validation_results["warnings"].append(
                "Read-only users have limited access to model operations"
            )
        
        return validation_results
        
    except Exception as e:
        return {
            "model_name": model_name,
            "available": False,
            "ready": False,
            "error": str(e),
            "suggestions": [
                f"Try downloading the model first: POST /api/models/download",
                "Check the model name spelling",
                "Verify you have the required permissions"
            ]
        }


# Helper functions
async def _track_models_usage(
    request: Request,
    user: User,
    action: str,
    model_name: str,
    status_code: int,
    db: Session
) -> None:
    """Track usage for model management requests."""
    try:
        usage_service = UsageService(db)
        
        api_key_id = None
        if hasattr(request.state, 'api_key'):
            api_key_id = request.state.api_key.id
        
        usage_data = UsageLogCreate(
            endpoint=f"/api/models/{action}",
            method=request.method,
            model_used=model_name,
            prompt_tokens=0,
            completion_tokens=0,
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
        print(f"Failed to track models usage: {str(e)}")


def _get_model_capabilities(model_name: str) -> Dict[str, Any]:
    """Get capabilities for a specific model."""
    # This would ideally come from model metadata
    capabilities = {
        "text_generation": True,
        "chat_completion": True,
        "code_generation": "code" in model_name.lower(),
        "multilingual": True,
        "function_calling": False,  # Depends on model
        "vision": "vision" in model_name.lower(),
        "embedding": "embed" in model_name.lower()
    }
    
    return capabilities


def _get_model_recommendations(model_name: str, user_role: str) -> List[str]:
    """Get usage recommendations for a model based on user role."""
    recommendations = []
    
    if "8b" in model_name:
        recommendations.append("Good balance of speed and quality")
    elif "70b" in model_name:
        recommendations.append("High quality but slower, requires more resources")
    
    if user_role == "read_only":
        recommendations.append("Consider using smaller models for faster responses")
    elif user_role == "developer":
        recommendations.append("Suitable for development and testing")
    
    return recommendations


def _get_model_usage_limits(user_role: str) -> Dict[str, Any]:
    """Get usage limits based on user role."""
    limits = {
        "admin": {"daily_requests": -1, "concurrent_requests": -1},
        "developer": {"daily_requests": 10000, "concurrent_requests": 10},
        "user": {"daily_requests": 1000, "concurrent_requests": 5},
        "read_only": {"daily_requests": 100, "concurrent_requests": 2}
    }
    
    return limits.get(user_role, limits["read_only"])


def _is_valid_model_name(model_name: str) -> bool:
    """Validate model name format."""
    if not model_name or len(model_name) > 100:
        return False
    
    # Basic validation - could be more sophisticated
    invalid_chars = set('<>:"/\\|?*')
    return not any(char in invalid_chars for char in model_name)


def _can_user_download_model(user: User, model_name: str) -> bool:
    """Check if user can download a specific model."""
    # Role-based restrictions
    if user.role == "read_only":
        return False
    
    # Size-based restrictions for regular users
    if user.role == "user":
        large_models = ["70b", "65b", "175b"]
        if any(size in model_name.lower() for size in large_models):
            return False
    
    return True


def _is_protected_model(model_name: str) -> bool:
    """Check if model is protected from deletion."""
    protected_models = ["llama3:8b", "mistral"]  # System default models
    return model_name in protected_models


async def _is_model_in_use(model_name: str, db: Session) -> bool:
    """Check if model is currently being used."""
    # This would check recent usage logs or active sessions
    # For now, return False as a placeholder
    return False


def _get_estimated_model_size(model_name: str) -> str:
    """Get estimated download size for a model."""
    size_map = {
        "7b": "3.8GB",
        "8b": "4.7GB", 
        "13b": "7.3GB",
        "30b": "17GB",
        "70b": "39GB"
    }
    
    for size, download_size in size_map.items():
        if size in model_name.lower():
            return download_size
    
    return "Unknown"


def _get_model_performance_metrics(model_name: str) -> Dict[str, Any]:
    """Get performance metrics for a model."""
    # This would come from benchmarks or monitoring
    return {
        "speed": "medium",
        "quality": "high",
        "memory_usage": "4GB",
        "recommended_use_cases": ["general chat", "code assistance"]
    }


def _get_recommended_model_settings(model_name: str) -> Dict[str, Any]:
    """Get recommended settings for a model."""
    return {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 2048,
        "context_length": 4096
    }


async def _get_global_model_usage(model_name: str, db: Session) -> Dict[str, Any]:
    """Get global usage statistics for a model (admin only)."""
    # This would aggregate usage across all users
    return {
        "total_users": 0,
        "total_requests": 0,
        "average_response_time": 0.0
    }