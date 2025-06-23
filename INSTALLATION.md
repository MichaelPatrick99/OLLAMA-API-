# 📦 Complete Installation Guide

## Quick Installation Options

### 1. Standard Installation
```bash
pip install -r requirements.txt
```

### 2. Development Installation
```bash
pip install -r requirements-dev.txt
```

### 3. Production Installation
```bash
pip install -r requirements-prod.txt
```

### 4. Automated Setup
```bash
# Standard setup
./setup.sh

# Development setup
./setup.sh dev

# Production setup  
./setup.sh prod
```

## 📋 Complete Dependency List

### Core Application Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.104.0 | Web framework |
| `uvicorn` | >=0.23.2 | ASGI server |
| `gunicorn` | >=21.2.0 | Production WSGI server |
| `httpx` | >=0.25.0 | HTTP client for Ollama API |
| `pydantic` | >=2.4.2 | Data validation |
| `pydantic-settings` | >=2.0.3 | Settings management |
| `python-dotenv` | >=1.0.0 | Environment variables |

### Database Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `sqlalchemy` | >=2.0.0 | Database ORM |
| `psycopg2-binary` | >=2.9.0 | PostgreSQL adapter |
| `alembic` | >=1.12.0 | Database migrations |

### Authentication & Security

| Package | Version | Purpose |
|---------|---------|---------|
| `python-jose[cryptography]` | >=3.3.0 | JWT tokens |
| `passlib[bcrypt]` | >=1.7.4 | Password hashing |
| `python-multipart` | >=0.0.6 | Form data parsing |
| `cryptography` | >=41.0.0 | Cryptographic functions |

### Additional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `redis` | >=5.0.0 | Caching & rate limiting |
| `email-validator` | >=2.0.0 | Email validation |
| `python-dateutil` | >=2.8.2 | Date utilities |

### Testing Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.4.0 | Testing framework |
| `pytest-asyncio` | >=0.21.0 | Async testing |
| `pytest-cov` | >=4.1.0 | Coverage reporting |
| `requests` | >=2.31.0 | HTTP testing |

## 🔧 Platform-Specific Installation

### Windows
```bash
# Install Visual C++ Build Tools first for cryptography
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

pip install -r requirements.txt
```

### macOS
```bash
# Install Xcode command line tools
xcode-select --install

pip install -r requirements.txt
```

### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-dev libpq-dev build-essential

pip install -r requirements.txt
```

### Linux (RHEL/CentOS/Fedora)
```bash
# Install system dependencies
sudo yum install -y python3-devel postgresql-devel gcc

pip install -r requirements.txt
```

## 🐳 Docker Installation

### Using Docker Compose
```bash
# Start all services including dependencies
docker-compose up -d

# Install Python dependencies in container
docker-compose exec app pip install -r requirements.txt
```

### Manual Docker Setup
```bash
# Build image
docker build -t ollama-api-auth .

# Run with dependencies
docker run -d --name postgres postgres:15
docker run -d --name redis redis:7-alpine
docker run -p 3000:3000 --link postgres --link redis ollama-api-auth
```

## 🚨 Troubleshooting Dependencies

### Common Issues

**1. PostgreSQL adapter installation fails**
```bash
# Linux
sudo apt-get install libpq-dev python3-dev

# macOS
brew install postgresql

# Windows
# Download and install PostgreSQL from official website
```

**2. Cryptography compilation errors**
```bash
# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install pre-compiled wheel
pip install --only-binary=cryptography cryptography
```

**3. bcrypt compilation errors**
```bash
# Install system dependencies
# Linux
sudo apt-get install build-essential libffi-dev

# macOS
xcode-select --install

# Use pre-compiled wheel
pip install --only-binary=bcrypt bcrypt
```

**4. Redis connection issues**
```bash
# Start Redis with Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally
# Linux
sudo apt-get install redis-server

# macOS
brew install redis
```

### Dependency Verification Script
```python
# verify_deps.py
import sys

required_modules = [
    'fastapi', 'uvicorn', 'sqlalchemy', 'alembic',
    'pydantic', 'httpx', 'jose', 'passlib', 'psycopg2',
    'redis', 'pytest', 'cryptography'
]

missing = []
for module in required_modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError:
        missing.append(module)
        print(f"❌ {module}")

if missing:
    print(f"\n🚨 Missing dependencies: {missing}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\n🎉 All dependencies verified!")
```

## 📊 Dependency Size Analysis

| Category              | Packages         | Approx Size|
|-----------------------|------------------|------------|
| Core FastAPI          | 5 packages       | ~50MB      |
| Database              | 3 packages       | ~30MB      |
| Authentication        | 4 packages       | ~40MB      |
| Testing               | 4 packages       | ~25MB      |
| Development           | 10+ packages     | ~100MB     |
| **Total Production**  | **~16 packages** | **~120MB** |
| **Total Development** | **~26 packages** | **~220MB** |

## 🎯 Minimal Installation

For the absolute minimum installation:
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose[cryptography] passlib[bcrypt]
```

## 🔄 Updating Dependencies

### Check for outdated packages
```bash
pip list --outdated
```

### Update all packages
```bash
pip install --upgrade -r requirements.txt
```

### Update specific package
```bash
pip install --upgrade fastapi
```

### Pin exact versions (production)
```bash
pip freeze > requirements-lock.txt
```

## 🧪 Testing Installation

```bash
# Test basic imports
python -c "import fastapi, sqlalchemy, pydantic; print('✅ Core imports work')"

# Test database connection
python -c "from sqlalchemy import create_engine; print('✅ Database ready')"

# Test authentication
python -c "from jose import jwt; from passlib.context import CryptContext; print('✅ Auth ready')"

# Run the application
python app.py
```

## 📈 Performance Optimization

### Faster installation
```bash
# Use binary wheels when available
pip install --only-binary=all -r requirements.txt

# Use pip cache
pip install --cache-dir ~/.pip/cache -r requirements.txt

# Parallel installation
pip install --upgrade pip
pip install -r requirements.txt --progress-bar off
```

### Reduce installation size
```bash
# Skip development dependencies in production
pip install --no-dev -r requirements-prod.txt

# Remove test packages after installation
pip uninstall pytest pytest-asyncio pytest-cov -y
```