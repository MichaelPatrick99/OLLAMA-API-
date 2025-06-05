"""Helper functions for the application."""

import json
from typing import Dict, Any, Optional
from fastapi import HTTPException


def format_error_response(status_code: int, detail: str) -> Dict[str, Any]:
    """Format an error response.
    
    Args:
        status_code: HTTP status code
        detail: Error details
        
    Returns:
        Formatted error response
    """
    return {"status_code": status_code, "detail": detail}


def parse_json_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a JSON line.
    
    Args:
        line: JSON line to parse
        
    Returns:
        Parsed JSON or None if invalid
    """
    if not line.strip():
        return None
    
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def extract_response_from_data(data: Dict[str, Any]) -> Optional[str]:
    """Extract response from data.
    
    Args:
        data: Data to extract from
        
    Returns:
        Extracted response or None if not found
    """
    if "response" in data:
        return data["response"]
    
    if "message" in data and isinstance(data["message"], dict) and "content" in data["message"]:
        return data["message"]["content"]
    
    return None