"""Authentication package initialization."""

from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse,
    Token, TokenData, RoleEnum,
    UsageLogCreate, UsageLogResponse, UsageStatsResponse,
    PermissionCreate, PermissionResponse,
    AuthErrorResponse
)

from .services import UserService, APIKeyService, UsageService

from .dependencies import (
    get_current_user, get_current_active_user, get_optional_user,
    require_role, require_permission,
    require_admin, require_developer, require_user, require_read_only,
    require_models_read, require_models_write, require_models_delete,
    require_generate_access, require_chat_access
)

from .utils import (
    verify_password, get_password_hash, create_access_token, verify_token,
    generate_api_key, hash_api_key, verify_api_key,
    AuthenticationError, AuthorizationError
)

__all__ = [
    # Schemas
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "APIKeyCreate", "APIKeyResponse", "APIKeyCreateResponse", 
    "Token", "TokenData", "RoleEnum",
    "UsageLogCreate", "UsageLogResponse", "UsageStatsResponse",
    "PermissionCreate", "PermissionResponse", "AuthErrorResponse",
    
    # Services
    "UserService", "APIKeyService", "UsageService",
    
    # Dependencies
    "get_current_user", "get_current_active_user", "get_optional_user",
    "require_role", "require_permission",
    "require_admin", "require_developer", "require_user", "require_read_only",
    "require_models_read", "require_models_write", "require_models_delete",
    "require_generate_access", "require_chat_access",
    
    # Utils
    "verify_password", "get_password_hash", "create_access_token", "verify_token",
    "generate_api_key", "hash_api_key", "verify_api_key",
    "AuthenticationError", "AuthorizationError"
]