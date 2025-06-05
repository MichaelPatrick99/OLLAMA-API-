"""Test suite for the Ollama API wrapper."""

import unittest
import asyncio
import requests
import json
import os
from typing import Dict, Any, List

# Configuration for tests
BASE_URL = os.getenv("TEST_API_URL", "http://138.2.171.35:5000")
TEST_MODEL = os.getenv("TEST_MODEL", "llama3:8b")  # Use a small model for testing


class OllamaApiTest(unittest.TestCase):
    """Test cases for the Ollama API wrapper."""

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = requests.get(f"{BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("message", data)

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = requests.get(f"{BASE_URL}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("message", data)


class ModelManagementTest(unittest.TestCase):
    """Test cases for model management endpoints."""

    def test_list_models(self):
        """Test listing available models."""
        response = requests.get(f"{BASE_URL}/api/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("models", data)
        self.assertIsInstance(data["models"], list)
        
        # If models exist, check their structure
        if data["models"]:
            model = data["models"][0]
            self.assertIn("name", model)

    def test_get_model_info(self):
        """Test getting model information."""
        # First check if the model exists
        models_response = requests.get(f"{BASE_URL}/api/models")
        models_data = models_response.json()
        
        if not models_data["models"]:
            self.skipTest("No models available for testing")
            
        # Get the first available model
        model_name = models_data["models"][0]["name"]
        
        # Test getting model info
        response = requests.get(f"{BASE_URL}/api/models/{model_name}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("name", data)
        self.assertEqual(data["name"], model_name)

    def test_download_model(self):
        """Test downloading a model."""
        # This test is marked as skip by default as it can take a long time
        # and consume significant resources
        self.skipTest("Skipping model download test to avoid long-running operations")
        
        response = requests.post(
            f"{BASE_URL}/api/models/download",
            json={"name": "tinyllama"}
        )
        
        # Either the model is already downloaded or being downloaded
        self.assertIn(response.status_code, [200, 202])
        data = response.json()
        self.assertIn("message", data)


class TextGenerationTest(unittest.TestCase):
    """Test cases for text generation endpoints."""

    def test_generate_non_streaming(self):
        """Test non-streaming text generation."""
        # First check if the model exists
        models_response = requests.get(f"{BASE_URL}/api/models")
        models_data = models_response.json()
        
        if not models_data["models"]:
            self.skipTest("No models available for testing")
        
        # Find a suitable model
        model_name = TEST_MODEL
        model_exists = any(model["name"] == model_name for model in models_data["models"])
        
        if not model_exists:
            # Use the first available model
            model_name = models_data["models"][0]["name"]
        
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json={
                "prompt": "Hello, how are you?",
                "model": model_name,
                "stream": False
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertIsInstance(data["response"], str)
        self.assertTrue(len(data["response"]) > 0)

    def test_generate_streaming(self):
        """Test streaming text generation."""
        # First check if the model exists
        models_response = requests.get(f"{BASE_URL}/api/models")
        models_data = models_response.json()
        
        if not models_data["models"]:
            self.skipTest("No models available for testing")
        
        # Find a suitable model
        model_name = TEST_MODEL
        model_exists = any(model["name"] == model_name for model in models_data["models"])
        
        if not model_exists:
            # Use the first available model
            model_name = models_data["models"][0]["name"]
        
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json={
                "prompt": "Hello, how are you?",
                "model": model_name,
                "stream": True
            },
            stream=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that we receive some content
        content_received = False
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                content_received = True
                break
                
        self.assertTrue(content_received, "No content received from streaming endpoint")


class ChatCompletionTest(unittest.TestCase):
    """Test cases for chat completion endpoints."""

    def test_chat_non_streaming(self):
        """Test non-streaming chat completion."""
        # First check if the model exists
        models_response = requests.get(f"{BASE_URL}/api/models")
        models_data = models_response.json()
        
        if not models_data["models"]:
            self.skipTest("No models available for testing")
        
        # Find a suitable model
        model_name = TEST_MODEL
        model_exists = any(model["name"] == model_name for model in models_data["models"])
        
        if not model_exists:
            # Use the first available model
            model_name = models_data["models"][0]["name"]
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "model": model_name,
                "stream": False
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("content", data["message"])
        self.assertTrue(len(data["message"]["content"]) > 0)

    def test_chat_streaming(self):
        """Test streaming chat completion."""
        # First check if the model exists
        models_response = requests.get(f"{BASE_URL}/api/models")
        models_data = models_response.json()
        
        if not models_data["models"]:
            self.skipTest("No models available for testing")
        
        # Find a suitable model
        model_name = TEST_MODEL
        model_exists = any(model["name"] == model_name for model in models_data["models"])
        
        if not model_exists:
            # Use the first available model
            model_name = models_data["models"][0]["name"]
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "model": model_name,
                "stream": True
            },
            stream=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that we receive some content
        content_received = False
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                content_received = True
                break
                
        self.assertTrue(content_received, "No content received from streaming endpoint")


class ErrorHandlingTest(unittest.TestCase):
    """Test cases for error handling."""

    def test_invalid_model(self):
        """Test requesting an invalid model."""
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json={
                "prompt": "Hello, how are you?",
                "model": "non_existent_model",
                "stream": False
            }
        )
        
        # Should return an error status code
        self.assertGreaterEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("status_code", data)

    def test_invalid_endpoint(self):
        """Test accessing an invalid endpoint."""
        response = requests.get(f"{BASE_URL}/api/nonexistent")
        self.assertEqual(response.status_code, 404)


def run_async_tests():
    """Run async tests using asyncio."""
    # This function can be used to run async tests if needed
    pass


if __name__ == "__main__":
    # Run the tests
    unittest.main()



