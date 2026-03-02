"""
Performance monitoring and metrics collection.
Tracks request duration, memory usage, and error rates.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import psutil
import os
from typing import Dict, List
from datetime import datetime
from collections import defaultdict


class PerformanceMonitor:
    """Monitor application performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.request_times: List[float] = []
        self.endpoint_times: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[int, int] = defaultdict(int)
        self.request_count = 0
        self.start_time = time.time()
    
    def record_request(self, endpoint: str, duration: float, status_code: int):
        """
        Record request metrics.
        
        Args:
            endpoint: API endpoint
            duration: Request duration in seconds
            status_code: HTTP status code
        """
        self.request_count += 1
        self.request_times.append(duration)
        self.endpoint_times[endpoint].append(duration)
        
        if status_code >= 400:
            self.error_counts[status_code] += 1
    
    def get_stats(self) -> Dict:
        """Get performance statistics."""
        if not self.request_times:
            return {
                "total_requests": 0,
                "avg_response_time": 0,
                "uptime_seconds": time.time() - self.start_time
            }
        
        return {
            "total_requests": self.request_count,
            "avg_response_time": sum(self.request_times) / len(self.request_times),
            "min_response_time": min(self.request_times),
            "max_response_time": max(self.request_times),
            "uptime_seconds": time.time() - self.start_time,
            "error_counts": dict(self.error_counts),
            "memory_usage_mb": self.get_memory_usage(),
            "cpu_percent": psutil.cpu_percent(interval=0.1)
        }
    
    def get_endpoint_stats(self) -> Dict:
        """Get per-endpoint statistics."""
        stats = {}
        
        for endpoint, times in self.endpoint_times.items():
            if times:
                stats[endpoint] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        
        return stats
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def reset(self):
        """Reset all metrics."""
        self.request_times.clear()
        self.endpoint_times.clear()
        self.error_counts.clear()
        self.request_count = 0
        self.start_time = time.time()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track performance metrics."""
    
    def __init__(self, app, monitor: PerformanceMonitor):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI app
            monitor: Performance monitor instance
        """
        super().__init__(app)
        self.monitor = monitor
    
    async def dispatch(self, request: Request, call_next):
        """Process request and record metrics."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        endpoint = f"{request.method} {request.url.path}"
        self.monitor.record_request(endpoint, duration, response.status_code)
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response


# Global monitor instance
global_monitor = PerformanceMonitor()


def log_performance(func):
    """Decorator to log function performance."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            print(f"⏱️  {func.__name__} took {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise
    
    return wrapper


def get_system_info() -> Dict:
    """Get system information."""
    return {
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
        "memory_available_gb": psutil.virtual_memory().available / 1024 / 1024 / 1024,
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage_percent": psutil.disk_usage('/').percent
    }


# Test function
def test_monitoring():
    """Test monitoring functionality."""
    print("\n" + "="*60)
    print("Testing Performance Monitoring")
    print("="*60)
    
    monitor = PerformanceMonitor()
    
    # Simulate requests
    print("\n1. Simulating requests:")
    monitor.record_request("GET /api/test", 0.1, 200)
    monitor.record_request("POST /api/test", 0.5, 200)
    monitor.record_request("GET /api/test", 0.2, 200)
    monitor.record_request("POST /api/test", 1.0, 500)
    print("   Recorded 4 requests")
    
    # Get stats
    print("\n2. Overall statistics:")
    stats = monitor.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")
    
    # Get endpoint stats
    print("\n3. Per-endpoint statistics:")
    endpoint_stats = monitor.get_endpoint_stats()
    for endpoint, stats in endpoint_stats.items():
        print(f"   {endpoint}:")
        print(f"     Count: {stats['count']}")
        print(f"     Avg time: {stats['avg_time']:.3f}s")
    
    # Get system info
    print("\n4. System information:")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    
    # Test decorator
    print("\n5. Testing performance decorator:")
    
    @log_performance
    def slow_function():
        time.sleep(0.1)
        return "Done"
    
    result = slow_function()
    print(f"   Result: {result}")
    
    print("\n" + "="*60)
    print("✅ Monitoring tests passed!")
    print("="*60)


if __name__ == "__main__":
    test_monitoring()
