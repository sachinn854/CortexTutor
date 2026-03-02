"""
Caching utilities for embeddings and responses.
Simple in-memory cache with TTL support.
"""

from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import hashlib
import json


class SimpleCache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if datetime.now() > entry['expires_at']:
            del self._cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at
        }
    
    def delete(self, key: str):
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of cached items."""
        return len(self._cache)
    
    def cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)


# Global cache instances
embedding_cache = SimpleCache(default_ttl=86400)  # 24 hours
response_cache = SimpleCache(default_ttl=3600)    # 1 hour
vector_store_cache = SimpleCache(default_ttl=7200)  # 2 hours


def cache_embeddings(func):
    """Decorator to cache embedding generation."""
    def wrapper(text: str, *args, **kwargs):
        # Generate cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # Check cache
        cached = embedding_cache.get(cache_key)
        if cached is not None:
            print(f"✅ Cache hit for embeddings")
            return cached
        
        # Generate embeddings
        result = func(text, *args, **kwargs)
        
        # Cache result
        embedding_cache.set(cache_key, result)
        print(f"💾 Cached embeddings")
        
        return result
    
    return wrapper


def cache_response(ttl: int = 3600):
    """Decorator to cache function responses."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = response_cache._generate_key(*args, **kwargs)
            
            # Check cache
            cached = response_cache.get(cache_key)
            if cached is not None:
                print(f"✅ Cache hit for response")
                return cached
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            response_cache.set(cache_key, result, ttl=ttl)
            print(f"💾 Cached response")
            
            return result
        
        return wrapper
    
    return decorator


# Test function
def test_cache():
    """Test cache functionality."""
    print("\n" + "="*60)
    print("Testing Cache System")
    print("="*60)
    
    cache = SimpleCache(default_ttl=2)  # 2 seconds TTL
    
    # Test set and get
    print("\n1. Testing set/get:")
    cache.set("key1", "value1")
    result = cache.get("key1")
    print(f"   Set 'key1' = 'value1'")
    print(f"   Get 'key1' = {result}")
    assert result == "value1", "Cache get failed"
    
    # Test expiration
    print("\n2. Testing expiration:")
    import time
    print("   Waiting 3 seconds...")
    time.sleep(3)
    result = cache.get("key1")
    print(f"   Get 'key1' after expiration = {result}")
    assert result is None, "Cache expiration failed"
    
    # Test cache size
    print("\n3. Testing cache size:")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    size = cache.size()
    print(f"   Cache size = {size}")
    assert size == 2, "Cache size incorrect"
    
    # Test clear
    print("\n4. Testing clear:")
    cache.clear()
    size = cache.size()
    print(f"   Cache size after clear = {size}")
    assert size == 0, "Cache clear failed"
    
    # Test decorator
    print("\n5. Testing decorator:")
    
    @cache_response(ttl=5)
    def expensive_function(x):
        print(f"   Computing {x}...")
        return x * 2
    
    result1 = expensive_function(5)
    print(f"   First call result = {result1}")
    
    result2 = expensive_function(5)
    print(f"   Second call result = {result2} (should be cached)")
    
    print("\n" + "="*60)
    print("✅ Cache tests passed!")
    print("="*60)


if __name__ == "__main__":
    test_cache()
