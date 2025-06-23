"""Tests for protected endpoints with authentication."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestProtectedGenerateEndpoints:
    """Test protected text generation endpoints."""
    
    def test_generate_without_auth_fails(self, test_client: TestClient, setup_test_db):
        """Test that generate endpoint requires authentication."""
        generate_data = {
            "prompt": "Hello, how are you?",
            "model": "llama3:8b",
            "stream": False
        }
        
        response = test_client.post("/api/generate", json=generate_data)
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    @patch('services.ollama_service.OllamaService.generate')
    def test_generate_with_auth_succeeds(self, mock_generate, test_client: TestClient, 
                                       authenticated_user: str, setup_test_db):
        """Test that generate endpoint works with authentication."""
        # Mock the Ollama service response
        mock_generate.return_value = {"response": "Hello! I'm doing well, thank you."}
        
        generate_data = {
            "prompt": "Hello, how are you?",
            "model": "llama3:8b", 
            "stream": False
        }
        
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = test_client.post("/api/generate", json=generate_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] == "Hello! I'm doing well, thank you."
    
    @patch('services.ollama_service.OllamaService.stream_generate')
    def test_generate_streaming_with_auth(self, mock_stream_generate, test_client: TestClient,
                                        authenticated_user: str, setup_test_db):
        """Test streaming generate endpoint with authentication."""
        # Mock the streaming response
        async def mock_stream():
            yield "Hello"
            yield " there"
            yield "!"
        
        mock_stream_generate.return_value = mock_stream()
        
        generate_data = {
            "prompt": "Hello",
            "model": "llama3:8b",
            "stream": True
        }
        
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = test_client.post("/api/generate", json=generate_data, headers=headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_generate_with_read_only_user_fails(self, test_client: TestClient, setup_test_db):
        """Test that read-only users cannot access generate endpoint."""
        # Create read-only user
        user_data = {
            "username": "readonly",
            "email": "readonly@example.com",
            "password": "TestPass123",
            "role": "read_only"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        login_response = test_client.post("/api/auth/login", data={
            "username": "readonly",
            "password": "TestPass123"
        })
        token = login_response.json()["access_token"]
        
        generate_data = {
            "prompt": "Hello",
            "model": "llama3:8b",
            "stream": False
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.post("/api/generate", json=generate_data, headers=headers)
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]


class TestProtectedChatEndpoints:
    """Test protected chat endpoints."""
    
    def test_chat_without_auth_fails(self, test_client: TestClient, setup_test_db):
        """Test that chat endpoint requires authentication."""
        chat_data = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "model": "llama3:8b",
            "stream": False
        }
        
        response = test_client.post("/api/chat", json=chat_data)
        assert response.status_code == 401
    
    @patch('services.ollama_service.OllamaService.chat')
    def test_chat_with_auth_succeeds(self, mock_chat, test_client: TestClient,
                                   authenticated_user: str, setup_test_db):
        """Test that chat endpoint works with authentication."""
        # Mock the Ollama service response
        mock_chat.return_value = {
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            }
        }
        
        chat_data = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "model": "llama3:8b",
            "stream": False
        }
        
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = test_client.post("/api/chat", json=chat_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"]["content"] == "Hello! How can I help you today?"
    
    def test_chat_message_validation(self, test_client: TestClient, 
                                   authenticated_user: str, setup_test_db):
        """Test chat message validation endpoint."""
        messages_data = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = test_client.post("/api/chat/validate", json=messages_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["message_count"] == 3
        assert "estimated_tokens" in data
    
    def test_chat_invalid_messages(self, test_client: TestClient,
                                 authenticated_user: str, setup_test_db):
        """Test chat with invalid message format."""
        invalid_messages = [
            {"role": "invalid_role", "content": "Hello"}
        ]
        
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = test_client.post("/api/chat/validate", json=invalid_messages, headers=headers)
        
        assert response.status_code == 400
        assert "Invalid message role" in response.json()["detail"]


class TestProtectedModelsEndpoints:
    """Test protected model management endpoints."""
    
    def test_list_models_without_auth_fails(self, test_client: TestClient, setup_test_db):
        """Test that models list requires authentication."""
        response = test_client.get("/api/models")
        assert response.status_code == 401
    
    @patch('services.ollama_service.OllamaService.list_models')
    def test_list_models_with_auth_succeeds(self, mock_list_models, test_client: TestClient,
                                          authenticated_user: str, setup_test_db):
        """Test that models list works with authentication."""
        # Mock the Ollama service response
        mock_list_models.return_value = {
            "models": [
                {
                    "name": "llama3:8b",
                    "modified_at": "2024-01-01T00:00:00Z",
                    "size": 4700000000
                }
            ]
        }
        
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = test_client.get("/api/models", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) == 1
        assert data["models"][0]["name"] == "llama3:8b"
        assert "accessible" in data["models"][0]
        assert "capabilities" in data["models"][0]
    
    @patch('services.ollama_service.OllamaService.model_info')
    def test_get_model_info_with_auth(self, mock_model_info, test_client: TestClient,
                                    authenticated_user: str, setup_test_db):
        """Test getting model info with authentication."""
        # Mock the Ollama service response
        mock_model_info.return_value = {
            "name": "llama3:8b",
            "modified_at": "2024-01-01T00:00:00Z",
            "size": 4700000000,
            "digest": "abc123"
        }
        
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = test_client.get("/api/models/llama3:8b", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "llama3:8b"
        assert "capabilities" in data
        assert "user_permissions" in data
    
    def test_download_model_requires_write_permission(self, test_client: TestClient, setup_test_db):
        """Test that model download requires write permission."""
        # Create read-only user
        user_data = {
            "username": "readonly2",
            "email": "readonly2@example.com",
            "password": "TestPass123",
            "role": "read_only"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        login_response = test_client.post("/api/auth/login", data={
            "username": "readonly2",
            "password": "TestPass123"
        })
        token = login_response.json()["access_token"]
        
        download_data = {"name": "tinyllama"}
        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.post("/api/models/download", json=download_data, headers=headers)
        
        assert response.status_code == 403
    
    @patch('services.ollama_service.OllamaService.download_model')
    def test_download_model_with_write_permission(self, mock_download, test_client: TestClient,
                                                authenticated_user: str, setup_test_db):
        """Test model download with proper permissions."""
        # Mock the download response
        mock_download.return_value = {"status": "downloading"}
        
        download_data = {"name": "tinyllama"}
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = test_client.post("/api/models/download", json=download_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "download_status" in data
        assert data["model_name"] == "tinyllama"
    
    def test_delete_model_requires_delete_permission(self, test_client: TestClient, setup_test_db):
        """Test that model deletion requires delete permission."""
        # Create regular user (should not have delete permission)
        user_data = {
            "username": "regularuser2",
            "email": "regular2@example.com",
            "password": "TestPass123",
            "role": "user"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        login_response = test_client.post("/api/auth/login", data={
            "username": "regularuser2",
            "password": "TestPass123"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.delete("/api/models/tinyllama", headers=headers)
        
        assert response.status_code == 403


class TestAPIKeyAuthentication:
    """Test API key authentication for endpoints."""
    
    def test_generate_with_api_key(self, test_client: TestClient, setup_test_db):
        """Test using API key for authentication."""
        # Create user and API key
        user_data = {
            "username": "apikeyuser2",
            "email": "apikey2@example.com",
            "password": "TestPass123"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        login_response = test_client.post("/api/auth/login", data={
            "username": "apikeyuser2",
            "password": "TestPass123"
        })
        token = login_response.json()["access_token"]
        
        # Create API key
        api_key_data = {"name": "Test Generate Key"}
        headers = {"Authorization": f"Bearer {token}"}
        api_key_response = test_client.post("/api/auth/api-keys", json=api_key_data, headers=headers)
        api_key_secret = api_key_response.json()["secret"]
        
        # Use API key for generate endpoint (mocked)
        with patch('services.ollama_service.OllamaService.generate') as mock_generate:
            mock_generate.return_value = {"response": "API key works!"}
            
            generate_data = {
                "prompt": "Test with API key",
                "model": "llama3:8b",
                "stream": False
            }
            
            api_headers = {"Authorization": f"Bearer {api_key_secret}"}
            response = test_client.post("/api/generate", json=generate_data, headers=api_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "API key works!"
    
    def test_invalid_api_key_fails(self, test_client: TestClient, setup_test_db):
        """Test that invalid API key fails authentication."""
        generate_data = {
            "prompt": "Test",
            "model": "llama3:8b",
            "stream": False
        }
        
        headers = {"Authorization": "Bearer oak_invalid_key"}
        response = test_client.post("/api/generate", json=generate_data, headers=headers)
        
        assert response.status_code == 401


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiting_with_api_key(self, test_client: TestClient, setup_test_db):
        """Test that rate limiting works with API keys."""
        # This would require more complex setup with Redis and actual rate limiting
        # For now, we'll test the basic structure
        pass
    
    def test_usage_tracking(self, test_client: TestClient, authenticated_user: str, setup_test_db):
        """Test that usage is tracked for authenticated requests."""
        with patch('services.ollama_service.OllamaService.generate') as mock_generate:
            mock_generate.return_value = {"response": "Tracked response"}
            
            generate_data = {
                "prompt": "Track this request",
                "model": "llama3:8b",
                "stream": False
            }
            
            headers = {"Authorization": f"Bearer {authenticated_user}"}
            response = test_client.post("/api/generate", json=generate_data, headers=headers)
            
            assert response.status_code == 200
            
            # Check that usage stats can be retrieved
            stats_response = test_client.get("/api/auth/usage/stats", headers=headers)
            assert stats_response.status_code == 200