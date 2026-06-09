"""
Cache Manager for Real-Time Inference Results.

This module provides Redis-based caching for inference results with
intelligent cache invalidation and TTL management.
"""

import logging
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import hashlib

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. Install with: pip install redis")

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for cache manager."""
    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    default_ttl: int = 3600  # 1 hour
    max_ttl: int = 86400  # 24 hours
    key_prefix: str = 'risk_calc:'
    enable_compression: bool = False


class CacheManager:
    """
    Redis-based cache manager for inference results.
    
    Provides caching with TTL management, invalidation strategies,
    and optional compression for large results.
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize cache manager.
        
        Args:
            config: Cache configuration (uses defaults if None)
        """
        self.config = config or CacheConfig()
        self.client: Optional[redis.Redis] = None
        self.enabled = False
        
        if REDIS_AVAILABLE:
            try:
                self.client = redis.Redis(
                    host=self.config.host,
                    port=self.config.port,
                    db=self.config.db,
                    password=self.config.password,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # Test connection
                self.client.ping()  # type: ignore
                self.enabled = True
                logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
                self.client = None
                self.enabled = False
        else:
            logger.warning("Redis not available. Caching disabled.")
    
    def _generate_key(self, entity_id: str, features_hash: Optional[str] = None) -> str:
        """
        Generate cache key for an entity.
        
        Args:
            entity_id: Entity identifier
            features_hash: Hash of features (optional)
            
        Returns:
            Cache key
        """
        if features_hash:
            return f"{self.config.key_prefix}{entity_id}:{features_hash}"
        return f"{self.config.key_prefix}{entity_id}"
    
    def _hash_features(self, features: Dict[str, Any]) -> str:
        """
        Generate hash of features for cache key.
        
        Args:
            features: Features dictionary
            
        Returns:
            Hash string
        """
        # Sort keys for consistent hashing
        features_str = json.dumps(features, sort_keys=True)
        return hashlib.md5(features_str.encode()).hexdigest()[:16]
    
    def get(self, entity_id: str, features: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached result for an entity.
        
        Args:
            entity_id: Entity identifier
            features: Features dictionary (for hash-based key)
            
        Returns:
            Cached result or None
        """
        if not self.enabled or self.client is None:
            return None
        
        try:
            features_hash = self._hash_features(features) if features else None
            key = self._generate_key(entity_id, features_hash)
            
            cached = self.client.get(key)
            if cached:
                result = json.loads(cached)
                logger.debug(f"Cache hit for {entity_id}")
                return result
            
            logger.debug(f"Cache miss for {entity_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, entity_id: str, result: Dict[str, Any],
            features: Optional[Dict[str, Any]] = None,
            ttl: Optional[int] = None):
        """
        Cache a result for an entity.
        
        Args:
            entity_id: Entity identifier
            result: Result to cache
            features: Features dictionary (for hash-based key)
            ttl: Time to live in seconds (uses default if None)
        """
        if not self.enabled or self.client is None:
            return
        
        try:
            features_hash = self._hash_features(features) if features else None
            key = self._generate_key(entity_id, features_hash)
            ttl = ttl or self.config.default_ttl
            
            # Ensure TTL doesn't exceed max
            ttl = min(ttl, self.config.max_ttl)
            
            # Serialize result
            cached_data = json.dumps(result)
            
            # Store with TTL
            self.client.setex(key, ttl, cached_data)
            logger.debug(f"Cached result for {entity_id} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
    
    def delete(self, entity_id: str, features: Optional[Dict[str, Any]] = None):
        """
        Delete cached result for an entity.
        
        Args:
            entity_id: Entity identifier
            features: Features dictionary (for hash-based key)
        """
        if not self.enabled or self.client is None:
            return
        
        try:
            features_hash = self._hash_features(features) if features else None
            key = self._generate_key(entity_id, features_hash)
            self.client.delete(key)
            logger.debug(f"Deleted cache for {entity_id}")
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., 'risk_calc:ENTITY_*')
        """
        if not self.enabled or self.client is None:
            return
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Error invalidating pattern: {e}")
    
    def invalidate_entity(self, entity_id: str):
        """
        Invalidate all cached results for an entity.
        
        Args:
            entity_id: Entity identifier
        """
        pattern = f"{self.config.key_prefix}{entity_id}*"
        self.invalidate_pattern(pattern)
    
    def invalidate_all(self):
        """Invalidate all cached results."""
        pattern = f"{self.config.key_prefix}*"
        self.invalidate_pattern(pattern)
    
    def get_ttl(self, entity_id: str, features: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Get remaining TTL for a cached result.
        
        Args:
            entity_id: Entity identifier
            features: Features dictionary (for hash-based key)
            
        Returns:
            Remaining TTL in seconds or None
        """
        if not self.enabled or self.client is None:
            return None
        
        try:
            features_hash = self._hash_features(features) if features else None
            key = self._generate_key(entity_id, features_hash)
            ttl = self.client.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Error getting TTL: {e}")
            return None
    
    def extend_ttl(self, entity_id: str, additional_seconds: int,
                   features: Optional[Dict[str, Any]] = None):
        """
        Extend TTL for a cached result.
        
        Args:
            entity_id: Entity identifier
            additional_seconds: Seconds to add to TTL
            features: Features dictionary (for hash-based key)
        """
        if not self.enabled or self.client is None:
            return
        
        try:
            features_hash = self._hash_features(features) if features else None
            key = self._generate_key(entity_id, features_hash)
            
            current_ttl = self.client.ttl(key)
            if current_ttl > 0:
                new_ttl = min(current_ttl + additional_seconds, self.config.max_ttl)
                self.client.expire(key, new_ttl)
                logger.debug(f"Extended TTL for {entity_id} to {new_ttl}s")
        except Exception as e:
            logger.error(f"Error extending TTL: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        if not self.enabled or self.client is None:
            return {'enabled': False}
        
        try:
            info = self.client.info('stats')
            pattern = f"{self.config.key_prefix}*"
            num_keys = len(self.client.keys(pattern))
            
            return {
                'enabled': True,
                'host': self.config.host,
                'port': self.config.port,
                'num_keys': num_keys,
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """
        Calculate cache hit rate.
        
        Args:
            hits: Number of cache hits
            misses: Number of cache misses
            
        Returns:
            Hit rate (0-1)
        """
        total = hits + misses
        return hits / total if total > 0 else 0.0
    
    def batch_get(self, entity_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get cached results for multiple entities.
        
        Args:
            entity_ids: List of entity identifiers
            
        Returns:
            Dictionary mapping entity_id to cached result (or None)
        """
        results: Dict[str, Optional[Dict[str, Any]]] = {}
        
        if not self.enabled or self.client is None:
            return {eid: None for eid in entity_ids}
        
        try:
            # Use pipeline for efficiency
            pipe = self.client.pipeline()
            keys = [self._generate_key(eid) for eid in entity_ids]
            
            for key in keys:
                pipe.get(key)
            
            cached_results = pipe.execute()
            
            for entity_id, cached in zip(entity_ids, cached_results):
                if cached:
                    results[entity_id] = json.loads(cached)
                else:
                    results[entity_id] = None
            
            hits = sum(1 for r in results.values() if r is not None)
            logger.debug(f"Batch get: {hits}/{len(entity_ids)} hits")
            
        except Exception as e:
            logger.error(f"Error in batch get: {e}")
            results = {eid: None for eid in entity_ids}
        
        return results
    
    def batch_set(self, results: Dict[str, Dict[str, Any]], ttl: Optional[int] = None):
        """
        Cache results for multiple entities.
        
        Args:
            results: Dictionary mapping entity_id to result
            ttl: Time to live in seconds (uses default if None)
        """
        if not self.enabled or self.client is None:
            return
        
        try:
            ttl = ttl or self.config.default_ttl
            ttl = min(ttl, self.config.max_ttl)
            
            # Use pipeline for efficiency
            pipe = self.client.pipeline()
            
            for entity_id, result in results.items():
                key = self._generate_key(entity_id)
                cached_data = json.dumps(result)
                pipe.setex(key, ttl, cached_data)
            
            pipe.execute()
            logger.debug(f"Batch cached {len(results)} results (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Error in batch set: {e}")
    
    def close(self):
        """Close Redis connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("Closed Redis connection")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")


if __name__ == '__main__':
    # Example usage
    print("Cache Manager Module")
    
    # Create cache manager
    config = CacheConfig(host='localhost', port=6379)
    cache = CacheManager(config)
    
    if cache.enabled:
        print(f"Cache enabled: {cache.enabled}")
        
        # Test caching
        test_result = {
            'entity_id': 'TEST_001',
            'risk_score': 0.75,
            'timestamp': time.time()
        }
        
        cache.set('TEST_001', test_result, ttl=60)
        cached = cache.get('TEST_001')
        
        print(f"Cached result: {cached}")
        print(f"Cache stats: {cache.get_stats()}")
        
        cache.close()
    else:
        print("Cache not available")

# Made with Bob
