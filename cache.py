"""
Cache Layer for ResellSquare
Manages cached market data with TTL (time-to-live)
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path


class Cache:
    """Simple JSON-based cache with TTL"""
    
    def __init__(self, cache_dir: str = ".cache", ttl_hours: int = 12):
        """
        Initialize cache
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours (default 12)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_hours = ttl_hours
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key"""
        # Sanitize key for filename
        safe_key = "".join(c if c.isalnum() else "_" for c in key.lower())
        return self.cache_dir / f"{safe_key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data if exists and not expired
        
        Args:
            key: Cache key (e.g., "ebay:airpods pro")
            
        Returns:
            Cached data dict or None if expired/missing
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            
            # Check if expired
            cached_at = datetime.fromisoformat(cached['cached_at'])
            expiry = cached_at + timedelta(hours=self.ttl_hours)
            
            if datetime.now() > expiry:
                # Expired - delete and return None
                cache_path.unlink()
                return None
            
            return cached['data']
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted cache - delete and return None
            if cache_path.exists():
                cache_path.unlink()
            return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        Store data in cache
        
        Args:
            key: Cache key
            data: Data to cache
        """
        cache_path = self._get_cache_path(key)
        
        cached = {
            'cached_at': datetime.now().isoformat(),
            'key': key,
            'data': data
        }
        
        with open(cache_path, 'w') as f:
            json.dump(cached, f, indent=2)
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache
        
        Args:
            key: Specific key to clear, or None to clear all
        """
        if key:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
    
    def is_fresh(self, key: str) -> bool:
        """Check if cache exists and is fresh"""
        return self.get(key) is not None


# Global cache instance
cache = Cache()


# Test if run directly
if __name__ == "__main__":
    print("Testing cache...")
    
    # Test set
    cache.set("test:product", {"prices": [10, 20, 30]})
    print("✓ Set cache")
    
    # Test get
    data = cache.get("test:product")
    print(f"✓ Got cache: {data}")
    
    # Test is_fresh
    fresh = cache.is_fresh("test:product")
    print(f"✓ Is fresh: {fresh}")
    
    # Test clear
    cache.clear("test:product")
    print("✓ Cleared cache")
    
    # Verify cleared
    data = cache.get("test:product")
    print(f"✓ After clear: {data}")
    
    print("\nCache tests passed! ✅")
