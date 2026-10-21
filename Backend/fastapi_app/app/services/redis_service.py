# backend/fastapi_app/services/redis_service.py
import redis.asyncio as redis
import json
import logging
from typing import Optional, Any


from ..config import settings

logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for caching and pub/sub"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._client is None:
            self._client = await redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8"
            )
        return self._client
    
    async def ping(self) -> bool:
        """Check Redis connection"""
        try:
            client = await self.get_client()
            return await client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            client = await self.get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get failed: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            client = await self.get_client()
            await client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Redis set failed: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            client = await self.get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete failed: {str(e)}")
            return False
    
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel"""
        try:
            client = await self.get_client()
            if isinstance(message, dict):
                message = json.dumps(message)
            return await client.publish(channel, message)
        except Exception as e:
            logger.error(f"Redis publish failed: {str(e)}")
            return 0
    
    def pubsub(self):
        """Get pubsub instance"""
        return self._client.pubsub() if self._client else None

# Singleton instance
redis_client = RedisService()