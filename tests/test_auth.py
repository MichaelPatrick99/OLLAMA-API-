"""Tests for authentication functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from auth.services import UserService, APIKeyService
from auth.schemas import UserCreate, APIKeyCreate, RoleEnum
from auth.utils import create_access_token, verify_password


class TestUserAuthentication:
    """Test user authentication functionality."""
    
    def test_user_registration(self, test_client: TestClient, setup_test_db):
        """Test user registration."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123",
            "full_name": "Test User"
        }
        
        response = test_client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
        assert "id" in data
    
    def test_user_registration_duplicate_username(self, test_client: TestClient, setup_test_db):
        """Test user registration with duplicate username."""
        user_data = {
            "username": "duplicate",
            "email": "test1@example.com",
            "password": "TestPass123"
        }
        
        # First registration should succeed
        response1 = test_client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Second registration with same username should fail
        user_data["email"] = "test2@example.com"
        response2 = test_client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    def test_user_login(self, test_client: TestClient, setup_test_db):
        """Test user login."""
        # First register a user
        user_data = {
            "username": "loginuser",
            "email": "login@example.com", 
            "password": "TestPass123"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        # Then try to login
        login_data = {
            "username": "loginuser",
            "password": "TestPass123"
        }
        
        response = test_client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_user_login_invalid_credentials(self, test_client: TestClient, setup_test_db):
        """Test user login with invalid credentials."""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpass"
        }
        
        response = test_client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    def test_get_current_user(self, test_client: TestClient, setup_test_db):
        """Test getting current user information."""
        # Register and login
        user_data = {
            "username": "currentuser",
            "email": "current@example.com",
            "password": "TestPass123"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        login_response = test_client.post("/api/auth/login", data={
            "username": "currentuser",
            "password": "TestPass123"
        })
        token = login_response.json()["access_token"]
        
        # Get current user info
        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "currentuser"
        assert data["email"] == "current@example.com"
    
    def test_update_current_user(self, test_client: TestClient, setup_test_db):
        """Test updating current user information."""
        # Register and login
        user_data = {
            "username": "updateuser",
            "email": "update@example.com",
            "password": "TestPass123"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        login_response = test_client.post("/api/auth/login", data={
            "username": "updateuser", 
            "password": "TestPass123"
        })
        token = login_response.json()["access_token"]
        
        # Update user info
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@example.com"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.put("/api/auth/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"


class TestAPIKeyAuthentication:
    """Test API key authentication functionality."""
    
    def test_create_api_key(self, test_client: TestClient, setup_test_db):
        """Test API key creation."""
        # Register and login user
        user_data = {
            "username": "apikeyuser",
            "email": "apikey@example.com",
            "password": "TestPass123"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        login_response = test_client.post("/api/auth/login", data={
            "username": "apikeyuser",
            "password": "TestPass123"
        })
        token = login_response.json()["access_token"]
        
        # Create API key
        api_key_data = {
            "name": "Test API Key",
            "usage_limit_per_hour": 100,
            "usage_limit_per_day": 1000
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.post("/api/auth/api-keys", json=api_key_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["api_key"]["name"] == "Test API Key"
        assert "secret" in data
        assert data["secret"].startswith("oak_")
    
    def test_list_api_keys(self, test_client: TestClient, setup_test_db):
        """Test listing API keys."""
        # Register user and create API key
        user_data = {
            "username": "listkeys",
            "email": "listkeys@example.com", 
            "password": "TestPass123"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        login_response = test_client.post("/api/auth/login", data={
            "username": "listkeys",
            "password": "TestPass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create an API key
        api_key_data = {"name": "List Test Key"}
        test_client.post("/api/auth/api-keys", json=api_key_data, headers=headers)
        
        # List API keys
        response = test_client.get("/api/auth/api-keys", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "List Test Key"
    
    def test_delete_api_key(self, test_client: TestClient, setup_test_db):
        """Test deleting an API key."""
        # Register user and create API key
        user_data = {
            "username": "deletekey",
            "email": "deletekey@example.com",
            "password": "TestPass123"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        login_response = test_client.post("/api/auth/login", data={
            "username": "deletekey",
            "password": "TestPass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create API key
        api_key_data = {"name": "Delete Test Key"}
        create_response = test_client.post("/api/auth/api-keys", json=api_key_data, headers=headers)
        key_id = create_response.json()["api_key"]["id"]
        
        # Delete API key
        response = test_client.delete(f"/api/auth/api-keys/{key_id}", headers=headers)
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    def test_admin_access_user_list(self, test_client: TestClient, setup_test_db):
        """Test admin access to user list."""
        # Create admin user
        admin_data = {
            "username": "admin",
            "email": "admin@example.com",
            "password": "AdminPass123",
            "role": "admin"
        }
        test_client.post("/api/auth/register", json=admin_data)
        
        # Login as admin
        login_response = test_client.post("/api/auth/login", data={
            "username": "admin",
            "password": "AdminPass123"
        })
        admin_token = login_response.json()["access_token"]
        
        # Access user list (should succeed)
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = test_client.get("/api/auth/users", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_regular_user_denied_user_list(self, test_client: TestClient, setup_test_db):
        """Test regular user denied access to user list."""
        # Create regular user
        user_data = {
            "username": "regularuser",
            "email": "regular@example.com",
            "password": "UserPass123"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        # Login as regular user
        login_response = test_client.post("/api/auth/login", data={
            "username": "regularuser",
            "password": "UserPass123"
        })
        user_token = login_response.json()["access_token"]
        
        # Try to access user list (should fail)
        headers = {"Authorization": f"Bearer {user_token}"}
        response = test_client.get("/api/auth/users", headers=headers)
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"] or "Insufficient permissions" in response.json()["detail"]


class TestPasswordValidation:
    """Test password validation functionality."""
    
    def test_weak_password_rejected(self, test_client: TestClient, setup_test_db):
        """Test that weak passwords are rejected."""
        weak_passwords = [
            "123",  # Too short
            "password",  # No uppercase/numbers
            "PASSWORD",  # No lowercase/numbers
            "Password",  # No numbers
            "12345678"  # No letters
        ]
        
        for i, weak_password in enumerate(weak_passwords):
            user_data = {
                "username": f"weakuser{i}",
                "email": f"weak{i}@example.com",
                "password": weak_password
            }
            
            response = test_client.post("/api/auth/register", json=user_data)
            assert response.status_code == 422  # Validation error
    
    def test_strong_password_accepted(self, test_client: TestClient, setup_test_db):
        """Test that strong passwords are accepted."""
        user_data = {
            "username": "stronguser",
            "email": "strong@example.com",
            "password": "StrongPass123!"
        }
        
        response = test_client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201


class TestAuthenticationUtilities:
    """Test authentication utility functions."""
    
    def test_password_hashing_and_verification(self):
        """Test password hashing and verification."""
        from auth.utils import get_password_hash, verify_password
        
        password = "TestPassword123"
        hashed = get_password_hash(password)
        
        # Verify correct password
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert verify_password("WrongPassword", hashed) is False
    
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        from auth.utils import create_access_token, verify_token
        from datetime import timedelta
        
        data = {"user_id": 1, "username": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(minutes=30))
        
        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["username"] == "testuser"
        assert "exp" in payload
    
    def test_api_key_generation(self):
        """Test API key generation."""
        from auth.utils import generate_api_key, hash_api_key, verify_api_key
        
        key_id, secret = generate_api_key()
        
        # Check format
        assert key_id.startswith("oak_")
        assert len(secret) > 20
        
        # Test hashing and verification
        hashed_secret = hash_api_key(secret)
        assert verify_api_key(secret, hashed_secret) is True
        assert verify_api_key("wrong_secret", hashed_secret) is False


class TestUsageTracking:
    """Test usage tracking functionality."""
    
    def test_usage_stats_endpoint(self, test_client: TestClient, setup_test_db):
        """Test usage statistics endpoint."""
        # Register and login user
        user_data = {
            "username": "usageuser",
            "email": "usage@example.com",
            "password": "TestPass123"
        }
        test_client.post("/api/auth/register", json=user_data)
        
        login_response = test_client.post("/api/auth/login", data={
            "username": "usageuser",
            "password": "TestPass123"
        })
        token = login_response.json()["access_token"]
        
        # Get usage stats
        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.get("/api/auth/usage/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "total_tokens" in data
        assert "requests_by_status" in data


@pytest.fixture
def authenticated_user(test_client: TestClient, setup_test_db):
    """Fixture to create an authenticated user and return token."""
    user_data = {
        "username": "authuser",
        "email": "auth@example.com",
        "password": "TestPass123"
    }
    test_client.post("/api/auth/register", json=user_data)
    
    login_response = test_client.post("/api/auth/login", data={
        "username": "authuser",
        "password": "TestPass123"
    })
    
    return login_response.json()["access_token"]


@pytest.fixture 
def admin_user(test_client: TestClient, setup_test_db):
    """Fixture to create an admin user and return token."""
    admin_data = {
        "username": "testadmin",
        "email": "testadmin@example.com", 
        "password": "AdminPass123",
        "role": "admin"
    }
    test_client.post("/api/auth/register", json=admin_data)
    
    login_response = test_client.post("/api/auth/login", data={
        "username": "testadmin",
        "password": "AdminPass123"
    })
    
    return login_response.json()["access_token"]