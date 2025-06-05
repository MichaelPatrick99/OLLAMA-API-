"""Router for model management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List

from models.schemas import ModelDownloadRequest, ModelResponse, ErrorResponse
from services.ollama_service import OllamaService


router = APIRouter(prefix="/api", tags=["models"])


def get_ollama_service() -> OllamaService:
    """Dependency to get the Ollama service."""
    return OllamaService()


@router.get(
    "/models",
    summary="List available models",
    description="List all available models",
    response_description="List of models",
    responses={
        200: {"description": "Successful response"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def list_models(ollama_service: OllamaService = Depends(get_ollama_service)):
    """List available models.
    
    Args:
        ollama_service: The Ollama service
        
    Returns:
        List of available models
    """
    return await ollama_service.list_models()


@router.post(
    "/models/download",
    summary="Download a model",
    description="Download a model from Ollama",
    response_description="Download status",
    responses={
        200: {"model": ModelResponse, "description": "Successful response"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def download_model(
    request: ModelDownloadRequest,
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """Download a model.
    
    Args:
        request: The download request
        ollama_service: The Ollama service
        
    Returns:
        Download status
    """
    return await ollama_service.download_model(request.name)


@router.get(
    "/models/{model_name}",
    summary="Get model information",
    description="Get information about a specific model",
    response_description="Model information",
    responses={
        200: {"description": "Successful response"},
        404: {"model": ErrorResponse, "description": "Model not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_model_info(
    model_name: str,
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """Get information about a model.
    
    Args:
        model_name: Name of the model
        ollama_service: The Ollama service
        
    Returns:
        Model information
    """
    return await ollama_service.model_info(model_name)


@router.delete(
    "/models/{model_name}",
    summary="Delete a model",
    description="Delete a model from Ollama",
    response_description="Deletion status",
    responses={
        200: {"model": ModelResponse, "description": "Successful response"},
        404: {"model": ErrorResponse, "description": "Model not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def delete_model(
    model_name: str,
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """Delete a model.
    
    Args:
        model_name: Name of the model to delete
        ollama_service: The Ollama service
        
    Returns:
        Deletion status
    """
    return await ollama_service.delete_model(model_name)