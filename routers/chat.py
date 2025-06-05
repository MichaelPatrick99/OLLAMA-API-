"""Router for chat endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, List

from models.schemas import ChatRequest, ChatMessage, ErrorResponse
from services.ollama_service import OllamaService


router = APIRouter(prefix="/api", tags=["chat"])


def get_ollama_service() -> OllamaService:
    """Dependency to get the Ollama service."""
    return OllamaService()


@router.post(
    "/chat",
    summary="Chat completion",
    description="Generate a chat completion for the given messages",
    response_description="Chat completion",
    responses={
        200: {"description": "Successful response"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def chat_completion(
    request: ChatRequest,
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """Generate a chat completion.
    
    Args:
        request: The chat request
        ollama_service: The Ollama service
        
    Returns:
        Chat completion (streaming or non-streaming)
    """
    # Convert Pydantic models to dictionaries for the API
    messages = [msg.dict() for msg in request.messages]
    
    if request.stream:
        return StreamingResponse(
            ollama_service.stream_chat(
                messages, 
                request.model, 
                request.options
            ),
            media_type="text/plain"
        )
    else:
        response = await ollama_service.chat(
            messages, 
            request.model, 
            request.options
        )
        return JSONResponse(response)