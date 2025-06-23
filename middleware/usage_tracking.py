"""Usage tracking middleware for logging API usage and analytics."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import time
import json

from database.connection import SessionLocal
from database.models import User, APIKey, UsageLog
from auth.schemas import UsageLogCreate
from auth.services import UsageService
from config import settings


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking API usage and analytics."""
    
    def __init__(self, app, enable_logging: bool = None):
        """Initialize the usage tracking middleware.
        
        Args:
            app: FastAPI application
            enable_logging: Whether to enable usage logging (defaults to settings)
        """
        super().__init__(app)
        self.enable_logging = enable_logging if enable_logging is not None else settings.LOG_USAGE
        
    async def dispatch(self, request: Request, call_next):
        """Process the request through usage tracking middleware.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        start_time = time.time()
        
        # Get request details
        method = request.method
        endpoint = str(request.url.path)
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        # Initialize tracking variables
        user_id = None
        api_key_id = None
        model_used = None
        prompt_tokens = 0
        completion_tokens = 0
        
        # Process the request
        response = await call_next(request)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        status_code = response.status_code
        
        # Extract user/API key information if available
        if hasattr(request.state, 'user'):
            user_id = request.state.user.id
        
        if hasattr(request.state, 'api_key'):
            api_key_id = request.state.api_key.id
            user_id = request.state.api_key.user_id
        
        # Extract model and token information from request/response if available
        model_used, prompt_tokens, completion_tokens = await self._extract_usage_details(
            request, response, endpoint
        )
        
        # Log usage if enabled and not a health/docs endpoint
        if self.enable_logging and self._should_log_endpoint(endpoint):
            await self._log_usage(
                endpoint=endpoint,
                method=method,
                model_used=model_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time_ms=response_time_ms,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent,
                user_id=user_id,
                api_key_id=api_key_id
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Get the client IP address from the request.
        
        Args:
            request: Incoming request
            
        Returns:
            Client IP address
        """
        # Check for forwarded IP headers (for reverse proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None
    
    def _should_log_endpoint(self, endpoint: str) -> bool:
        """Check if this endpoint should be logged.
        
        Args:
            endpoint: Endpoint path
            
        Returns:
            True if should be logged
        """
        # Skip logging for health checks, docs, and static files
        skip_endpoints = {
            "/", "/health", "/docs", "/redoc", "/openapi.json",
            "/favicon.ico"
        }
        
        return endpoint not in skip_endpoints and not endpoint.startswith("/static")
    
    async def _extract_usage_details(
        self, 
        request: Request, 
        response: Response, 
        endpoint: str
    ) -> tuple[Optional[str], int, int]:
        """Extract usage details from request and response.
        
        Args:
            request: Incoming request
            response: Outgoing response
            endpoint: Endpoint path
            
        Returns:
            Tuple of (model_used, prompt_tokens, completion_tokens)
        """
        model_used = None
        prompt_tokens = 0
        completion_tokens = 0
        
        try:
            # Try to extract model from request body for generation endpoints
            if endpoint in ["/api/generate", "/api/chat"] and request.method == "POST":
                # This is a simplified extraction - in practice, you might need
                # to parse the request body more carefully
                if hasattr(request.state, 'request_body'):
                    body = request.state.request_body
                    if isinstance(body, dict):
                        model_used = body.get("model")
                        
                        # Estimate tokens (this is a rough estimation)
                        if "prompt" in body:
                            prompt_tokens = self._estimate_tokens(body["prompt"])
                        elif "messages" in body:
                            # For chat, estimate tokens from all messages
                            for message in body.get("messages", []):
                                prompt_tokens += self._estimate_tokens(message.get("content", ""))
            
            # For completion tokens, we'd need to parse the response
            # This is a simplified version - you might want to integrate with
            # the actual token counting from your Ollama service
            if response.status_code == 200 and endpoint in ["/api/generate", "/api/chat"]:
                completion_tokens = 50  # Placeholder - implement actual token counting
                
        except Exception:
            # Don't fail the request if usage extraction fails
            pass
        
        return model_used, prompt_tokens, completion_tokens
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text.
        
        This is a rough estimation. For production, you might want to use
        a proper tokenizer library like tiktoken.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated number of tokens
        """
        if not text:
            return 0
        
        # Rough estimation: ~4 characters per token on average
        return len(text) // 4
    
    async def _log_usage(
        self,
        endpoint: str,
        method: str,
        model_used: Optional[str],
        prompt_tokens: int,
        completion_tokens: int,
        response_time_ms: float,
        status_code: int,
        ip_address: Optional[str],
        user_agent: Optional[str],
        user_id: Optional[int],
        api_key_id: Optional[int]
    ) -> None:
        """Log the usage to the database.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            model_used: Model used for the request
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
            ip_address: Client IP address
            user_agent: User agent string
            user_id: User ID if authenticated
            api_key_id: API key ID if used
        """
        try:
            db = SessionLocal()
            
            usage_service = UsageService(db)
            usage_data = UsageLogCreate(
                endpoint=endpoint,
                method=method,
                model_used=model_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time_ms=response_time_ms,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            usage_service.log_usage(
                usage_data=usage_data,
                user_id=user_id,
                api_key_id=api_key_id
            )
            
            db.close()
            
        except Exception as e:
            # Don't fail the request if logging fails
            # In production, you might want to log this error to a monitoring service
            print(f"Failed to log usage: {str(e)}")
            pass