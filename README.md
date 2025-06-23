# Ollama API Wrapper with Authentication

A secure, production-ready FastAPI wrapper for the Ollama API featuring comprehensive authentication, role-based access control, and advanced usage analytics.

## 🚀 Features

### Core Functionality
- **Text Generation**: Non-streaming and streaming text generation from prompts
- **Chat Completion**: Conversational AI with full message history support
- **Model Management**: Download, list, inspect, and delete Ollama models

### 🔐 Security & Authentication
- **Dual Authentication**: JWT Bearer tokens and API key authentication
- **Role-Based Access Control (RBAC)**: Admin, Developer, User, and Read-Only roles
- **API Key Management**: Create, manage, and monitor API keys with usage limits
- **Rate Limiting**: Configurable per-hour, per-day, and per-month limits
- **Usage Tracking**: Comprehensive analytics and monitoring

### 🏗️ Architecture
- **Production Ready**: Proper error handling, logging, and monitoring
- **Database Integration**: PostgreSQL with SQLAlchemy ORM
- **Middleware**: Authentication, rate limiting, and usage tracking
- **Comprehensive Testing**: Full test suite with authentication scenarios
- **API Documentation**: Auto-generated Swagger UI with authentication examples

## 📋 Requirements

- Python 3.8+
- PostgreSQL 12+
- Redis 6+ (optional, for enhanced rate limiting)
- Ollama API running locally or remotely

## 🛠️ Installation

### 1. Clone and Setup

```bash
# Clone the repository (or your forked version)
git clone <your-repo-url>
cd ollama-api-wrapper

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Start PostgreSQL and Redis with Docker Compose
docker-compose up -d postgres redis

# Or install locally and create database
createdb ollama_api
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

Key environment variables:
```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/ollama_api

# Authentication
SECRET_KEY=your_super_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama API
OLLAMA_API_BASE_URL=http://localhost:11434

# Admin User (created automatically)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change_this_secure_password
```

### 4. Database Migration

```bash
# Initialize Alembic (first time only)
alembic init migrations

# Create initial migration
alembic revision --autogenerate -m "Initial tables"

# Apply migrations
alembic upgrade head
```

### 5. Start the Application

```bash
# Development mode
python app.py

# Production mode with Gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:3000
```

## 🔑 Authentication

### User Registration & Login

```bash
# Register a new user
curl -X POST "http://localhost:3000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "developer1",
    "email": "dev@company.com",
    "password": "SecurePass123",
    "full_name": "Jane Developer",
    "role": "developer"
  }'

# Login to get access token
curl -X POST "http://localhost:3000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=developer1&password=SecurePass123"
```

### API Key Management

```bash
# Create API key (requires authentication)
curl -X POST "http://localhost:3000/api/auth/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "usage_limit_per_hour": 1000,
    "usage_limit_per_day": 10000,
    "usage_limit_per_month": 100000
  }'

# List your API keys
curl -X GET "http://localhost:3000/api/auth/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🎯 API Usage

### Text Generation

```bash
# With JWT Token
curl -X POST "http://localhost:3000/api/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to calculate fibonacci numbers",
    "model": "llama3:8b",
    "stream": false
  }'

# With API Key
curl -X POST "http://localhost:3000/api/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing",
    "model": "llama3:8b",
    "stream": true
  }'
```

### Chat Completion

```bash
curl -X POST "http://localhost:3000/api/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful coding assistant"},
      {"role": "user", "content": "How do I implement authentication in FastAPI?"}
    ],
    "model": "llama3:8b",
    "stream": false
  }'
```

### Model Management

```bash
# List available models
curl -X GET "http://localhost:3000/api/models" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Download a model (requires developer+ role)
curl -X POST "http://localhost:3000/api/models/download" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "codellama:7b"}'

# Get model information
curl -X GET "http://localhost:3000/api/models/llama3:8b" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 👥 Role-Based Access Control

### Role Hierarchy
- **Admin**: Full system access, user management, all model operations
- **Developer**: Model management, full API access, API key management
- **User**: Basic API usage, limited model operations, own API key management
- **Read-Only**: View-only access, cannot modify anything

### Permission Matrix
| Endpoint | Admin | Developer | User | Read-Only |
|----------|-------|-----------|------|-----------|
| Text Generation | ✅ | ✅ | ✅ | ❌ |
| Chat Completion | ✅ | ✅ | ✅ | ❌ |
| List Models | ✅ | ✅ | ✅ | ✅ |
| Download Models | ✅ | ✅ | ✅ | ❌ |
| Delete Models | ✅ | ✅ | ❌ | ❌ |
| User Management | ✅ | ❌ | ❌ | ❌ |
| View All Users | ✅ | ❌ | ❌ | ❌ |
| API Key Management | ✅ | ✅ | ✅ | ✅ |
| Usage Analytics | ✅ | ✅ | ✅ | ✅ |

## 📊 Usage Analytics & Monitoring

### View Your Usage Statistics

```bash
# Get your usage stats
curl -X GET "http://localhost:3000/api/auth/usage/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get generation-specific usage
curl -X GET "http://localhost:3000/api/generate/usage" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get chat-specific usage
curl -X GET "http://localhost:3000/api/chat/usage" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Rate Limits

Default rate limits by role:
- **Admin**: Unlimited
- **Developer**: 10,000 requests/day, 10 concurrent
- **User**: 1,000 requests/day, 5 concurrent  
- **Read-Only**: 100 requests/day, 2 concurrent

API keys can have custom limits set during creation.

## 🧪 Testing

### Run the Test Suite

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Create test database
createdb ollama_api_test

# Run all tests
pytest

# Run specific test categories
pytest tests/test_auth.py -v
pytest tests/test_protected_endpoints.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Test Authentication Flow

```bash
# Test user registration
curl -X POST "http://localhost:3000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "TestPass123"
  }'

# Test login
curl -X POST "http://localhost:3000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPass123"
```

## 🔧 Development

### Project Structure

```
ollama-api-wrapper/
├── auth/                    # Authentication module
│   ├── dependencies.py     # FastAPI auth dependencies  
│   ├── router.py           # Auth endpoints
│   ├── schemas.py          # Pydantic models
│   ├── services.py         # Business logic
│   └── utils.py            # Auth utilities
├── database/               # Database layer
│   ├── connection.py       # DB connection setup
│   └── models.py           # SQLAlchemy models
├── middleware/             # Custom middleware
│   ├── auth_middleware.py  # Authentication middleware
│   └── usage_tracking.py   # Usage tracking middleware
├── routers/                # Protected API endpoints
│   ├── chat.py            # Chat completion (protected)
│   ├── generate.py        # Text generation (protected)
│   └── models.py          # Model management (protected)
├── services/               # Business logic
│   └── ollama_service.py   # Ollama API integration
├── tests/                  # Test suite
│   ├── test_auth.py       # Authentication tests
│   └── test_protected_endpoints.py
├── migrations/             # Database migrations
├── app.py                 # Main application
├── config.py              # Configuration
└── requirements.txt       # Dependencies
```

### Adding New Features

1. **Create new router** in `routers/`
2. **Add authentication** using dependencies from `auth.dependencies`
3. **Implement business logic** in `services/`
4. **Add tests** in `tests/`
5. **Update documentation**

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback migration  
alembic downgrade -1
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3000

CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:3000"]
```

```bash
# Build and run
docker build -t ollama-api-auth .
docker run -p 3000:3000 --env-file .env ollama-api-auth
```

### Production Checklist

- [ ] Change default admin password
- [ ] Set strong SECRET_KEY
- [ ] Configure proper database credentials
- [ ] Set up SSL/TLS (HTTPS)
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set proper CORS origins
- [ ] Review security headers

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: `http://localhost:3000/docs`
- **ReDoc**: `http://localhost:3000/redoc`

### Health Checks

```bash
# Basic health check
curl http://localhost:3000/health

# Detailed API info
curl http://localhost:3000/api/info
```

## 🔒 Security Best Practices

### For Administrators
1. **Change default credentials** immediately
2. **Use strong, unique passwords** for all accounts
3. **Regularly rotate API keys** and monitor usage
4. **Enable rate limiting** to prevent abuse
5. **Monitor usage logs** for suspicious activity
6. **Keep the system updated** with security patches

### For Developers
1. **Store API keys securely** (use environment variables)
2. **Never commit credentials** to version control
3. **Use HTTPS** in production
4. **Implement proper error handling** in your applications
5. **Monitor your usage** to stay within limits

### For Users
1. **Use strong passwords** for your account
2. **Don't share API keys** with others
3. **Rotate API keys** periodically
4. **Monitor your usage** to avoid unexpected charges
5. **Report suspicious activity** to administrators

## 🐛 Troubleshooting

### Common Issues

**Authentication Failed**
```bash
# Check if user exists and password is correct
curl -X POST "http://localhost:3000/api/auth/login" -d "username=user&password=pass"

# Verify token is not expired
# Check server logs for detailed error messages
```

**Rate Limit Exceeded**
```bash
# Check your current usage
curl -X GET "http://localhost:3000/api/auth/usage/stats" -H "Authorization: Bearer YOUR_TOKEN"

# Wait for rate limit reset or contact admin for limit increase
```

**Database Connection Error**
```bash
# Check database is running
docker-compose ps

# Verify connection string in .env
# Check database logs for errors
```

**Model Not Found**
```bash
# List available models
curl -X GET "http://localhost:3000/api/models" -H "Authorization: Bearer YOUR_TOKEN"

# Download the model if needed
curl -X POST "http://localhost:3000/api/models/download" -H "Authorization: Bearer YOUR_TOKEN" -d '{"name": "model_name"}'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run tests before committing
pytest

# Check code formatting
black . --check
flake8 .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Ollama](https://ollama.ai/) for the local LLM API
- [SQLAlchemy](https://sqlalchemy.org/) for database ORM
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation

## 📞 Support

- **Documentation**: Check the `/docs` endpoint for interactive API documentation
- **Issues**: Open an issue on GitHub for bug reports or feature requests
- **Discussions**: Use GitHub Discussions for questions and community support

---

**⚡ Ready to secure your Ollama API?** Follow the installation guide above and start building with confidence!