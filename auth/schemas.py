"""Pydantic schemas for authentication and authorization."""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RoleEnum(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    READ_ONLY = "read_only"


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    role: RoleEnum = RoleEnum.USER


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


# API Key Schemas
class APIKeyBase(BaseModel):
    """Base API key schema."""
    name: str = Field(..., min_length=1, max_length=100)
    role: RoleEnum = RoleEnum.USER
    usage_limit_per_hour: int = Field(100, ge=1, le=10000)
    usage_limit_per_day: int = Field(1000, ge=1, le=100000)
    usage_limit_per_month: int = Field(10000, ge=1, le=1000000)
    expires_at: Optional[datetime] = None


class APIKeyCreate(APIKeyBase):
    """Schema for API key creation."""
    pass


class APIKeyResponse(APIKeyBase):
    """Schema for API key response."""
    id: int
    key_id: str
    current_hour_usage: int
    current_day_usage: int
    current_month_usage: int
    total_usage: int
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]
    
    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """Schema for API key creation response (includes secret)."""
    api_key: APIKeyResponse
    secret: str  # Only returned once during creation
    
    class Config:
        from_attributes = True


# Authentication Schemas
class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


# Usage Schemas
class UsageLogCreate(BaseModel):
    """Schema for creating usage logs."""
    endpoint: str
    method: str
    model_used: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    response_time_ms: Optional[float] = None
    status_code: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class UsageLogResponse(BaseModel):
    """Schema for usage log response."""
    id: int
    endpoint: str
    method: str
    model_used: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time_ms: Optional[float]
    status_code: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UsageStatsResponse(BaseModel):
    """Schema for usage statistics."""
    total_requests: int
    total_tokens: int
    average_response_time: Optional[float]
    requests_by_status: dict
    requests_by_endpoint: dict
    usage_by_hour: List[dict]
    usage_by_day: List[dict]


# Permission Schemas
class PermissionBase(BaseModel):
    """Base permission schema."""
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    """Schema for permission creation."""
    pass


class PermissionResponse(PermissionBase):
    """Schema for permission response."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Error Schemas
class AuthErrorResponse(BaseModel):
    """Authentication error response."""
    detail: str
    error_code: str
    status_code: int