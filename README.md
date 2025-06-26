# 🤖 Ollama API Wrapper with Authentication

A secure, production-ready FastAPI wrapper for the Ollama API featuring comprehensive authentication, role-based access control, and a beautiful web interface.

## 🎯 Features

### 🔐 **Authentication & Security**
- **Dual Authentication**: JWT Bearer tokens + API key authentication
- **Role-Based Access Control**: Admin, Developer, User, and Read-Only roles
- **Advanced Security**: Rate limiting, password requirements, secure token management
- **Session Management**: Persistent login sessions with automatic token refresh

### 🌐 **Web Interface**
- **Modern Dashboard**: Beautiful, responsive web interface
- **Real-time Status**: Live API and Ollama connection monitoring
- **Interactive Chat**: Full conversational AI interface
- **API Key Management**: Create, manage, and monitor API keys
- **Admin Panel**: User management and usage analytics

### 🚀 **API Features**
- **Text Generation**: Single prompt text generation
- **Chat Completion**: Multi-turn conversations with context
- **Model Management**: List and manage Ollama models
- **Usage Analytics**: Comprehensive request tracking and statistics
- **Rate Limiting**: Configurable per-user rate limits

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Database**: SQLite (included) or PostgreSQL
- **Ollama**: Latest version for AI model inference
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 5-50GB for Ollama models

## 🚀 Quick Start

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd ollama-api-wrapper

# Create virtual environment
python -m venv ollama-env
source ollama-env/bin/activate  # On Windows: ollama-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (use your favorite editor)
nano .env
```

**Key settings to update in `.env`:**
```env
# Database (SQLite is ready to use)
DATABASE_URL=sqlite:///./ollama_api.db

# Authentication (⚠️ CHANGE THESE!)
SECRET_KEY=your_super_secret_key_here
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_PASSWORD=YourSecurePassword123!

# Ollama API
OLLAMA_API_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3:8b
```

### 3. Initialize Database

```bash
# Create database tables
alembic upgrade head

# The default admin user will be created automatically on first startup
```

### 4. Install and Start Ollama

#### Windows:
1. Download from [ollama.com](https://ollama.com/download)
2. Install and run the installer
3. Start Ollama:
```powershell
ollama serve
```

#### Download a Model:
```bash
# Recommended: Balanced performance model
ollama pull llama3:8b

# Or try a smaller model for testing
ollama pull phi3:mini
```

### 5. Start the Application

```bash
# Start the API server
python app.py

# The server will start on http://localhost:3000
```

### 6. Access the Web Interface

```bash
# Navigate to the frontend directory
cd frontend

# Start the frontend server
python -m http.server 8080

# Open your browser to: http://localhost:8080
```

## 🌐 Using the Web Interface

### **Login**
- **URL**: `http://localhost:8080`
- **Default Admin**: `admin` / `AdminPassword123!` (change this!)

### **Dashboard Features**
1. **Overview**: Account info, usage statistics, system status
2. **API Keys**: Create and manage API keys for programmatic access
3. **Generate**: Single-prompt text generation interface
4. **Chat**: Interactive conversational AI
5. **Models**: View and manage available Ollama models
6. **Admin**: User management and system analytics (admin only)

## 🔑 API Usage

### **Authentication Methods**

#### Method 1: JWT Token Authentication
```bash
# 1. Login to get token
curl -X POST "http://localhost:3000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=AdminPassword123!"

# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# 2. Use token for API calls
curl -X POST "http://localhost:3000/api/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?", "model": "llama3:8b"}'
```

#### Method 2: API Key Authentication
```bash
# 1. Create API key via web interface or API
curl -X POST "http://localhost:3000/api/auth/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "description": "For my application"}'

# 2. Use API key for requests
curl -X POST "http://localhost:3000/api/generate" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a Python function", "model": "llama3:8b"}'
```

### **Key API Endpoints**

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/` | GET | Health check | No |
| `/api/auth/login` | POST | User login | No |
| `/api/auth/register` | POST | User registration | No |
| `/api/auth/me` | GET | Current user info | Yes |
| `/api/auth/api-keys` | POST/GET | Manage API keys | Yes |
| `/api/generate` | POST | Text generation | Yes |
| `/api/chat` | POST | Chat completion | Yes |
| `/api/models` | GET | List models | Yes |
| `/docs` | GET | API documentation | No |

## 👥 User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access, user management, all API endpoints |
| **Developer** | API access, model management, usage analytics |
| **User** | Basic API access, text generation, chat |
| **Read-Only** | View-only access, no generation capabilities |

## 🔧 Advanced Configuration

### **Database Options**

#### SQLite (Default - Recommended for Development)
```env
DATABASE_URL=sqlite:///./ollama_api.db
```

#### PostgreSQL (Recommended for Production)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/ollama_api
```

### **Rate Limiting**
```env
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### **Security Settings**
```env
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=True
PASSWORD_REQUIRE_LOWERCASE=True
PASSWORD_REQUIRE_DIGITS=True
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### **Ollama Configuration**
```env
OLLAMA_API_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3:8b
REQUEST_TIMEOUT=60.0
```

## 🛠️ Development

### **Project Structure**
```
ollama-api-wrapper/
├── frontend/                 # Web interface
│   ├── index.html           # Main dashboard
│   ├── css/                 # Styling
│   └── js/                  # Frontend logic
├── auth/                    # Authentication system
│   ├── router.py           # Auth endpoints
│   ├── services.py         # Business logic
│   └── schemas.py          # Data models
├── database/               # Database layer
│   ├── models.py           # SQLAlchemy models
│   └── connection.py       # DB connection
├── routers/                # API endpoints
├── migrations/             # Database migrations
├── app.py                  # Main application
└── config.py              # Configuration
```

### **Adding New Features**

1. **New API Endpoint**:
   - Add router in `routers/`
   - Include in `app.py`
   - Add authentication decorator

2. **Database Changes**:
   - Update `database/models.py`
   - Create migration: `alembic revision --autogenerate -m "Description"`
   - Apply: `alembic upgrade head`

3. **Frontend Updates**:
   - Update relevant files in `frontend/`
   - Test in browser at `http://localhost:8080`

### **Testing**

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=. tests/
```

## 🚀 Production Deployment

### **Security Checklist**
- [ ] Change default admin credentials
- [ ] Generate new SECRET_KEY
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Configure firewall rules
- [ ] Set up monitoring
- [ ] Regular backups

### **Environment Variables for Production**
```env
DEBUG=False
SECRET_KEY=your_super_secure_secret_key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
CORS_ORIGINS=["https://yourdomain.com"]
LOG_LEVEL=INFO
```

### **Docker Deployment**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:3000"]
```

## 🔍 Troubleshooting

### **Common Issues**

#### **"Ollama connection failed"**
- ✅ Ensure Ollama is running: `ollama serve`
- ✅ Check if model is downloaded: `ollama list`
- ✅ Verify Ollama URL in `.env`

#### **"Database connection error"**
- ✅ Check database URL in `.env`
- ✅ Run migrations: `alembic upgrade head`
- ✅ Ensure database permissions

#### **"Authentication failed"**
- ✅ Check username/password
- ✅ Verify admin user was created
- ✅ Check token expiration

#### **"CORS errors in browser"**
- ✅ Use local server: `python -m http.server 8080`
- ✅ Don't open HTML file directly
- ✅ Check CORS settings in `.env`

### **Debugging**

```bash
# Check API health
curl http://localhost:3000/

# View logs
tail -f logs/app.log

# Check database
python -c "from database.models import User; print(User.query.all())"
```

## 📚 API Documentation

- **Interactive Docs**: `http://localhost:3000/docs`
- **OpenAPI Spec**: `http://localhost:3000/openapi.json`
- **ReDoc**: `http://localhost:3000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Documentation**: [Wiki](https://github.com/your-repo/wiki)

## 🎉 Acknowledgments

- **Ollama**: For the amazing local AI model runtime
- **FastAPI**: For the excellent web framework
- **SQLAlchemy**: For robust database ORM
- **Community**: For feedback and contributions

---

**Happy Coding! 🚀**