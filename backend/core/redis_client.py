"""
Redis Client for Caching, Session Management, and Rate Limiting
Async Redis operations with connection pooling
"""

import json
import pickle
from typing import Any, Optional, Union
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper"""
    
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection pool"""
        self.pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=50,
            decode_responses=False,
        )
        self.client = redis.Redis(connection_pool=self.pool)
        
        # Test connection
        await self.client.ping()
        logger.info("Redis connected successfully")
    
    async def disconnect(self):
        """Close Redis connection pool"""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        logger.info("Redis disconnected")
    
    async def get(self, key: str, use_pickle: bool = False) -> Optional[Any]:
        """Get value by key"""
        if not self.client:
            return None
        
        value = await self.client.get(key)
        if value and use_pickle:
            return pickle.loads(value)
        return value.decode() if value else None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        use_pickle: bool = False,
    ) -> bool:
        """Set key-value pair with optional TTL"""
        if not self.client:
            return False
        
        if use_pickle:
            value = pickle.dumps(value)
        elif isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif not isinstance(value, bytes):
            value = str(value).encode()
        
        if ttl:
            await self.client.setex(key, ttl, value)
        else:
            await self.client.set(key, value)
        return True
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        if not self.client:
            return 0
        return await self.client.delete(*keys)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        return await self.client.exists(key) > 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key"""
        if not self.client:
            return False
        return await self.client.expire(key, ttl)
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self.client:
            return 0
        return await self.client.incr(key, amount)
    
    async def sadd(self, key: str, *values: str) -> int:
        """Add to set"""
        if not self.client:
            return 0
        return await self.client.sadd(key, *values)
    
    async def srem(self, key: str, *values: str) -> int:
        """Remove from set"""
        if not self.client:
            return 0
        return await self.client.srem(key, *values)
    
    async def smembers(self, key: str) -> set:
        """Get all set members"""
        if not self.client:
            return set()
        members = await self.client.smembers(key)
        return {m.decode() for m in members}


# Global Redis client instance
redis_client = RedisClient()