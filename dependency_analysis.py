"""
Dependency Analysis for Ollama API Wrapper with Authentication
===========================================================

This script analyzes all imports in our codebase to ensure 
all dependencies are included in requirements.txt
"""

import ast
import os
from pathlib import Path

def extract_imports_from_file(file_path):
    """Extract all imports from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read())
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
        
        return imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def analyze_project_dependencies():
    """Analyze all Python files in the project for dependencies."""
    project_root = Path(".")
    python_files = []
    
    # Find all Python files
    for pattern in ["**/*.py"]:
        python_files.extend(project_root.glob(pattern))
    
    all_imports = set()
    
    for file_path in python_files:
        if "venv" in str(file_path) or "__pycache__" in str(file_path):
            continue
        
        imports = extract_imports_from_file(file_path)
        all_imports.update(imports)
    
    return sorted(all_imports)

# Standard library modules (don't need to be installed)
STANDARD_LIBRARY = {
    'os', 'sys', 'json', 'time', 'datetime', 'typing', 'pathlib',
    'asyncio', 'contextlib', 'enum', 'secrets', 'hashlib', 'uuid',
    'logging', 'collections', 'functools', 'itertools', 'operator',
    'math', 'random', 're', 'string', 'warnings', 'weakref',
}

# Mapping of import names to pip package names
IMPORT_TO_PACKAGE = {
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'gunicorn': 'gunicorn',
    'pydantic': 'pydantic',
    'pydantic_settings': 'pydantic-settings',
    'sqlalchemy': 'sqlalchemy',
    'alembic': 'alembic',
    'psycopg2': 'psycopg2-binary',
    'httpx': 'httpx',
    'jose': 'python-jose[cryptography]',
    'passlib': 'passlib[bcrypt]',
    'redis': 'redis',
    'pytest': 'pytest',
    'requests': 'requests',
    'dotenv': 'python-dotenv',
    'email_validator': 'email-validator',
    'dateutil': 'python-dateutil',
    'cryptography': 'cryptography',
    'starlette': 'fastapi',  # Included with FastAPI
}

def main():
    """Main analysis function."""
    print("🔍 Analyzing project dependencies...")
    print("=" * 50)
    
    imports = analyze_project_dependencies()
    
    # Filter out standard library imports
    third_party_imports = [imp for imp in imports if imp not in STANDARD_LIBRARY]
    
    print("📦 Third-party imports found:")
    for imp in third_party_imports:
        package = IMPORT_TO_PACKAGE.get(imp, f"{imp} (⚠️  UNKNOWN PACKAGE)")
        print(f"   {imp} -> {package}")
    
    print("\n🎯 Required packages (unique):")
    required_packages = set()
    for imp in third_party_imports:
        if imp in IMPORT_TO_PACKAGE:
            required_packages.add(IMPORT_TO_PACKAGE[imp])
        else:
            required_packages.add(f"{imp}  # ⚠️  VERIFY THIS PACKAGE")
    
    for package in sorted(required_packages):
        print(f"   {package}")
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()


# Expected dependencies based on our codebase:
EXPECTED_CORE_DEPENDENCIES = [
    "fastapi>=0.104.0",
    "uvicorn>=0.23.2", 
    "gunicorn>=21.2.0",
    "httpx>=0.25.0",
    "pydantic>=2.4.2",
    "pydantic-settings>=2.0.3",
    "python-dotenv>=1.0.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.0",
    "alembic>=1.12.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "redis>=5.0.0",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "requests>=2.31.0",
    "email-validator>=2.0.0",
    "python-dateutil>=2.8.2",
    "cryptography>=41.0.0"
]

print("\n📋 Expected core dependencies:")
for dep in EXPECTED_CORE_DEPENDENCIES:
    print(f"   {dep}")