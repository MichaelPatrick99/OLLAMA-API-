"""Authentication middleware for rate limiting and request validation."""

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from typing import Dict, Optional
from datetime import datetime, timedelta
import time

from database.connection import SessionLocal
from database.models import APIKey, User
from auth.utils import extract_api_key_from_header, verify_api_key, AuthenticationError
from config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and rate limiting."""
    
    def __init__(self, app, enable_rate_limiting: bool = True):
        """Initialize the authentication middleware.
        
        Args:
            app: FastAPI application
            enable_rate_limiting: Whether to enable rate limiting
        """
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.rate_limit_cache: Dict[str, Dict] = {}
        
    async def dispatch(self, request: Request, call_next):
        """Process the request through authentication middleware.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        start_time = time.time()
        
        # Skip auth for certain endpoints
        if self._should_skip_auth(request):
            response = await call_next(request)
            return response
        
        # Check API key rate limits if applicable
        if self.enable_rate_limiting:
            try:
                await self._check_rate_limits(request)
            except HTTPException as e:
                return Response(
                    content=f'{{"detail": "{e.detail}", "status_code": {e.status_code}}}',
                    status_code=e.status_code,
                    media_type="application/json"
                )
        
        # Process the request
        response = await call_next(request)
        
        # Add processing time header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    def _should_skip_auth(self, request: Request) -> bool:
        """Check if authentication should be skipped for this request.
        
        Args:
            request: Incoming request
            
        Returns:
            True if auth should be skipped
        """
        skip_paths = {
            "/", "/health", "/docs", "/redoc", "/openapi.json",
            "/api/auth/register", "/api/auth/login"
        }
        
        return request.url.path in skip_paths
    
    async def _check_rate_limits(self, request: Request) -> None:
        """Check rate limits for API key requests.
        
        Args:
            request: Incoming request
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        # Extract API key from request
        authorization = request.headers.get("Authorization")
        if not authorization:
            return  # No API key, skip rate limiting
        
        api_key_secret = extract_api_key_from_header(authorization)
        if not api_key_secret:
            return  # Invalid format, will be handled by auth dependencies
        
        # Get API key from database
        db = SessionLocal()
        try:
            # Extract key_id from the secret (format: oak_{key_id}_{secret})
            parts = api_key_secret.split("_")
            if len(parts) < 2:
                return
            
            key_id = parts[1]
            api_key = db.query(APIKey).filter(APIKey.key_id.contains(key_id)).first()
            
            if not api_key:
                return  # API key not found, will be handled by auth dependencies
            
            # Check rate limits
            current_time = datetime.utcnow()
            
            # Check hourly limit
            if self._is_hour_limit_exceeded(api_key, current_time):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Hourly rate limit exceeded. Limit: {api_key.usage_limit_per_hour} requests/hour"
                )
            
            # Check daily limit
            if self._is_day_limit_exceeded(api_key, current_time):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Daily rate limit exceeded. Limit: {api_key.usage_limit_per_day} requests/day"
                )
            
            # Check monthly limit
            if self._is_month_limit_exceeded(api_key, current_time):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Monthly rate limit exceeded. Limit: {api_key.usage_limit_per_month} requests/month"
                )
            
            # Update usage counters
            self._update_usage_counters(api_key, current_time, db)
            
        finally:
            db.close()
    
    def _is_hour_limit_exceeded(self, api_key: APIKey, current_time: datetime) -> bool:
        """Check if hourly rate limit is exceeded.
        
        Args:
            api_key: API key to check
            current_time: Current time
            
        Returns:
            True if limit exceeded
        """
        # Reset counter if it's a new hour
        if (not api_key.last_used or 
            api_key.last_used.hour != current_time.hour or
            api_key.last_used.date() != current_time.date()):
            return False
        
        return api_key.current_hour_usage >= api_key.usage_limit_per_hour
    
    def _is_day_limit_exceeded(self, api_key: APIKey, current_time: datetime) -> bool:
        """Check if daily rate limit is exceeded.
        
        Args:
            api_key: API key to check
            current_time: Current time
            
        Returns:
            True if limit exceeded
        """
        # Reset counter if it's a new day
        if (not api_key.last_used or 
            api_key.last_used.date() != current_time.date()):
            return False
        
        return api_key.current_day_usage >= api_key.usage_limit_per_day
    
    def _is_month_limit_exceeded(self, api_key: APIKey, current_time: datetime) -> bool:
        """Check if monthly rate limit is exceeded.
        
        Args:
            api_key: API key to check
            current_time: Current time
            
        Returns:
            True if limit exceeded
        """
        # Reset counter if it's a new month
        if (not api_key.last_used or 
            api_key.last_used.month != current_time.month or
            api_key.last_used.year != current_time.year):
            return False
        
        return api_key.current_month_usage >= api_key.usage_limit_per_month
    
    def _update_usage_counters(self, api_key: APIKey, current_time: datetime, db: Session) -> None:
        """Update usage counters for the API key.
        
        Args:
            api_key: API key to update
            current_time: Current time
            db: Database session
        """
        # Reset counters if needed
        reset_hour = (not api_key.last_used or 
                     api_key.last_used.hour != current_time.hour or
                     api_key.last_used.date() != current_time.date())
        
        reset_day = (not api_key.last_used or 
                    api_key.last_used.date() != current_time.date())
        
        reset_month = (not api_key.last_used or 
                      api_key.last_used.month != current_time.month or
                      api_key.last_used.year != current_time.year)
        
        if reset_hour:
            api_key.current_hour_usage = 1
        else:
            api_key.current_hour_usage += 1
        
        if reset_day:
            api_key.current_day_usage = 1
        else:
            api_key.current_day_usage += 1
        
        if reset_month:
            api_key.current_month_usage = 1
        else:
            api_key.current_month_usage += 1
        
        api_key.total_usage += 1
        api_key.last_used = current_time
        
        db.commit()