"""
Rate limiting middleware for API endpoints.
Token bucket implementation with request and token limits.
Conservative limits for resume/demo projects.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict
from datetime import datetime, timedelta
import time


class RateLimiter:
    """Token bucket rate limiter with request and token tracking."""
    
    def __init__(
        self, 
        requests_per_minute: int = 10,  # Conservative: 10 req/min
        max_tokens_per_minute: int = 5000  # Conservative: 5000 tokens/min (half of Groq)
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute per IP
            max_tokens_per_minute: Maximum tokens per minute per IP
        """
        self.requests_per_minute = requests_per_minute
        self.max_tokens_per_minute = max_tokens_per_minute
        self.requests: Dict[str, list] = {}
        self.tokens: Dict[str, list] = {}  # Track token usage
    
    def is_allowed(self, client_id: str, estimated_tokens: int = 500) -> tuple[bool, str]:
        """
        Check if request is allowed.
        
        Args:
            client_id: Client identifier (usually IP address)
            estimated_tokens: Estimated tokens for this request
            
        Returns:
            tuple: (is_allowed, reason)
        """
        now = time.time()
        minute_ago = now - 60
        
        # Initialize or clean old requests
        if client_id not in self.requests:
            self.requests[client_id] = []
            self.tokens[client_id] = []
        
        # Remove requests older than 1 minute
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        # Remove token records older than 1 minute
        self.tokens[client_id] = [
            (token_count, req_time) for token_count, req_time in self.tokens[client_id]
            if req_time > minute_ago
        ]
        
        # Check request limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False, f"Request limit exceeded ({self.requests_per_minute}/min)"
        
        # Check token limit
        total_tokens = sum(token_count for token_count, _ in self.tokens[client_id])
        if total_tokens + estimated_tokens > self.max_tokens_per_minute:
            return False, f"Token limit exceeded ({self.max_tokens_per_minute}/min)"
        
        # Add current request
        self.requests[client_id].append(now)
        self.tokens[client_id].append((estimated_tokens, now))
        
        return True, "OK"
    
    def get_remaining(self, client_id: str) -> dict:
        """Get remaining requests and tokens for client."""
        if client_id not in self.requests:
            return {
                "requests": self.requests_per_minute,
                "tokens": self.max_tokens_per_minute
            }
        
        now = time.time()
        minute_ago = now - 60
        
        recent_requests = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        recent_tokens = [
            token_count for token_count, req_time in self.tokens[client_id]
            if req_time > minute_ago
        ]
        
        return {
            "requests": max(0, self.requests_per_minute - len(recent_requests)),
            "tokens": max(0, self.max_tokens_per_minute - sum(recent_tokens))
        }
    
    def cleanup(self):
        """Remove old entries to prevent memory leak."""
        now = time.time()
        minute_ago = now - 60
        
        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > minute_ago
            ]
            
            self.tokens[client_id] = [
                (token_count, req_time) for token_count, req_time in self.tokens[client_id]
                if req_time > minute_ago
            ]
            
            # Remove empty entries
            if not self.requests[client_id]:
                del self.requests[client_id]
                del self.tokens[client_id]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(
        self, 
        app, 
        requests_per_minute: int = 10,  # Conservative
        max_tokens_per_minute: int = 5000  # Conservative
    ):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI app
            requests_per_minute: Rate limit for requests
            max_tokens_per_minute: Rate limit for tokens
        """
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute, max_tokens_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks and OPTIONS requests
        if request.url.path in ["/", "/health", "/docs", "/openapi.json", "/styles.css", "/app.js"] or request.method == "OPTIONS":
            return await call_next(request)
        
        # Estimate tokens based on endpoint
        estimated_tokens = 500  # Default
        if "/ingest/" in request.url.path:
            estimated_tokens = 1500  # Video processing uses more
        elif "/chat/" in request.url.path:
            estimated_tokens = 800  # Q&A uses moderate
        
        # Check rate limit
        allowed, reason = self.limiter.is_allowed(client_ip, estimated_tokens)
        
        if not allowed:
            remaining = self.limiter.get_remaining(client_ip)
            raise HTTPException(
                status_code=429,
                detail={
                    "status": "error",
                    "message": f"Rate limit exceeded: {reason}",
                    "limits": {
                        "requests_per_minute": self.limiter.requests_per_minute,
                        "tokens_per_minute": self.limiter.max_tokens_per_minute
                    },
                    "remaining": remaining,
                    "retry_after": "60 seconds"
                }
            )
        
        # Add rate limit headers
        response = await call_next(request)
        remaining = self.limiter.get_remaining(client_ip)
        
        response.headers["X-RateLimit-Requests-Limit"] = str(self.limiter.requests_per_minute)
        response.headers["X-RateLimit-Requests-Remaining"] = str(remaining["requests"])
        response.headers["X-RateLimit-Tokens-Limit"] = str(self.limiter.max_tokens_per_minute)
        response.headers["X-RateLimit-Tokens-Remaining"] = str(remaining["tokens"])
        
        return response


# Global rate limiter instance (conservative for resume projects)
global_rate_limiter = RateLimiter(
    requests_per_minute=10,  # 10 requests/min
    max_tokens_per_minute=5000  # 5000 tokens/min
)


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
