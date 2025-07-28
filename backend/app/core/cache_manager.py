"""
Redis caching and session management system.
"""
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, Union, Dict
import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings


class CacheManager:
    """Redis-based cache manager for the application."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self.redis: Optional[redis.Redis] = None
        
    async def connect(self):
        """Connect to Redis."""
        if not self.redis:
            self.redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None,
        prefix: str = "cache"
    ) -> bool:
        """Set a value in cache with optional expiration."""
        await self.connect()
        
        full_key = f"{prefix}:{key}"
        
        # Serialize the value
        if isinstance(value, (dict, list, BaseModel)):
            if isinstance(value, BaseModel):
                serialized_value = value.model_dump_json()
            else:
                serialized_value = json.dumps(value)
        else:
            serialized_value = str(value)
            
        # Set the value
        if expire:
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            return await self.redis.setex(full_key, expire, serialized_value)
        else:
            return await self.redis.set(full_key, serialized_value)
            
    async def get(
        self,
        key: str,
        prefix: str = "cache",
        default: Any = None
    ) -> Any:
        """Get a value from cache."""
        await self.connect()
        
        full_key = f"{prefix}:{key}"
        value = await self.redis.get(full_key)
        
        if value is None:
            return default
            
        try:
            # Try to deserialize as JSON first
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Return as string if not JSON
            return value
            
    async def delete(self, key: str, prefix: str = "cache") -> bool:
        """Delete a value from cache."""
        await self.connect()
        
        full_key = f"{prefix}:{key}"
        result = await self.redis.delete(full_key)
        return result > 0
        
    async def exists(self, key: str, prefix: str = "cache") -> bool:
        """Check if a key exists in cache."""
        await self.connect()
        
        full_key = f"{prefix}:{key}"
        return await self.redis.exists(full_key)
        
    async def expire(self, key: str, seconds: int, prefix: str = "cache") -> bool:
        """Set expiration time for a key."""
        await self.connect()
        
        full_key = f"{prefix}:{key}"
        return await self.redis.expire(full_key, seconds)
        
    async def ttl(self, key: str, prefix: str = "cache") -> int:
        """Get time to live for a key."""
        await self.connect()
        
        full_key = f"{prefix}:{key}"
        return await self.redis.ttl(full_key)
        
    async def keys(self, pattern: str = "*", prefix: str = "cache") -> list:
        """Get all keys matching a pattern."""
        await self.connect()
        
        full_pattern = f"{prefix}:{pattern}"
        keys = await self.redis.keys(full_pattern)
        # Remove prefix from returned keys
        return [key.replace(f"{prefix}:", "") for key in keys]
        
    async def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with a specific prefix."""
        await self.connect()
        
        pattern = f"{prefix}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            return await self.redis.delete(*keys)
        return 0
        
    # Session management methods
    async def set_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        expire: int = 86400  # 24 hours default
    ) -> bool:
        """Set session data."""
        return await self.set(
            key=session_id,
            value=session_data,
            expire=expire,
            prefix="session"
        )
        
    async def get_session(
        self,
        session_id: str,
        default: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get session data."""
        return await self.get(
            key=session_id,
            prefix="session",
            default=default or {}
        )
        
    async def delete_session(self, session_id: str) -> bool:
        """Delete session data."""
        return await self.delete(key=session_id, prefix="session")
        
    async def extend_session(self, session_id: str, extend_by: int = 86400) -> bool:
        """Extend session expiration."""
        return await self.expire(key=session_id, seconds=extend_by, prefix="session")
        
    # User-specific caching methods
    async def set_user_cache(
        self,
        user_id: str,
        cache_key: str,
        value: Any,
        expire: Optional[int] = 3600  # 1 hour default
    ) -> bool:
        """Set user-specific cache."""
        key = f"user:{user_id}:{cache_key}"
        return await self.set(key=key, value=value, expire=expire, prefix="ucache")
        
    async def get_user_cache(
        self,
        user_id: str,
        cache_key: str,
        default: Any = None
    ) -> Any:
        """Get user-specific cache."""
        key = f"user:{user_id}:{cache_key}"
        return await self.get(key=key, prefix="ucache", default=default)
        
    async def clear_user_cache(self, user_id: str) -> int:
        """Clear all cache for a specific user."""
        return await self.clear_prefix(f"ucache:user:{user_id}")
        
    # Rate limiting methods
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int = 60  # 1 minute window
    ) -> Dict[str, Any]:
        """Check rate limit for an identifier."""
        await self.connect()
        
        key = f"ratelimit:{identifier}"
        current = await self.redis.get(key)
        
        if current is None:
            # First request
            await self.redis.setex(key, window, 1)
            return {
                "allowed": True,
                "count": 1,
                "limit": limit,
                "reset_at": datetime.utcnow() + timedelta(seconds=window)
            }
        else:
            count = int(current)
            if count >= limit:
                # Rate limit exceeded
                ttl = await self.redis.ttl(key)
                return {
                    "allowed": False,
                    "count": count,
                    "limit": limit,
                    "reset_at": datetime.utcnow() + timedelta(seconds=ttl)
                }
            else:
                # Increment counter
                await self.redis.incr(key)
                ttl = await self.redis.ttl(key)
                return {
                    "allowed": True,
                    "count": count + 1,
                    "limit": limit,
                    "reset_at": datetime.utcnow() + timedelta(seconds=ttl)
                }
                
    # Statistics and monitoring
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        await self.connect()
        
        info = await self.redis.info()
        
        return {
            "redis_version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) / 
                max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
            ) * 100
        }


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions
async def cache_set(key: str, value: Any, expire: Optional[int] = None) -> bool:
    """Convenience function to set cache."""
    return await cache_manager.set(key, value, expire)


async def cache_get(key: str, default: Any = None) -> Any:
    """Convenience function to get cache."""
    return await cache_manager.get(key, default=default)


async def cache_delete(key: str) -> bool:
    """Convenience function to delete cache."""
    return await cache_manager.delete(key)


async def cache_exists(key: str) -> bool:
    """Convenience function to check cache existence."""
    return await cache_manager.exists(key)