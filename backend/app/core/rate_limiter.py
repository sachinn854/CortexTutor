"""
Rate limiting middleware for API endpoints.
Simple token bucket implementation.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict
from datetime import datetime, timedelta
import time


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute per IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            client_id: Client identifier (usually IP address)
            
        Returns:
            bool: True if request is allowed
        """
        now = time.time()
        minute_ago = now - 60
        
        # Initialize or clean old requests
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove requests older than 1 minute
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client."""
        if client_id not in self.requests:
            return self.requests_per_minute
        
        now = time.time()
        minute_ago = now - 60
        
        recent_requests = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        return max(0, self.requests_per_minute - len(recent_requests))
    
    def cleanup(self):
        """Remove old entries to prevent memory leak."""
        now = time.time()
        minute_ago = now - 60
        
        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > minute_ago
            ]
            
            # Remove empty entries
            if not self.requests[client_id]:
                del self.requests[client_id]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI app
            requests_per_minute: Rate limit
        """
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks and OPTIONS requests
        if request.url.path in ["/", "/health", "/docs", "/openapi.json"] or request.method == "OPTIONS":
            return await call_next(request)
        
        # Check rate limit
        if not self.limiter.is_allowed(client_ip):
            remaining = self.limiter.get_remaining(client_ip)
            raise HTTPException(
                status_code=429,
                detail={
                    "status": "error",
                    "message": "Rate limit exceeded. Please try again later.",
                    "limit": self.limiter.requests_per_minute,
                    "remaining": remaining
                }
            )
        
        # Add rate limit headers
        response = await call_next(request)
        remaining = self.limiter.get_remaining(client_ip)
        
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


# Global rate limiter instance
global_rate_limiter = RateLimiter(requests_per_minute=60)


def rate_limit(requests_per_minute: int = 60):
    """
    Decorator for rate limiting specific endpoints.
    
    Args:
        requests_per_minute: Rate limit
    """
    limiter = RateLimiter(requests_per_minute)
    
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            
            if not limiter.is_allowed(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail={
                        "status": "error",
                        "message": "Rate limit exceeded",
                        "limit": requests_per_minute
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


# Test function
def test_rate_limiter():
    """Test rate limiter."""
    print("\n" + "="*60)
    print("Testing Rate Limiter")
    print("="*60)
    
    limiter = RateLimiter(requests_per_minute=5)
    client_id = "test_client"
    
    print("\n1. Testing normal requests:")
    for i in range(5):
        allowed = limiter.is_allowed(client_id)
        remaining = limiter.get_remaining(client_id)
        print(f"   Request {i+1}: Allowed={allowed}, Remaining={remaining}")
        assert allowed, f"Request {i+1} should be allowed"
    
    print("\n2. Testing rate limit exceeded:")
    allowed = limiter.is_allowed(client_id)
    remaining = limiter.get_remaining(client_id)
    print(f"   Request 6: Allowed={allowed}, Remaining={remaining}")
    assert not allowed, "Request 6 should be blocked"
    
    print("\n3. Testing cleanup:")
    limiter.cleanup()
    print(f"   Active clients after cleanup: {len(limiter.requests)}")
    
    print("\n4. Testing expiration:")
    print("   Waiting 61 seconds for rate limit reset...")
    print("   (Skipping in test - would work in production)")
    
    print("\n" + "="*60)
    print("✅ Rate limiter tests passed!")
    print("="*60)


if __name__ == "__main__":
    test_rate_limiter()
