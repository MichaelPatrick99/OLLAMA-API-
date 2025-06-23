"""Authentication and user management services."""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from database.models import User, APIKey, UsageLog, RoleEnum
from auth.schemas import (
    UserCreate, UserUpdate, UserResponse,
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse,
    UsageLogCreate, UsageStatsResponse
)
from auth.utils import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    generate_api_key,
    hash_api_key,
    get_current_time
)
from config import settings


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        """Initialize the user service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user
            
        Raises:
            HTTPException: If user already exists or validation fails
        """
        # Check if username already exists
        existing_user = self.db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role.value,
            is_active=True,
            is_verified=False  # Email verification can be implemented later
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return UserResponse.from_orm(db_user)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = self.db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = get_current_time()
        self.db.commit()
        
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Get list of users.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of users
        """
        users = self.db.query(User).offset(skip).limit(limit).all()
        return [UserResponse.from_orm(user) for user in users]
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        """Update user information.
        
        Args:
            user_id: User ID
            user_data: User update data
            
        Returns:
            Updated user if found, None otherwise
            
        Raises:
            HTTPException: If username/email already exists
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Check for conflicts if updating username or email
        if user_data.username and user_data.username != user.username:
            existing = self.db.query(User).filter(User.username == user_data.username).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
        
        if user_data.email and user_data.email != user.email:
            existing = self.db.query(User).filter(User.email == user_data.email).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        # Update user fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                if field == "role":
                    setattr(user, field, value.value)
                else:
                    setattr(user, field, value)
        
        user.updated_at = get_current_time()
        self.db.commit()
        self.db.refresh(user)
        
        return UserResponse.from_orm(user)
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True


class APIKeyService:
    """Service for API key management operations."""
    
    def __init__(self, db: Session):
        """Initialize the API key service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_api_key(self, user_id: int, key_data: APIKeyCreate) -> APIKeyCreateResponse:
        """Create a new API key for a user.
        
        Args:
            user_id: User ID
            key_data: API key creation data
            
        Returns:
            Created API key with secret
            
        Raises:
            HTTPException: If user not found or validation fails
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate API key pair
        key_id, secret = generate_api_key()
        key_hash = hash_api_key(secret)
        
        # Set expiration date
        expires_at = None
        if key_data.expires_at:
            expires_at = key_data.expires_at
        else:
            expires_at = get_current_time() + timedelta(days=settings.API_KEY_DEFAULT_EXPIRE_DAYS)
        
        # Create API key record
        db_api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=key_data.name,
            user_id=user_id,
            role=key_data.role.value,
            usage_limit_per_hour=key_data.usage_limit_per_hour,
            usage_limit_per_day=key_data.usage_limit_per_day,
            usage_limit_per_month=key_data.usage_limit_per_month,
            expires_at=expires_at,
            is_active=True
        )
        
        self.db.add(db_api_key)
        self.db.commit()
        self.db.refresh(db_api_key)
        
        return APIKeyCreateResponse(
            api_key=APIKeyResponse.from_orm(db_api_key),
            secret=f"{key_id}_{secret}"  # Combined format for user
        )
    
    def get_user_api_keys(self, user_id: int) -> List[APIKeyResponse]:
        """Get all API keys for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of user's API keys
        """
        api_keys = self.db.query(APIKey).filter(APIKey.user_id == user_id).all()
        return [APIKeyResponse.from_orm(key) for key in api_keys]
    
    def get_api_key_by_id(self, key_id: int, user_id: Optional[int] = None) -> Optional[APIKey]:
        """Get API key by ID.
        
        Args:
            key_id: API key ID
            user_id: Optional user ID for authorization check
            
        Returns:
            API key if found and authorized, None otherwise
        """
        query = self.db.query(APIKey).filter(APIKey.id == key_id)
        if user_id:
            query = query.filter(APIKey.user_id == user_id)
        
        return query.first()
    
    def update_api_key(
        self, 
        key_id: int, 
        user_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[APIKeyResponse]:
        """Update API key settings.
        
        Args:
            key_id: API key ID
            user_id: User ID for authorization
            update_data: Update data
            
        Returns:
            Updated API key if found, None otherwise
        """
        api_key = self.db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()
        
        if not api_key:
            return None
        
        # Update allowed fields
        allowed_fields = {
            'name', 'usage_limit_per_hour', 'usage_limit_per_day', 
            'usage_limit_per_month', 'expires_at', 'is_active'
        }
        
        for field, value in update_data.items():
            if field in allowed_fields and value is not None:
                setattr(api_key, field, value)
        
        self.db.commit()
        self.db.refresh(api_key)
        
        return APIKeyResponse.from_orm(api_key)
    
    def delete_api_key(self, key_id: int, user_id: int) -> bool:
        """Delete an API key.
        
        Args:
            key_id: API key ID
            user_id: User ID for authorization
            
        Returns:
            True if deleted, False if not found
        """
        api_key = self.db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()
        
        if not api_key:
            return False
        
        self.db.delete(api_key)
        self.db.commit()
        return True
    
    def check_rate_limits(self, api_key: APIKey) -> Dict[str, bool]:
        """Check if API key has exceeded rate limits.
        
        Args:
            api_key: API key to check
            
        Returns:
            Dictionary with limit check results
        """
        return {
            "hour_limit_exceeded": api_key.current_hour_usage >= api_key.usage_limit_per_hour,
            "day_limit_exceeded": api_key.current_day_usage >= api_key.usage_limit_per_day,
            "month_limit_exceeded": api_key.current_month_usage >= api_key.usage_limit_per_month
        }


class UsageService:
    """Service for usage tracking and analytics."""
    
    def __init__(self, db: Session):
        """Initialize the usage service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def log_usage(
        self, 
        usage_data: UsageLogCreate,
        user_id: Optional[int] = None,
        api_key_id: Optional[int] = None
    ) -> None:
        """Log API usage.
        
        Args:
            usage_data: Usage log data
            user_id: Optional user ID
            api_key_id: Optional API key ID
        """
        db_usage_log = UsageLog(
            user_id=user_id,
            api_key_id=api_key_id,
            endpoint=usage_data.endpoint,
            method=usage_data.method,
            model_used=usage_data.model_used,
            prompt_tokens=usage_data.prompt_tokens,
            completion_tokens=usage_data.completion_tokens,
            total_tokens=usage_data.prompt_tokens + usage_data.completion_tokens,
            response_time_ms=usage_data.response_time_ms,
            status_code=usage_data.status_code,
            ip_address=usage_data.ip_address,
            user_agent=usage_data.user_agent
        )
        
        self.db.add(db_usage_log)
        self.db.commit()
    
    def get_user_usage_stats(
        self, 
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageStatsResponse:
        """Get usage statistics for a user.
        
        Args:
            user_id: User ID
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Usage statistics
        """
        query = self.db.query(UsageLog).filter(UsageLog.user_id == user_id)
        
        if start_date:
            query = query.filter(UsageLog.created_at >= start_date)
        if end_date:
            query = query.filter(UsageLog.created_at <= end_date)
        
        usage_logs = query.all()
        
        # Calculate statistics
        total_requests = len(usage_logs)
        total_tokens = sum(log.total_tokens for log in usage_logs)
        
        response_times = [log.response_time_ms for log in usage_logs if log.response_time_ms]
        average_response_time = sum(response_times) / len(response_times) if response_times else None
        
        # Group by status code
        requests_by_status = {}
        for log in usage_logs:
            status = str(log.status_code)
            requests_by_status[status] = requests_by_status.get(status, 0) + 1
        
        # Group by endpoint
        requests_by_endpoint = {}
        for log in usage_logs:
            endpoint = log.endpoint
            requests_by_endpoint[endpoint] = requests_by_endpoint.get(endpoint, 0) + 1
        
        return UsageStatsResponse(
            total_requests=total_requests,
            total_tokens=total_tokens,
            average_response_time=average_response_time,
            requests_by_status=requests_by_status,
            requests_by_endpoint=requests_by_endpoint,
            usage_by_hour=[],  # Can be implemented for detailed analytics
            usage_by_day=[]    # Can be implemented for detailed analytics
        )