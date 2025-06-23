"""Database models for authentication and authorization."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from enum import Enum as PyEnum

from database.connection import Base


class RoleEnum(PyEnum):
    """User role enumeration."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    READ_ONLY = "read_only"


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default=RoleEnum.USER.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")


class APIKey(Base):
    """API Key model for programmatic access."""
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(32), unique=True, index=True, nullable=False)  # Public identifier
    key_hash = Column(String(255), nullable=False)  # Hashed secret
    name = Column(String(100), nullable=False)  # Human-readable name
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default=RoleEnum.USER.value, nullable=False)
    
    # Usage limits and tracking
    usage_limit_per_hour = Column(Integer, default=100, nullable=False)
    usage_limit_per_day = Column(Integer, default=1000, nullable=False)
    usage_limit_per_month = Column(Integer, default=10000, nullable=False)
    current_hour_usage = Column(Integer, default=0, nullable=False)
    current_day_usage = Column(Integer, default=0, nullable=False)
    current_month_usage = Column(Integer, default=0, nullable=False)
    total_usage = Column(Integer, default=0, nullable=False)
    
    # Status and dates
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    usage_logs = relationship("UsageLog", back_populates="api_key", cascade="all, delete-orphan")


class UsageLog(Base):
    """Usage tracking for API calls."""
    
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    
    # Request details
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    model_used = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # Performance metrics
    response_time_ms = Column(Float, nullable=True)
    status_code = Column(Integer, nullable=False)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    api_key = relationship("APIKey", back_populates="usage_logs")


class Permission(Base):
    """Permission model for fine-grained access control."""
    
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False)  # e.g., 'models', 'generate', 'chat'
    action = Column(String(50), nullable=False)    # e.g., 'read', 'write', 'delete'
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RolePermission(Base):
    """Many-to-many relationship between roles and permissions."""
    
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    permission = relationship("Permission")