"""
Redis Cache Service
Provides Redis connection management and caching operations
"""

import os
import logging
import json
import pickle
from typing import Any, Optional, List, Dict, Union
from datetime import timedelta

try:
    import redis
    from redis import Redis, ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None  # type: ignore
    ConnectionPool = None  # type: ignore

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service with connection pooling"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50,
        decode_responses: bool = True
    ):
        """
        Initialize cache service
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            max_connections: Maximum connections in pool
            decode_responses: Whether to decode responses to strings
        """
        if not REDIS_AVAILABLE:
            raise RuntimeError("redis package is not installed. Install with: pip install redis")
        
        self.host = host
        self.port = port
        self.db = db
        
        # Create connection pool
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            decode_responses=decode_responses
        )
        
        self.client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish Redis connection"""
        try:
            self.client = redis.Redis(connection_pool=self.pool)
            # Test connection
            if self.client:
                self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)
            
            if ttl:
                return bool(self.client.setex(key, ttl, serialized))
            else:
                return bool(self.client.set(key, serialized))
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        if not self.client:
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        if not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking key {key}: {e}")
            return False
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs
        """
        if not self.client or not keys:
            return {}
        
        try:
            values = self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Error getting multiple keys: {e}")
            return {}
    
    def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set multiple values
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        if not self.client or not mapping:
            return False
        
        try:
            # Serialize values
            serialized = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized[key] = json.dumps(value)
                else:
                    serialized[key] = str(value)
            
            # Use pipeline for efficiency
            pipe = self.client.pipeline()
            pipe.mset(serialized)
            
            if ttl:
                for key in serialized.keys():
                    pipe.expire(key, ttl)
            
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Error setting multiple keys: {e}")
            return False
    
    def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple keys
        
        Args:
            keys: List of cache keys
            
        Returns:
            Number of keys deleted
        """
        if not self.client or not keys:
            return 0
        
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting multiple keys: {e}")
            return 0
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., 'user:*')
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
        
        try:
            keys = list(self.client.scan_iter(match=pattern))
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error deleting pattern {pattern}: {e}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter
        
        Args:
            key: Cache key
            amount: Amount to increment
            
        Returns:
            New value or None on error
        """
        if not self.client:
            return None
        
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return None
    
    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Decrement counter
        
        Args:
            key: Cache key
            amount: Amount to decrement
            
        Returns:
            New value or None on error
        """
        if not self.client:
            return None
        
        try:
            return self.client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Error decrementing key {key}: {e}")
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration on key
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            return bool(self.client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Error setting expiration on key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> Optional[int]:
        """
        Get time to live for key
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        if not self.client:
            return None
        
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return None
    
    def flush_db(self) -> bool:
        """
        Flush current database
        
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.flushdb()
            logger.warning(f"Flushed Redis database {self.db}")
            return True
        except Exception as e:
            logger.error(f"Error flushing database: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get Redis server info
        
        Returns:
            Server information dictionary
        """
        if not self.client:
            return {}
        
        try:
            return self.client.info()
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Statistics dictionary
        """
        if not self.client:
            return {}
        
        try:
            info = self.client.info('stats')
            return {
                'total_connections_received': info.get('total_connections_received', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100
    
    def test_connection(self) -> bool:
        """
        Test Redis connection
        
        Returns:
            True if connection is working
        """
        if not self.client:
            return False
        
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self) -> None:
        """Close Redis connection"""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Initialize cache service
    cache = CacheService(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379))
    )
    
    try:
        # Test connection
        if cache.test_connection():
            print("✓ Redis connection successful")
        
        # Set value
        cache.set('test_key', {'value': 123}, ttl=60)
        print("✓ Set test_key")
        
        # Get value
        value = cache.get('test_key')
        print(f"✓ Got test_key: {value}")
        
        # Get stats
        stats = cache.get_stats()
        print(f"✓ Cache stats: {stats}")
        
    finally:
        cache.close()

# Made with Bob
