# 👨‍💻 Developer Guide

Complete guide for developers who want to contribute to or extend the Ollama API Wrapper with Authentication.

## 🏗️ Architecture Overview

### **System Components**

```mermaid
graph TB
    A[Frontend Web UI] --> B[FastAPI Application]
    B --> C[Authentication Layer]
    B --> D[Database Layer]
    B --> E[Ollama API]
    C --> F[JWT Tokens]
    C --> G[API Keys]
    D --> H[SQLite/PostgreSQL]
    E --> I[Local Ollama Models]
```

### **Authentication Flow**

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database
    participant O as Ollama

    U->>F: Login (username/password)
    F->>A: POST /api/auth/login
    A->>D: Validate credentials
    D-->>A: User data
    A-->>F: JWT token
    F->>A: Generate text (with token)
    A->>D: Log usage
    A->>O: Forward request
    O-->>A: AI response
    A-->>F: Formatted response
```

## 🔧 Development Setup

### **Prerequisites**
- Python 3.8+
- Node.js (optional, for advanced frontend dev)
- Git
- Ollama installed locally
- IDE with Python support (VS Code recommended)

### **Environment Setup**

```bash
# Clone repository
git clone <repo-url>
cd ollama-api-wrapper

# Create development environment
python -m venv dev-env
source dev-env/bin/activate  # Windows: dev-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools

# Setup pre-commit hooks
pre-commit install

# Copy environment template
cp .env.example .env.dev
```

### **Development Environment Variables**

Create `.env.dev`:
```env
# Development settings
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./dev_ollama_api.db

# Development admin
ADMIN_USERNAME=dev_admin
ADMIN_PASSWORD=DevPassword123!

# Disable rate limiting for development
RATE_LIMIT_ENABLED=False

# Enable CORS for development
CORS_ORIGINS=["http://localhost:8080", "http://127.0.0.1:8080"]
```

### **Database Setup**

```bash
# Initialize development database
alembic upgrade head

# Create test data (optional)
python scripts/create_test_data.py
```

## 📁 Project Structure Deep Dive

```
ollama-api-wrapper/
├── 📁 auth/                    # Authentication module
│   ├── 🐍 __init__.py
│   ├── 🐍 dependencies.py     # FastAPI dependencies
│   ├── 🐍 router.py           # Authentication endpoints
│   ├── 🐍 schemas.py          # Pydantic models
│   ├── 🐍 services.py         # Business logic
│   └── 🐍 utils.py            # Auth utilities
├── 📁 database/               # Database layer
│   ├── 🐍 __init__.py
│   ├── 🐍 connection.py       # Database connection
│   └── 🐍 models.py           # SQLAlchemy models
├── 📁 frontend/               # Web interface
│   ├── 🌐 index.html          # Main dashboard
│   ├── 📁 css/                # Stylesheets
│   │   ├── 🎨 styles.css      # Main styles
│   │   └── 🎨 components.css  # Component styles
│   └── 📁 js/                 # JavaScript modules
│       ├── 📜 main.js         # Application logic
│       ├── 📜 api.js          # API communication
│       ├── 📜 auth.js         # Authentication
│       └── 📜 components.js   # UI components
├── 📁 middleware/             # Custom middleware
│   ├── 🐍 __init__.py
│   ├── 🐍 auth_middleware.py  # Authentication middleware
│   └── 🐍 usage_tracking.py   # Usage tracking
├── 📁 routers/                # API endpoints
│   ├── 🐍 __init__.py
│   ├── 🐍 chat.py            # Chat endpoints
│   ├── 🐍 generate.py        # Text generation
│   └── 🐍 models.py          # Model management
├── 📁 services/               # Business services
│   ├── 🐍 __init__.py
│   └── 🐍 ollama_service.py   # Ollama integration
├── 📁 tests/                  # Test suite
│   ├── 🧪 test_auth.py        # Authentication tests
│   ├── 🧪 test_api.py         # API endpoint tests
│   └── 🧪 conftest.py         # Test configuration
├── 📁 migrations/             # Database migrations
├── 📁 scripts/                # Utility scripts
├── 🐍 app.py                  # Main application
├── 🐍 config.py               # Configuration
├── 📄 requirements.txt        # Dependencies
├── 📄 requirements-dev.txt    # Dev dependencies
└── 📄 .env.example            # Environment template
```

## 🧪 Testing

### **Running Tests**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_user_registration -v
```

### **Writing Tests**

Example test structure:
```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_user_login():
    """Test user login functionality."""
    response = client.post("/api/auth/login", data={
        "username": "test_user",
        "password": "test_password"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_protected_endpoint():
    """Test protected endpoint with authentication."""
    # Login first
    login_response = client.post("/api/auth/login", data={
        "username": "test_user",
        "password": "test_password"
    })
    token = login_response.json()["access_token"]
    
    # Use token for protected endpoint
    response = client.post("/api/generate", 
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": "Test prompt", "model": "test_model"}
    )
    assert response.status_code == 200
```

## 🔌 Adding New Features

### **1. Adding a New API Endpoint**

**Step 1**: Create router file (`routers/new_feature.py`):
```python
from fastapi import APIRouter, Depends
from auth.dependencies import get_current_active_user
from database.models import User

router = APIRouter(prefix="/api/new-feature", tags=["new-feature"])

@router.get("/")
async def get_new_feature(
    current_user: User = Depends(get_current_active_user)
):
    """New feature endpoint."""
    return {"message": "New feature works!", "user": current_user.username}
```

**Step 2**: Include in main app (`app.py`):
```python
from routers import new_feature

app.include_router(new_feature.router)
```

**Step 3**: Add frontend integration (`frontend/js/components.js`):
```javascript
async function testNewFeature() {
    try {
        const response = await apiClient.makeRequest('/api/new-feature');
        showMessage('New feature works!', 'success');
    } catch (error) {
        showMessage('Feature failed', 'error');
    }
}
```

### **2. Adding Database Models**

**Step 1**: Update models (`database/models.py`):
```python
class NewModel(Base):
    __tablename__ = "new_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationship
    user = relationship("User", back_populates="new_models")
```

**Step 2**: Create migration:
```bash
alembic revision --autogenerate -m "Add new model table"
alembic upgrade head
```

**Step 3**: Add to user model:
```python
# In User class
new_models = relationship("NewModel", back_populates="user")
```

### **3. Adding Authentication Permissions**

**Step 1**: Add permission to models:
```python
# In database/models.py
class Permission(Base):
    # Add new permission
    NEW_FEATURE_ACCESS = "new_feature_access"
```

**Step 2**: Create permission dependency:
```python
# In auth/dependencies.py
def require_new_feature_access(
    current_user: User = Depends(get_current_active_user)
):
    if not has_permission(current_user, "new_feature_access"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user
```

**Step 3**: Use in endpoints:
```python
@router.get("/protected")
async def protected_new_feature(
    current_user: User = Depends(require_new_feature_access)
):
    return {"message": "You have access!"}
```

### **4. Frontend Component Development**

**Component Structure**:
```javascript
// In frontend/js/components.js

/**
 * New Feature Component
 */
class NewFeatureComponent {
    constructor() {
        this.isLoaded = false;
        this.data = [];
    }
    
    async load() {
        try {
            showLoading('Loading new feature...');
            const response = await apiClient.makeRequest('/api/new-feature');
            this.data = response.data;
            this.render();
        } catch (error) {
            showMessage('Failed to load feature', 'error');
        } finally {
            hideLoading();
        }
    }
    
    render() {
        const container = document.getElementById('newFeatureContainer');
        if (!container) return;
        
        container.innerHTML = `
            <div class="feature-card">
                <h3>New Feature</h3>
                <p>Data loaded: ${this.data.length} items</p>
            </div>
        `;
    }
}

// Initialize component
const newFeatureComponent = new NewFeatureComponent();
```

## 🔒 Security Best Practices

### **Authentication Security**
```python
# Strong password validation
def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

# Secure token generation
def create_secure_token() -> str:
    return secrets.token_urlsafe(32)

# Rate limiting
@limiter.limit("5/minute")
async def sensitive_endpoint():
    pass
```

### **SQL Injection Prevention**
```python
# ✅ Good - Using SQLAlchemy ORM
user = session.query(User).filter(User.username == username).first()

# ✅ Good - Parameterized queries
result = session.execute(
    text("SELECT * FROM users WHERE username = :username"),
    {"username": username}
)

# ❌ Bad - String concatenation
query = f"SELECT * FROM users WHERE username = '{username}'"  # DON'T DO THIS
```

### **XSS Prevention**
```javascript
// ✅ Good - Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ✅ Good - Use textContent
element.textContent = userInput;

// ❌ Bad - Direct innerHTML
element.innerHTML = userInput;  // DON'T DO THIS
```

## 📊 Performance Optimization

### **Database Optimization**
```python
# Use indexes for frequently queried fields
class User(Base):
    username = Column(String, index=True)  # Add index
    email = Column(String, index=True)     # Add index

# Use eager loading to prevent N+1 queries
users = session.query(User).options(
    joinedload(User.api_keys),
    joinedload(User.usage_logs)
).all()

# Use pagination for large datasets
def get_users_paginated(skip: int = 0, limit: int = 100):
    return session.query(User).offset(skip).limit(limit).all()
```

### **API Performance**
```python
# Use async for I/O operations
async def call_ollama_api(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(ollama_url, json=data)
        return response.json()

# Cache frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=100)
def get_model_info(model_name: str):
    return expensive_model_lookup(model_name)
```

### **Frontend Performance**
```javascript
// Debounce user input
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Virtual scrolling for large lists
class VirtualList {
    constructor(container, itemHeight, renderItem) {
        this.container = container;
        this.itemHeight = itemHeight;
        this.renderItem = renderItem;
        this.setupScrollListener();
    }
}
```

## 🐛 Debugging

### **Backend Debugging**
```python
# Add detailed logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@router.post("/debug-endpoint")
async def debug_endpoint(data: dict):
    logger.debug(f"Received data: {data}")
    try:
        result = process_data(data)
        logger.info(f"Processing successful: {result}")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise

# Use debugger
import pdb; pdb.set_trace()  # Breakpoint

# Or use better debugger
import ipdb; ipdb.set_trace()  # Enhanced debugger
```

### **Frontend Debugging**
```javascript
// Comprehensive debug utilities
window.DebugUtils = {
    // Log all API calls
    logApiCalls: true,
    
    // Monitor authentication state
    watchAuth() {
        setInterval(() => {
            console.log('Auth State:', {
                isAuthenticated: authManager.isAuthenticated,
                user: authManager.currentUser?.username,
                token: authManager.token ? 'Present' : 'None'
            });
        }, 5000);
    },
    
    // Test API endpoints
    async testEndpoint(endpoint, method = 'GET', data = null) {
        try {
            const result = await apiClient.makeRequest(endpoint, {
                method,
                body: data ? JSON.stringify(data) : undefined
            });
            console.log(`✅ ${method} ${endpoint}:`, result);
            return result;
        } catch (error) {
            console.error(`❌ ${method} ${endpoint}:`, error);
            throw error;
        }
    },
    
    // Simulate network issues
    simulateNetworkError() {
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            if (Math.random() < 0.3) {
                return Promise.reject(new Error('Simulated network error'));
            }
            return originalFetch(...args);
        };
    }
};
```

### **Database Debugging**
```python
# Enable SQL query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Database inspection utilities
def inspect_database():
    """Debug utility to inspect database state."""
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"Table {table}:")
        for column in columns:
            print(f"  {column['name']}: {column['type']}")

# Performance monitoring
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # Log slow queries
        logger.warning(f"Slow query: {total:.3f}s - {statement[:100]}...")
```

## 🚀 Deployment Guide

### **Production Configuration**

**Environment Variables** (`.env.prod`):
```env
# Production settings
DEBUG=False
LOG_LEVEL=INFO
SECRET_KEY=super_secure_secret_key_32_chars_min

# Database
DATABASE_URL=postgresql://user:pass@db-host:5432/prod_db

# Security
CORS_ORIGINS=["https://yourdomain.com"]
RATE_LIMIT_ENABLED=True
PASSWORD_MIN_LENGTH=12

# Monitoring
LOG_FILE=/var/log/ollama-api/app.log
LOG_USAGE=True

# Performance
WORKERS=4
MAX_CONNECTIONS=100
```

### **Docker Deployment**

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Run application
CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:3000"]
```

**Docker Compose** (`docker-compose.prod.yml`):
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/ollama_api
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ollama_api
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

### **Monitoring & Logging**

**Structured Logging**:
```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage in code
logger.info("User logged in", user_id=user.id, username=user.username)
logger.error("Database error", error=str(e), query=query)
```

**Health Checks**:
```python
from fastapi import APIRouter
from sqlalchemy import text

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["checks"]["database"] = "healthy"
    except Exception as e:
        checks["checks"]["database"] = f"unhealthy: {str(e)}"
        checks["status"] = "unhealthy"
    
    # Ollama check
    try:
        response = await httpx.get(f"{settings.OLLAMA_API_BASE_URL}/api/tags")
        checks["checks"]["ollama"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        checks["checks"]["ollama"] = f"unhealthy: {str(e)}"
        checks["status"] = "unhealthy"
    
    return checks
```

## 📚 API Documentation Standards

### **Endpoint Documentation**
```python
@router.post("/generate", 
    response_model=GenerateResponse,
    summary="Generate text using AI model",
    description="Generate text based on a prompt using the specified AI model",
    responses={
        200: {"description": "Text generated successfully"},
        400: {"description": "Invalid prompt or model"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def generate_text(
    request: GenerateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate text using AI model.
    
    Args:
        request: Generation request containing prompt and parameters
        current_user: Authenticated user making the request
    
    Returns:
        GenerateResponse: Generated text and metadata
    
    Raises:
        HTTPException: If generation fails or user lacks permissions
    
    Example:
        ```json
        {
            "prompt": "Write a Python function to calculate factorial",
            "model": "llama3:8b",
            "temperature": 0.7,
            "max_tokens": 500
        }
        ```
    """
    pass
```

### **Schema Documentation**
```python
from pydantic import BaseModel, Field
from typing import Optional

class GenerateRequest(BaseModel):
    """Request model for text generation."""
    
    prompt: str = Field(
        ...,
        description="Text prompt for generation",
        example="Write a Python function to calculate factorial",
        min_length=1,
        max_length=10000
    )
    
    model: str = Field(
        default="llama3:8b",
        description="AI model to use for generation",
        example="llama3:8b"
    )
    
    temperature: float = Field(
        default=0.7,
        description="Randomness in generation (0.0 to 2.0)",
        ge=0.0,
        le=2.0,
        example=0.7
    )
    
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens to generate",
        gt=0,
        le=4096,
        example=500
    )
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "Write a Python function to calculate factorial",
                "model": "llama3:8b",
                "temperature": 0.7,
                "max_tokens": 500
            }
        }
```

## 🧩 Extension Points

### **Custom Authentication Providers**
```python
from abc import ABC, abstractmethod

class AuthProvider(ABC):
    """Abstract base class for authentication providers."""
    
    @abstractmethod
    async def authenticate(self, credentials: dict) -> Optional[User]:
        """Authenticate user with custom provider."""
        pass
    
    @abstractmethod
    async def get_user_info(self, user_id: str) -> dict:
        """Get additional user information."""
        pass

class LDAPAuthProvider(AuthProvider):
    """LDAP authentication provider."""
    
    async def authenticate(self, credentials: dict) -> Optional[User]:
        # LDAP authentication logic
        pass

class OAuthProvider(AuthProvider):
    """OAuth authentication provider."""
    
    async def authenticate(self, credentials: dict) -> Optional[User]:
        # OAuth authentication logic
        pass

# Register providers
auth_providers = {
    "ldap": LDAPAuthProvider(),
    "oauth": OAuthProvider()
}
```

### **Custom Middleware**
```python
from starlette.middleware.base import BaseHTTPMiddleware

class CustomLoggingMiddleware(BaseHTTPMiddleware):
    """Custom logging middleware for detailed request tracking."""
    
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info("Request started", 
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent")
        )
        
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info("Request completed",
            status_code=response.status_code,
            duration=duration
        )
        
        return response

# Add to application
app.add_middleware(CustomLoggingMiddleware)
```

### **Plugin System**
```python
from typing import Dict, Callable
import importlib

class PluginManager:
    """Plugin manager for extending functionality."""
    
    def __init__(self):
        self.plugins: Dict[str, object] = {}
        self.hooks: Dict[str, list] = {}
    
    def register_plugin(self, name: str, plugin: object):
        """Register a plugin."""
        self.plugins[name] = plugin
        
        # Auto-register hooks
        for attr_name in dir(plugin):
            if attr_name.startswith('hook_'):
                hook_name = attr_name[5:]  # Remove 'hook_' prefix
                if hook_name not in self.hooks:
                    self.hooks[hook_name] = []
                self.hooks[hook_name].append(getattr(plugin, attr_name))
    
    async def call_hook(self, hook_name: str, *args, **kwargs):
        """Call all registered hooks for an event."""
        if hook_name in self.hooks:
            for hook in self.hooks[hook_name]:
                await hook(*args, **kwargs)
    
    def load_plugins_from_directory(self, directory: str):
        """Load plugins from a directory."""
        import os
        for filename in os.listdir(directory):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]
                spec = importlib.util.spec_from_file_location(
                    module_name, 
                    os.path.join(directory, filename)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'Plugin'):
                    plugin = module.Plugin()
                    self.register_plugin(module_name, plugin)

# Usage
plugin_manager = PluginManager()
plugin_manager.load_plugins_from_directory('plugins/')

# In your endpoint
@router.post("/generate")
async def generate_text(request: GenerateRequest):
    await plugin_manager.call_hook('before_generate', request)
    result = await generate_text_logic(request)
    await plugin_manager.call_hook('after_generate', result)
    return result
```

## 🤝 Contributing Guidelines

### **Code Style**
```python
# Use Black for formatting
black .

# Use isort for imports
isort .

# Use flake8 for linting
flake8 .

# Use mypy for type checking
mypy .
```

### **Pre-commit Hooks** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### **Pull Request Template**
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Updated documentation

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for hard-to-understand areas
- [ ] Documentation updated
- [ ] No new warnings introduced
```

## 📈 Performance Monitoring

### **Metrics Collection**
```python
import time
from functools import wraps
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

def monitor_performance(func):
    """Decorator to monitor endpoint performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            REQUEST_COUNT.labels(method='POST', endpoint=func.__name__).inc()
            return result
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION.observe(duration)
    return wrapper

# Start metrics server
start_http_server(8000)  # Metrics available at http://localhost:8000
```

---

## 🎯 Summary

This developer guide covers:

- ✅ **Complete development setup** with proper environment configuration
- ✅ **Architecture deep dive** with system components and flow diagrams
- ✅ **Testing strategies** and best practices
- ✅ **Security implementation** patterns and guidelines
- ✅ **Performance optimization** techniques
- ✅ **Debugging tools** and methodologies
- ✅ **Deployment strategies** for production environments
- ✅ **Extension points** for custom functionality
- ✅ **Contributing guidelines** and code standards

This guide should help developers understand, contribute to, and extend the Ollama API wrapper effectively. For questions or contributions, please refer to the main README.md or open an issue in the repository.

**Happy coding! 🚀**