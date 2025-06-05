# Ollama API Wrapper

A FastAPI-based wrapper for the Ollama API with enhanced features, better structure, and comprehensive documentation.

## Features

- Text generation with streaming and non-streaming options
- Chat completion with streaming and non-streaming options
- Model management (list, download, info, delete)
- Proper error handling and response formatting
- Comprehensive API documentation with Swagger UI
- CORS support for frontend integration
- Request timing middleware
- Configuration via environment variables

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- httpx
- pydantic
- pydantic-settings

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install fastapi uvicorn httpx pydantic pydantic-settings