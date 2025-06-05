"""Pydantic models for request and response validation."""

from fastapi.datastructures import Default
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union

from config import Settings

settings = Settings()
DEFAULT_MODEL = settings.DEFAULT_MODEL


class GenerateRequest(BaseModel):
    """Request model for text generation."""
    
    prompt: str = Field(..., description="The prompt to generate text from")
    model: str = Field(DEFAULT_MODEL, description="The model to use for generation")
    stream: bool = Field(True, description="Whether to stream the response")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional model options")


class ChatMessage(BaseModel):
    """Individual chat message."""
    
    role: str = Field(..., description="The role of the message sender (system, user, assistant)")
    content: str = Field(..., description="The content of the message")


class ChatRequest(BaseModel):
    """Request model for chat completion."""
    
    messages: List[ChatMessage] = Field(..., description="The messages to generate a response from")
    model: str = Field(DEFAULT_MODEL, description="The model to use for chat")
    stream: bool = Field(True, description="Whether to stream the response")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional model options")


class ModelInfo(BaseModel):
    """Model information."""
    
    name: str = Field(..., description="The name of the model")
    modified_at: Optional[str] = Field(None, description="When the model was last modified")
    size: Optional[int] = Field(None, description="The size of the model in bytes")
    digest: Optional[str] = Field(None, description="The digest of the model")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional model details")


class ModelsList(BaseModel):
    """List of available models."""
    
    models: List[ModelInfo] = Field(..., description="List of available models")


class ModelDownloadRequest(BaseModel):
    """Request to download a model."""
    
    name: str = Field(..., description="The name of the model to download")


class ModelResponse(BaseModel):
    """Response for model operations."""
    
    message: str = Field(..., description="Response message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    detail: str = Field(..., description="Error details")
    status_code: int = Field(..., description="HTTP status code")