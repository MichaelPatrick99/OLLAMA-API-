"""Authentication utilities for password hashing, token generation, etc."""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = getattr(settings, 'SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> tuple[str, str]:
    """Generate an API key pair.
    
    Returns:
        Tuple of (key_id, secret) where:
        - key_id: Public identifier (prefix for the key)
        - secret: The actual secret to be hashed and stored
    """
    # Generate a unique key ID (public identifier)
    key_id = f"oak_{secrets.token_urlsafe(16)}"  # oak = Ollama API Key
    
    # Generate the secret (what user will use)
    secret = secrets.token_urlsafe(32)
    
    return key_id, secret


def hash_api_key(secret: str) -> str:
    """Hash an API key secret for storage.
    
    Args:
        secret: The API key secret
        
    Returns:
        Hashed secret for database storage
    """
    # Use SHA-256 for API keys (faster than bcrypt, still secure for tokens)
    return hashlib.sha256(secret.encode()).hexdigest()


def verify_api_key(secret: str, hashed_secret: str) -> bool:
    """Verify an API key secret against its hash.
    
    Args:
        secret: Plain API key secret
        hashed_secret: Hashed secret from database
        
    Returns:
        True if secret matches, False otherwise
    """
    return hashlib.sha256(secret.encode()).hexdigest() == hashed_secret


def extract_api_key_from_header(authorization: str) -> Optional[str]:
    """Extract API key from Authorization header.
    
    Expected format: "Bearer oak_xxxxxxxxxxxxx"
    
    Args:
        authorization: Authorization header value
        
    Returns:
        API key or None if invalid format
    """
    if not authorization:
        return None
    
    try:
        scheme, credentials = authorization.split()
        if scheme.lower() != "bearer":
            return None
        
        # Validate API key format
        if not credentials.startswith("oak_"):
            return None
            
        return credentials
    except ValueError:
        return None


def get_current_time() -> datetime:
    """Get current UTC time.
    
    Returns:
        Current UTC datetime
    """
    return datetime.utcnow()


def is_token_expired(expires_at: datetime) -> bool:
    """Check if a token/key has expired.
    
    Args:
        expires_at: Expiration datetime
        
    Returns:
        True if expired, False otherwise
    """
    if not expires_at:
        return False
    return get_current_time() > expires_at


def generate_secure_random_string(length: int = 32) -> str:
    """Generate a secure random string.
    
    Args:
        length: Length of the string
        
    Returns:
        Secure random string
    """
    return secrets.token_urlsafe(length)


class AuthenticationError(HTTPException):
    """Custom authentication error."""
    
    def __init__(self, detail: str = "Authentication failed", error_code: str = "AUTH_ERROR"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
        self.error_code = error_code


class AuthorizationError(HTTPException):
    """Custom authorization error."""
    
    def __init__(self, detail: str = "Insufficient permissions", error_code: str = "AUTHZ_ERROR"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
        self.error_code = error_code