# ADDED FOR CRYPTOSATX ENHANCEMENT
"""
API Key Authentication Middleware
Protects sensitive endpoints without breaking existing public endpoints
"""
import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

# API Key header configuration
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Validate API key from header
    
    Usage in routes:
        @router.get("/protected")
        async def protected_endpoint(api_key: str = Depends(get_api_key)):
            ...
    """
    # Get valid API keys from environment (comma-separated for multiple keys)
    valid_keys = os.getenv("API_KEYS", "").split(",")
    valid_keys = [key.strip() for key in valid_keys if key.strip()]
    
    # If no API keys configured, allow access (backward compatibility)
    if not valid_keys:
        return "public"
    
    # Check if provided key is valid
    if not api_key or api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


async def get_optional_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    Optional API key validation - doesn't raise error if missing
    Useful for endpoints that have both free and premium features
    """
    valid_keys = os.getenv("API_KEYS", "").split(",")
    valid_keys = [key.strip() for key in valid_keys if key.strip()]
    
    if not valid_keys:
        return None
    
    if api_key and api_key in valid_keys:
        return api_key
    
    return None


def is_authenticated(api_key: Optional[str]) -> bool:
    """Helper to check if request is authenticated"""
    return api_key is not None and api_key != "public"
