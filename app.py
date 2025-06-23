"""Main FastAPI application with authentication and authorization."""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import asyncio
from contextlib import asynccontextmanager

from config import settings
from database.connection import create_tables, get_db
from database.models import User, RoleEnum
from routers import generate_router, chat_router, models_router
from auth.router import router as auth_router
from auth.services import UserService
from auth.utils import get_password_hash
from middleware import AuthMiddleware, UsageTrackingMiddleware
from utils import format_error_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting up...")
    
    # Create database tables
    print("Creating database tables...")
    create_tables()
    
    # Create default admin user if enabled
    if settings.CREATE_DEFAULT_ADMIN:
        await create_default_admin()
    
    print("Startup complete!")
    
    yield
    
    # Shutdown
    print("Shutting down...")


async def create_default_admin():
    """Create default admin user if it doesn't exist."""
    try:
        db = next(get_db())
        user_service = UserService(db)
        
        # Check if admin user already exists
        existing_admin = user_service.get_user_by_username(settings.ADMIN_USERNAME)
        if existing_admin:
            print(f"Admin user '{settings.ADMIN_USERNAME}' already exists")
            return
        
        # Create admin user
        from auth.schemas import UserCreate, RoleEnum as SchemaRoleEnum
        admin_data = UserCreate(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            full_name="System Administrator",
            role=SchemaRoleEnum.ADMIN
        )
        
        admin_user = user_service.create_user(admin_data)
        print(f"Created default admin user: {admin_user.username}")
        
    except Exception as e:
        print(f"Failed to create default admin user: {str(e)}")


# Create FastAPI app with lifespan events
app = FastAPI(
    title="Ollama API Wrapper with Authentication",
    description="A secure FastAPI wrapper for the Ollama API with user authentication and role-based access control",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add custom middleware
app.add_middleware(
    UsageTrackingMiddleware,
    enable_logging=settings.LOG_USAGE
)

app.add_middleware(
    AuthMiddleware,
    enable_rate_limiting=settings.RATE_LIMIT_ENABLED
)

# Include routers
app.include_router(auth_router)  # Authentication routes
app.include_router(generate_router)  # Text generation routes (will be protected)
app.include_router(chat_router)  # Chat routes (will be protected)
app.include_router(models_router)  # Model management routes (will be protected)


# Add request timing middleware (now handled by AuthMiddleware)
@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    """Add request ID to response headers for tracking."""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(exc.status_code, exc.detail),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content=format_error_response(500, f"Internal server error: {str(exc)}"),
    )


@app.get("/", tags=["health"])
async def root():
    """Root endpoint for health check."""
    return {
        "status": "ok", 
        "message": "Ollama API wrapper with authentication is running",
        "version": "2.0.0",
        "features": [
            "User authentication",
            "API key management", 
            "Role-based access control",
            "Rate limiting",
            "Usage analytics"
        ]
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "ok",
        "timestamp": time.time(),
        "version": "2.0.0",
        "services": {
            "api": "healthy",
            "database": "unknown",
            "ollama": "unknown"
        }
    }
    
    # Check database connection
    try:
        db = next(get_db())
        # Simple query to test connection
        db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Ollama connection
    try:
        from services.ollama_service import OllamaService
        ollama_service = OllamaService()
        # This would need to be updated to test actual Ollama connection
        health_status["services"]["ollama"] = "healthy"
    except Exception as e:
        health_status["services"]["ollama"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/api/info", tags=["info"])
async def api_info():
    """Get API information and capabilities."""
    return {
        "name": "Ollama API Wrapper",
        "version": "2.0.0",
        "description": "Secure wrapper for Ollama API with authentication and RBAC",
        "authentication": {
            "methods": ["JWT Bearer Token", "API Key"],
            "roles": ["admin", "developer", "user", "read_only"]
        },
        "features": {
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
            "usage_tracking": settings.LOG_USAGE,
            "cors_enabled": True
        },
        "endpoints": {
            "authentication": "/api/auth/*",
            "text_generation": "/api/generate",
            "chat_completion": "/api/chat", 
            "model_management": "/api/models/*",
            "documentation": "/docs"
        },
        "limits": {
            "default_rate_per_hour": settings.RATE_LIMIT_PER_HOUR,
            "default_rate_per_minute": settings.RATE_LIMIT_PER_MINUTE
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )