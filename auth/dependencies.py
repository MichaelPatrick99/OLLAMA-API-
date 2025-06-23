"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Union
from datetime import datetime

from database.connection import get_db
from database.models import User, APIKey, UsageLog, RoleEnum
from auth.utils import (
    verify_token, 
    extract_api_key_from_header, 
    verify_api_key,
    AuthenticationError,
    AuthorizationError,
    is_token_expired
)
from auth.schemas import TokenData, RoleEnum as SchemaRoleEnum


# Security scheme for bearer tokens
security = HTTPBearer(auto_error=False)


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token.
    
    Args:
        credentials: Bearer token credentials
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
        
    Raises:
        AuthenticationError: If token is invalid
    """
    if not credentials:
        return None
    
    # Verify the token
    payload = verify_token(credentials.credentials)
    if not payload:
        raise AuthenticationError("Invalid token")
    
    # Extract user info from token
    user_id = payload.get("user_id")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("User account is deactivated")
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


async def get_current_user_from_api_key(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from API key.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
        
    Raises:
        AuthenticationError: If API key is invalid
    """
    # Extract API key from Authorization header
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    
    api_key_secret = extract_api_key_from_header(authorization)
    if not api_key_secret:
        return None
    
    # Find API key in database
    api_key = db.query(APIKey).filter(APIKey.key_id == api_key_secret.split("_")[1]).first()
    if not api_key:
        raise AuthenticationError("Invalid API key")
    
    # Verify the API key secret
    if not verify_api_key(api_key_secret, api_key.key_hash):
        raise AuthenticationError("Invalid API key")
    
    # Check if API key is active
    if not api_key.is_active:
        raise AuthenticationError("API key is deactivated")
    
    # Check if API key has expired
    if api_key.expires_at and is_token_expired(api_key.expires_at):
        raise AuthenticationError("API key has expired")
    
    # Get the user associated with the API key
    user = db.query(User).filter(User.id == api_key.user_id).first()
    if not user or not user.is_active:
        raise AuthenticationError("User account is deactivated")
    
    # Update API key usage
    api_key.last_used = datetime.utcnow()
    api_key.total_usage += 1
    
    # Check usage limits (this will be enforced in middleware)
    # We're just updating counters here
    current_hour = datetime.utcnow().hour
    if not hasattr(api_key, '_current_hour') or api_key._current_hour != current_hour:
        api_key.current_hour_usage = 1
        api_key._current_hour = current_hour
    else:
        api_key.current_hour_usage += 1
    
    db.commit()
    
    # Store API key info in request state for middleware
    request.state.api_key = api_key
    
    return user


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from either JWT token or API key.
    
    Args:
        request: FastAPI request object
        credentials: Bearer token credentials
        db: Database session
        
    Returns:
        Authenticated user
        
    Raises:
        AuthenticationError: If authentication fails
    """
    # Try JWT token first
    user = await get_current_user_from_token(credentials, db)
    if user:
        return user
    
    # Try API key authentication
    user = await get_current_user_from_api_key(request, db)
    if user:
        return user
    
    # No authentication provided
    raise AuthenticationError("Authentication required")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active user
        
    Raises:
        AuthenticationError: If user is not active
    """
    if not current_user.is_active:
        raise AuthenticationError("User account is deactivated")
    
    return current_user


def require_role(required_role: RoleEnum):
    """Dependency factory for role-based access control.
    
    Args:
        required_role: Required role for access
        
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Check if user has required role.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            User if authorized
            
        Raises:
            AuthorizationError: If user doesn't have required role
        """
        user_role = RoleEnum(current_user.role)
        
        # Define role hierarchy (higher roles include lower role permissions)
        role_hierarchy = {
            RoleEnum.ADMIN: [RoleEnum.ADMIN, RoleEnum.DEVELOPER, RoleEnum.USER, RoleEnum.READ_ONLY],
            RoleEnum.DEVELOPER: [RoleEnum.DEVELOPER, RoleEnum.USER, RoleEnum.READ_ONLY],
            RoleEnum.USER: [RoleEnum.USER, RoleEnum.READ_ONLY],
            RoleEnum.READ_ONLY: [RoleEnum.READ_ONLY]
        }
        
        if required_role not in role_hierarchy.get(user_role, []):
            raise AuthorizationError(
                f"Role '{required_role.value}' required. User has role '{user_role.value}'"
            )
        
        return current_user
    
    return role_checker


def require_permission(resource: str, action: str):
    """Dependency factory for permission-based access control.
    
    Args:
        resource: Resource name (e.g., 'models', 'generate')
        action: Action name (e.g., 'read', 'write', 'delete')
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if user has required permission.
        
        Args:
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            User if authorized
            
        Raises:
            AuthorizationError: If user doesn't have required permission
        """
        # For now, we'll use role-based permissions
        # This can be extended to use the Permission and RolePermission tables
        
        user_role = RoleEnum(current_user.role)
        
        # Define permissions for each role
        role_permissions = {
            RoleEnum.ADMIN: ["*"],  # Admin has all permissions
            RoleEnum.DEVELOPER: [
                "models:read", "models:write", "models:delete",
                "generate:read", "generate:write",
                "chat:read", "chat:write",
                "api_keys:read", "api_keys:write", "api_keys:delete"
            ],
            RoleEnum.USER: [
                "models:read",
                "generate:read", "generate:write",
                "chat:read", "chat:write",
                "api_keys:read", "api_keys:write"
            ],
            RoleEnum.READ_ONLY: [
                "models:read",
                "generate:read",
                "chat:read"
            ]
        }
        
        required_permission = f"{resource}:{action}"
        user_permissions = role_permissions.get(user_role, [])
        
        # Check if user has the specific permission or wildcard permission
        if "*" not in user_permissions and required_permission not in user_permissions:
            raise AuthorizationError(
                f"Permission '{required_permission}' required. "
                f"User role '{user_role.value}' does not have this permission."
            )
        
        return current_user
    
    return permission_checker


# Convenience dependencies for common role requirements
require_admin = require_role(RoleEnum.ADMIN)
require_developer = require_role(RoleEnum.DEVELOPER)
require_user = require_role(RoleEnum.USER)
require_read_only = require_role(RoleEnum.READ_ONLY)

# Convenience dependencies for common permission requirements
require_models_read = require_permission("models", "read")
require_models_write = require_permission("models", "write")
require_models_delete = require_permission("models", "delete")
require_generate_access = require_permission("generate", "write")
require_chat_access = require_permission("chat", "write")


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, but don't require authentication.
    
    Args:
        request: FastAPI request object
        credentials: Bearer token credentials
        db: Database session
        
    Returns:
        User if authenticated, None otherwise
    """
    try:
        return await get_current_user(request, credentials, db)
    except AuthenticationError:
        return None