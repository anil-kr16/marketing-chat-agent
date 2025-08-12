"""
Authentication utilities for the Marketing Agent API.

This module handles API key validation and rate limiting.
For production use, consider implementing JWT tokens, OAuth2,
or integration with external identity providers.
"""

import time
from typing import Optional, Dict
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.utils.config import get_api_config
from app.utils.logging import setup_logging


class APIKeyAuth:
    """
    Simple API key authentication handler.
    
    In production, consider:
    - Database-backed API key storage
    - Key rotation and expiration
    - User management and permissions
    - Rate limiting per key
    """
    
    def __init__(self):
        """Initialize the API key authenticator."""
        self.config = get_api_config()
        self.logger = setup_logging()
        
        # Simple rate limiting storage (in production, use Redis)
        self.rate_limit_storage: Dict[str, list] = {}

    def validate_api_key(self, request: Request) -> str:
        """
        Validate API key from request headers.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Validated API key
            
        Raises:
            HTTPException: If API key is invalid or missing
        """
        # Get API key from header
        api_key = request.headers.get(self.config.api_key_header)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Missing {self.config.api_key_header} header",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        # Validate against configured key(s)
        # In production, check against database
        if api_key != self.config.default_api_key:
            self.logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        return api_key

    def check_rate_limit(self, api_key: str, client_ip: str) -> bool:
        """
        Check if request is within rate limits.
        
        Args:
            api_key: The API key making the request
            client_ip: Client IP address
            
        Returns:
            True if within limits, False if rate limited
        """
        # Use API key + IP as rate limit key
        rate_key = f"{api_key}:{client_ip}"
        current_time = time.time()
        
        # Get or create request history for this key
        if rate_key not in self.rate_limit_storage:
            self.rate_limit_storage[rate_key] = []
        
        request_times = self.rate_limit_storage[rate_key]
        
        # Remove requests older than 1 minute
        request_times[:] = [req_time for req_time in request_times if current_time - req_time < 60]
        
        # Check if within limit
        if len(request_times) >= self.config.rate_limit_per_minute:
            return False
        
        # Add current request
        request_times.append(current_time)
        return True

    async def authenticate_request(self, request: Request) -> str:
        """
        Full authentication check including API key and rate limiting.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Validated API key
            
        Raises:
            HTTPException: If authentication fails
        """
        # Validate API key
        api_key = self.validate_api_key(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limits
        if not self.check_rate_limit(api_key, client_ip):
            self.logger.warning(f"Rate limit exceeded for {api_key[:8]}... from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.config.rate_limit_per_minute} requests per minute.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.config.rate_limit_per_minute),
                    "X-RateLimit-Reset": str(int(time.time()) + 60)
                }
            )
        
        return api_key


class BearerTokenAuth(HTTPBearer):
    """
    Bearer token authentication (for future JWT implementation).
    
    Currently not used but provided as template for JWT tokens.
    """
    
    def __init__(self):
        super().__init__(auto_error=False)
        self.logger = setup_logging()

    async def __call__(self, request: Request) -> Optional[str]:
        """
        Validate bearer token.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Token if valid, None otherwise
        """
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(request)
        
        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
            
            # Validate token (implement JWT validation here)
            token = credentials.credentials
            
            # For now, just return the token
            # In production, validate JWT signature and claims
            return token
        
        return None


# Global authentication instances
api_key_auth = APIKeyAuth()
bearer_auth = BearerTokenAuth()


async def get_current_api_key(request: Request) -> str:
    """
    Dependency for protecting endpoints with API key authentication.
    
    Usage:
        @app.get("/protected")
        async def protected_endpoint(api_key: str = Depends(get_current_api_key)):
            return {"message": "Access granted"}
    """
    return await api_key_auth.authenticate_request(request)


def create_api_key_header_dependency():
    """
    Create a dependency that extracts API key from custom header.
    
    Returns:
        FastAPI dependency function
    """
    config = get_api_config()
    
    async def get_api_key_header(request: Request) -> str:
        return await api_key_auth.authenticate_request(request)
    
    return get_api_key_header


def generate_api_key(user_id: Optional[str] = None, prefix: str = "mktg") -> str:
    """
    Generate a new API key.
    
    Args:
        user_id: Optional user identifier
        prefix: Key prefix for identification
        
    Returns:
        Generated API key
    """
    import secrets
    import string
    
    # Generate random string
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    # Create key with prefix
    api_key = f"{prefix}_{random_part}"
    
    return api_key
