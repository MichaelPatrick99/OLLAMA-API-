"""Service for interacting with the Ollama API."""

import json
import httpx
from typing import Dict, Any, AsyncGenerator, Optional
from fastapi import HTTPException

from config import settings


class OllamaService:
    """Service for interacting with the Ollama API."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        """Initialize the Ollama service.
        
        Args:
            base_url: Base URL for the Ollama API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.OLLAMA_API_BASE_URL
        self.timeout = timeout or settings.REQUEST_TIMEOUT
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Make a request to the Ollama API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            json_data: JSON data to send
            
        Returns:
            Response from the API
            
        Raises:
            HTTPException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, json=json_data)
                response.raise_for_status()
                return response
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (4xx, 5xx)
            error_detail = f"Ollama API error: {e.response.status_code}"
            try:
                error_json = e.response.json()
                if "error" in error_json:
                    error_detail = f"Ollama API error: {error_json['error']}"
            except Exception:
                pass
            raise HTTPException(status_code=e.response.status_code, detail=error_detail)
        except httpx.RequestError as e:
            # Handle connection errors
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")
    
    async def stream_generate(
        self, prompt: str, model: str, options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream generated text from the Ollama API.
        
        Args:
            prompt: The prompt to generate from
            model: The model to use
            options: Additional model options
            
        Yields:
            Generated text chunks
            
        Raises:
            HTTPException: If the request fails
        """
        url = f"{self.base_url}/api/generate"
        payload = {"model": model, "prompt": prompt}
        
        if options:
            payload.update(options)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        error_detail = "Failed to connect to the model server"
                        try:
                            error_json = await response.json()
                            if "error" in error_json:
                                error_detail = error_json["error"]
                        except Exception:
                            pass
                        raise HTTPException(status_code=response.status_code, detail=error_detail)
                    
                    async for chunk in response.aiter_bytes():
                        decoded_chunk = chunk.decode('utf-8')
                        for line in decoded_chunk.split("\n"):
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        yield data["response"]
                                except json.JSONDecodeError:
                                    continue  # Skip invalid JSON
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")
    
    async def generate(
        self, prompt: str, model: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate text from the Ollama API (non-streaming).
        
        Args:
            prompt: The prompt to generate from
            model: The model to use
            options: Additional model options
            
        Returns:
            Generated text response
            
        Raises:
            HTTPException: If the request fails
        """
        url = f"{self.base_url}/api/generate"
        payload = {"model": model, "prompt": prompt}
        
        if options:
            payload.update(options)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                # Combine all responses into a single string
                combined_response = ""
                for line in response.text.splitlines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                combined_response += data["response"]
                        except json.JSONDecodeError:
                            continue  # Skip invalid JSON
                
                return {"response": combined_response}
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")
    
    async def stream_chat(
        self, messages: list, model: str, options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from the Ollama API.
        
        Args:
            messages: List of chat messages
            model: The model to use
            options: Additional model options
            
        Yields:
            Generated chat response chunks
            
        Raises:
            HTTPException: If the request fails
        """
        url = f"{self.base_url}/api/chat"
        payload = {"model": model, "messages": messages}
        
        if options:
            payload.update(options)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        error_detail = "Failed to connect to the model server"
                        try:
                            error_json = await response.json()
                            if "error" in error_json:
                                error_detail = error_json["error"]
                        except Exception:
                            pass
                        raise HTTPException(status_code=response.status_code, detail=error_detail)
                    
                    async for chunk in response.aiter_bytes():
                        decoded_chunk = chunk.decode('utf-8')
                        for line in decoded_chunk.split("\n"):
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if "message" in data and "content" in data["message"]:
                                        yield data["message"]["content"]
                                except json.JSONDecodeError:
                                    continue  # Skip invalid JSON
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")
    
    async def chat(
        self, messages: list, model: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get chat completion from the Ollama API (non-streaming).
        
        Args:
            messages: List of chat messages
            model: The model to use
            options: Additional model options
            
        Returns:
            Chat completion response
            
        Raises:
            HTTPException: If the request fails
        """
        url = f"{self.base_url}/api/chat"
        payload = {"model": model, "messages": messages}
        
        if options:
            payload.update(options)
        
        response = await self._make_request("POST", "/api/chat", payload)
        return response.json()
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models.
        
        Returns:
            List of available models
            
        Raises:
            HTTPException: If the request fails
        """
        response = await self._make_request("GET", "/api/tags")
        return response.json()
    
    async def download_model(self, model_name: str) -> Dict[str, Any]:
        """Download a model.
        
        Args:
            model_name: Name of the model to download
            
        Returns:
            Download status
            
        Raises:
            HTTPException: If the request fails
        """
        payload = {"name": model_name}
        response = await self._make_request("POST", "/api/pull", payload)
        return {"message": f"Model {model_name} downloaded successfully", "details": response.json()}
    
    async def model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model information
            
        Raises:
            HTTPException: If the request fails
        """
        payload = {"name": model_name}
        response = await self._make_request("POST", "/api/show", payload)
        return response.json()
    
    async def delete_model(self, model_name: str) -> Dict[str, Any]:
        """Delete a model.
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            Deletion status
            
        Raises:
            HTTPException: If the request fails
        """
        payload = {"name": model_name}
        response = await self._make_request("DELETE", "/api/delete", payload)
        return {"message": f"Model {model_name} deleted successfully", "details": response.json()}