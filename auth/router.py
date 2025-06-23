"""Authentication router for user management and API key operations."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta

from database.connection import get_db
from database.models import User
from auth.schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin, Token,
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse,
    UsageStatsResponse, AuthErrorResponse
)
from auth.services import UserService, APIKeyService, UsageService
from auth.dependencies import (
    get_current_active_user, require_admin, require_developer,
    get_optional_user
)
from auth.utils import create_access_token, AuthenticationError
from config import settings


router = APIRouter(prefix="/api/auth", tags=["authentication"])


# User Authentication Endpoints
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account",
    responses={
        201: {"description": "User created successfully"},
        400: {"model": AuthErrorResponse, "description": "User already exists or validation error"},
        422: {"description": "Validation error"}
    }
)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user information
    """
    user_service = UserService(db)
    return user_service.create_user(user_data)


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user and return access token",
    responses={
        200: {"description": "Login successful"},
        401: {"model": AuthErrorResponse, "description": "Invalid credentials"},
        422: {"description": "Validation error"}
    }
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token.
    
    Args:
        form_data: Login form data (username and password)
        db: Database session
        
    Returns:
        Access token
    """
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise AuthenticationError("Invalid username or password")
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds())
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user",
    responses={
        200: {"description": "User information"},
        401: {"model": AuthErrorResponse, "description": "Not authenticated"}
    }
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information.
    
    Args:
        current_user: Currently authenticated user
        
    Returns:
        User information
    """
    return UserResponse.from_orm(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update information for the currently authenticated user",
    responses={
        200: {"description": "User updated successfully"},
        400: {"model": AuthErrorResponse, "description": "Username or email already exists"},
        401: {"model": AuthErrorResponse, "description": "Not authenticated"}
    }
)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information.
    
    Args:
        user_data: User update data
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Updated user information
    """
    user_service = UserService(db)
    
    # Users can't change their own role (only admins can do that)
    if user_data.role is not None:
        user_data.role = None
    
    updated_user = user_service.update_user(current_user.id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


# Admin User Management Endpoints
@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users",
    description="Get a list of all users (admin only)",
    dependencies=[Depends(require_admin)],
    responses={
        200: {"description": "List of users"},
        403: {"model": AuthErrorResponse, "description": "Admin access required"}
    }
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users (admin only).
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        db: Database session
        current_user: Current admin user
        
    Returns:
        List of users
    """
    user_service = UserService(db)
    return user_service.get_users(skip=skip, limit=limit)


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Get user information by ID (admin only)",
    dependencies=[Depends(require_admin)],
    responses={
        200: {"description": "User information"},
        404: {"model": AuthErrorResponse, "description": "User not found"},
        403: {"model": AuthErrorResponse, "description": "Admin access required"}
    }
)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get user by ID (admin only).
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current admin user
        
    Returns:
        User information
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user by ID",
    description="Update user information by ID (admin only)",
    dependencies=[Depends(require_admin)],
    responses={
        200: {"description": "User updated successfully"},
        404: {"model": AuthErrorResponse, "description": "User not found"},
        403: {"model": AuthErrorResponse, "description": "Admin access required"}
    }
)
async def update_user_by_id(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user by ID (admin only).
    
    Args:
        user_id: User ID
        user_data: User update data
        db: Database session
        current_user: Current admin user
        
    Returns:
        Updated user information
    """
    user_service = UserService(db)
    updated_user = user_service.update_user(user_id, user_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.delete(
    "/users/{user_id}",
    summary="Delete user by ID",
    description="Delete user by ID (admin only)",
    dependencies=[Depends(require_admin)],
    responses={
        200: {"description": "User deleted successfully"},
        404: {"model": AuthErrorResponse, "description": "User not found"},
        403: {"model": AuthErrorResponse, "description": "Admin access required"}
    }
)
async def delete_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete user by ID (admin only).
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current admin user
        
    Returns:
        Success message
    """
    user_service = UserService(db)
    success = user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


# API Key Management Endpoints
@router.post(
    "/api-keys",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
    description="Create a new API key for the current user",
    responses={
        201: {"description": "API key created successfully"},
        401: {"model": AuthErrorResponse, "description": "Not authenticated"}
    }
)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new API key.
    
    Args:
        key_data: API key creation data
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Created API key with secret (shown only once)
    """
    api_key_service = APIKeyService(db)
    return api_key_service.create_api_key(current_user.id, key_data)


@router.get(
    "/api-keys",
    response_model=List[APIKeyResponse],
    summary="List API keys",
    description="Get all API keys for the current user",
    responses={
        200: {"description": "List of API keys"},
        401: {"model": AuthErrorResponse, "description": "Not authenticated"}
    }
)
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all API keys for the current user.
    
    Args:
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        List of API keys
    """
    api_key_service = APIKeyService(db)
    return api_key_service.get_user_api_keys(current_user.id)


@router.put(
    "/api-keys/{key_id}",
    response_model=APIKeyResponse,
    summary="Update API key",
    description="Update an API key's settings",
    responses={
        200: {"description": "API key updated successfully"},
        404: {"model": AuthErrorResponse, "description": "API key not found"},
        401: {"model": AuthErrorResponse, "description": "Not authenticated"}
    }
)
async def update_api_key(
    key_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an API key.
    
    Args:
        key_id: API key ID
        update_data: Update data
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Updated API key
    """
    api_key_service = APIKeyService(db)
    updated_key = api_key_service.update_api_key(key_id, current_user.id, update_data)
    
    if not updated_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return updated_key


@router.delete(
    "/api-keys/{key_id}",
    summary="Delete API key",
    description="Delete an API key",
    responses={
        200: {"description": "API key deleted successfully"},
        404: {"model": AuthErrorResponse, "description": "API key not found"},
        401: {"model": AuthErrorResponse, "description": "Not authenticated"}
    }
)
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an API key.
    
    Args:
        key_id: API key ID
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    api_key_service = APIKeyService(db)
    success = api_key_service.delete_api_key(key_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key deleted successfully"}


# Usage Analytics Endpoints
@router.get(
    "/usage/stats",
    response_model=UsageStatsResponse,
    summary="Get usage statistics",
    description="Get usage statistics for the current user",
    responses={
        200: {"description": "Usage statistics"},
        401: {"model": AuthErrorResponse, "description": "Not authenticated"}
    }
)
async def get_usage_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics for the current user.
    
    Args:
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Usage statistics
    """
    usage_service = UsageService(db)
    return usage_service.get_user_usage_stats(current_user.id)