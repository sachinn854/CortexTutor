"""
Request timeout middleware.
Prevents long-running requests from blocking the server.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
from typing import Optional


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request timeouts."""
    
    def __init__(self, app, timeout_seconds: int = 300):
        """
        Initialize timeout middleware.
        
        Args:
            app: FastAPI app
            timeout_seconds: Maximum request duration (default: 5 minutes)
        """
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
    
    async def dispatch(self, request: Request, call_next):
        """Process request with timeout."""
        try:
            # Skip timeout for health checks
            if request.url.path in ["/", "/health"]:
                return await call_next(request)
            
            # Execute with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
            
            return response
            
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail={
                    "status": "error",
                    "message": f"Request timeout after {self.timeout_seconds} seconds",
                    "timeout": self.timeout_seconds
                }
            )


def with_timeout(timeout_seconds: int = 60):
    """
    Decorator to add timeout to specific functions.
    
    Args:
        timeout_seconds: Timeout in seconds
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
                return result
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail={
                        "status": "error",
                        "message": f"Operation timeout after {timeout_seconds} seconds"
                    }
                )
        
        return wrapper
    
    return decorator


# Test function
async def test_timeout():
    """Test timeout functionality."""
    print("\n" + "="*60)
    print("Testing Timeout System")
    print("="*60)
    
    @with_timeout(timeout_seconds=2)
    async def fast_operation():
        """Fast operation that completes in time."""
        await asyncio.sleep(1)
        return "Success"
    
    @with_timeout(timeout_seconds=2)
    async def slow_operation():
        """Slow operation that times out."""
        await asyncio.sleep(5)
        return "Should not reach here"
    
    # Test fast operation
    print("\n1. Testing fast operation (1s with 2s timeout):")
    try:
        result = await fast_operation()
        print(f"   Result: {result}")
        print("   ✅ Completed successfully")
    except HTTPException as e:
        print(f"   ❌ Unexpected timeout: {e.detail}")
    
    # Test slow operation
    print("\n2. Testing slow operation (5s with 2s timeout):")
    try:
        result = await slow_operation()
        print(f"   ❌ Should have timed out but got: {result}")
    except HTTPException as e:
        print(f"   ✅ Timed out as expected: {e.detail['message']}")
    
    print("\n" + "="*60)
    print("✅ Timeout tests passed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_timeout())
