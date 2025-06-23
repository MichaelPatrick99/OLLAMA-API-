#!/bin/bash

# Ollama API Wrapper with Authentication - Quick Setup Script
# This script helps you get the application running quickly

set -e  # Exit on any error

echo "🚀 Ollama API Wrapper with Authentication - Quick Setup"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if PostgreSQL is available
if ! command -v psql &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ PostgreSQL or Docker is required"
    echo "   Please install PostgreSQL locally or Docker for containerized setup"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip

# Check which requirements file to use
if [ "$1" = "dev" ]; then
    echo "   Installing development dependencies..."
    pip install -r requirements-dev.txt
elif [ "$1" = "prod" ]; then
    echo "   Installing production dependencies..."
    pip install -r requirements-prod.txt
else
    echo "   Installing standard dependencies..."
    pip install -r requirements.txt
fi

# Verify critical dependencies
echo "🔍 Verifying critical dependencies..."
python3 -c "
import sys
critical_imports = [
    'fastapi', 'uvicorn', 'sqlalchemy', 'alembic', 
    'pydantic', 'httpx', 'jose', 'passlib', 'psycopg2'
]

missing = []
for module in critical_imports:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    print(f'❌ Missing critical dependencies: {missing}')
    sys.exit(1)
else:
    print('✅ All critical dependencies verified')
"

# Setup environment file
if [ ! -f .env ]; then
    echo "⚙️  Creating environment configuration..."
    cp .env.example .env
    
    # Generate a secure secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env with generated secret key
    if command -v sed &> /dev/null; then
        sed -i.bak "s/your_super_secret_key_here_generate_a_new_one/$SECRET_KEY/" .env
        rm .env.bak 2>/dev/null || true
    else
        echo "Please manually update SECRET_KEY in .env file"
    fi
    
    echo "📝 Environment file created at .env"
    echo "   Please review and update the settings as needed"
else
    echo "✅ Environment file already exists"
fi

# Setup database
echo "🗄️  Setting up database..."

# Check if Docker is available and docker-compose.yml exists
if command -v docker &> /dev/null && [ -f docker-compose.yml ]; then
    echo "🐳 Starting PostgreSQL and Redis with Docker..."
    docker-compose up -d postgres redis
    
    echo "⏳ Waiting for database to be ready..."
    sleep 10
    
    # Check if database is responding
    until docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; do
        echo "   Waiting for PostgreSQL..."
        sleep 2
    done
    
    echo "✅ Database is ready"
else
    echo "📝 Docker not available or docker-compose.yml not found"
    echo "   Please ensure PostgreSQL is running manually"
    echo "   Database: ollama_api"
    echo "   Default connection: postgresql://postgres:password@localhost:5432/ollama_api"
fi

# Setup database migrations
echo "🔄 Setting up database migrations..."

# Initialize Alembic if not already done
if [ ! -d "migrations" ]; then
    echo "   Initializing Alembic..."
    alembic init migrations
    
    # Update alembic.ini with our configuration
    if [ -f alembic.ini ]; then
        cp alembic.ini alembic.ini.bak
    fi
fi

# Create initial migration
echo "   Creating initial migration..."
alembic revision --autogenerate -m "Initial authentication tables" || echo "Migration may already exist"

# Apply migrations
echo "   Applying migrations..."
alembic upgrade head

echo "✅ Database setup completed"

# Create admin user
echo "👤 The application will create a default admin user on first startup"
echo "   Username: admin (from .env ADMIN_USERNAME)"
echo "   Password: Check ADMIN_PASSWORD in .env file"
echo "   ⚠️  Please change the default password after first login!"

# Final instructions
echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "   source venv/bin/activate  # Activate virtual environment"
echo "   python app.py             # Start development server"
echo ""
echo "📖 Or check the README.md for detailed instructions"
echo ""
echo "🌐 Once running, visit:"
echo "   • Application: http://localhost:3000"
echo "   • API Docs: http://localhost:3000/docs"
echo "   • Health Check: http://localhost:3000/health"
echo ""
echo "🔐 Authentication endpoints:"
echo "   • Register: POST /api/auth/register"
echo "   • Login: POST /api/auth/login"
echo "   • API Keys: POST /api/auth/api-keys"
echo ""
echo "⚠️  Important next steps:"
echo "   1. Review and update .env configuration"
echo "   2. Change default admin password"
echo "   3. Configure your Ollama API endpoint"
echo "   4. Set up proper production settings if deploying"
echo ""
echo "📚 For detailed documentation, visit http://localhost:3000/docs after starting the app"