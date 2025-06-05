"""Router for text generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any

from models.schemas import GenerateRequest, ErrorResponse
from services.ollama_service import OllamaService


router = APIRouter(prefix="/api", tags=["generation"])


def get_ollama_service() -> OllamaService:
    """Dependency to get the Ollama service."""
    return OllamaService()


@router.post(
    "/generate",
    summary="Generate text from a prompt",
    description="Generate text from a prompt using the specified model",
    response_description="Generated text",
    responses={
        200: {"description": "Successful response"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def generate_text(
    request: GenerateRequest,
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """Generate text from a prompt.
    
    Args:
        request: The generation request
        ollama_service: The Ollama service
        
    Returns:
        Generated text (streaming or non-streaming)
    """
    if request.stream:
        return StreamingResponse(
            ollama_service.stream_generate(
                request.prompt, 
                request.model, 
                request.options
            ),
            media_type="text/plain"
        )
    else:
        response = await ollama_service.generate(
            request.prompt, 
            request.model, 
            request.options
        )
        return JSONResponse(response)