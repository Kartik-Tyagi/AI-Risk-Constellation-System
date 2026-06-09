"""
Cache Strategies
Implements various caching patterns and TTL strategies
"""

import logging
from typing import Any, Optional, Callable, Dict
from datetime import timedelta
from functools import wraps
from enum import Enum

from backend.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class CachePattern(Enum):
    """Cache pattern types"""
    CACHE_ASIDE = "cache_aside"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    READ_THROUGH = "read_through"


class TTLStrategy:
    """TTL (Time To Live) strategies for different data types"""
    
    # Default TTLs in seconds
    MARKET_DATA = 60  # 1 minute
    RISK_CALCULATIONS = 300  # 5 minutes
    PORTFOLIO_DATA = 600  # 10 minutes
    USER_SESSION = 3600  # 1 hour
    STATIC_DATA = 86400  # 24 hours
    TEMPORARY = 30  # 30 seconds
    
    @staticmethod
    def get_ttl(data_type: str) -> int:
        """
        Get TTL for data type
        
        Args:
            data_type: Type of data
            
        Returns:
            TTL in seconds
        """
        ttl_map = {
            'market_data': TTLStrategy.MARKET_DATA,
            'risk_calculation': TTLStrategy.RISK_CALCULATIONS,
            'portfolio': TTLStrategy.PORTFOLIO_DATA,
            'user_session': TTLStrategy.USER_SESSION,
            'static': TTLStrategy.STATIC_DATA,
            'temporary': TTLStrategy.TEMPORARY
        }
        return ttl_map.get(data_type, TTLStrategy.TEMPORARY)


class CacheKeyBuilder:
    """Builds cache keys with consistent naming"""
    
    @staticmethod
    def build_key(prefix: str, *args: Any) -> str:
        """
        Build cache key
        
        Args:
            prefix: Key prefix
            *args: Key components
            
        Returns:
            Cache key string
        """
        components = [prefix] + [str(arg) for arg in args]
        return ':'.join(components)
    
    @staticmethod
    def market_data_key(asset_id: str, timestamp: str) -> str:
        """Build market data cache key"""
        return CacheKeyBuilder.build_key('market_data', asset_id, timestamp)
    
    @staticmethod
    def risk_calculation_key(entity_id: str, calculation_type: str) -> str:
        """Build risk calculation cache key"""
        return CacheKeyBuilder.build_key('risk_calc', entity_id, calculation_type)
    
    @staticmethod
    def portfolio_key(portfolio_id: str) -> str:
        """Build portfolio cache key"""
        return CacheKeyBuilder.build_key('portfolio', portfolio_id)
    
    @staticmethod
    def user_session_key(user_id: str) -> str:
        """Build user session cache key"""
        return CacheKeyBuilder.build_key('session', user_id)


class CacheAside:
    """
    Cache-Aside (Lazy Loading) Pattern
    Application checks cache first, loads from DB on miss
    """
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    def get(
        self,
        key: str,
        loader: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value with cache-aside pattern
        
        Args:
            key: Cache key
            loader: Function to load data on cache miss
            ttl: Time to live in seconds
            
        Returns:
            Cached or loaded value
        """
        # Try cache first
        value = self.cache.get(key)
        if value is not None:
            logger.debug(f"Cache hit: {key}")
            return value
        
        # Cache miss - load from source
        logger.debug(f"Cache miss: {key}")
        value = loader()
        
        # Store in cache
        if value is not None:
            self.cache.set(key, value, ttl)
        
        return value
    
    def decorator(self, key_builder: Callable, ttl: Optional[int] = None):
        """
        Decorator for cache-aside pattern
        
        Args:
            key_builder: Function to build cache key from args
            ttl: Time to live in seconds
        """
        def decorator_wrapper(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Build cache key
                key = key_builder(*args, **kwargs)
                
                # Try cache
                value = self.cache.get(key)
                if value is not None:
                    logger.debug(f"Cache hit: {key}")
                    return value
                
                # Cache miss - call function
                logger.debug(f"Cache miss: {key}")
                value = func(*args, **kwargs)
                
                # Store in cache
                if value is not None:
                    self.cache.set(key, value, ttl)
                
                return value
            return wrapper
        return decorator_wrapper


class WriteThrough:
    """
    Write-Through Pattern
    Writes go through cache to database
    """
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    def set(
        self,
        key: str,
        value: Any,
        writer: Callable[[Any], bool],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value with write-through pattern
        
        Args:
            key: Cache key
            value: Value to set
            writer: Function to write to database
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        # Write to database first
        if not writer(value):
            logger.error(f"Failed to write to database for key: {key}")
            return False
        
        # Write to cache
        return self.cache.set(key, value, ttl)


class CacheWarmer:
    """
    Cache Warming
    Pre-loads frequently accessed data into cache
    """
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    def warm_market_data(
        self,
        asset_ids: list,
        data_loader: Callable[[str], Any],
        ttl: Optional[int] = None
    ) -> Dict[str, bool]:
        """
        Warm cache with market data
        
        Args:
            asset_ids: List of asset IDs
            data_loader: Function to load data for an asset
            ttl: Time to live in seconds
            
        Returns:
            Dictionary of asset_id: success status
        """
        results = {}
        for asset_id in asset_ids:
            try:
                data = data_loader(asset_id)
                key = CacheKeyBuilder.market_data_key(asset_id, 'latest')
                success = self.cache.set(key, data, ttl or TTLStrategy.MARKET_DATA)
                results[asset_id] = success
            except Exception as e:
                logger.error(f"Failed to warm cache for {asset_id}: {e}")
                results[asset_id] = False
        
        return results
    
    def warm_risk_calculations(
        self,
        entity_ids: list,
        calculation_type: str,
        data_loader: Callable[[str], Any],
        ttl: Optional[int] = None
    ) -> Dict[str, bool]:
        """
        Warm cache with risk calculations
        
        Args:
            entity_ids: List of entity IDs
            calculation_type: Type of calculation
            data_loader: Function to load data for an entity
            ttl: Time to live in seconds
            
        Returns:
            Dictionary of entity_id: success status
        """
        results = {}
        for entity_id in entity_ids:
            try:
                data = data_loader(entity_id)
                key = CacheKeyBuilder.risk_calculation_key(entity_id, calculation_type)
                success = self.cache.set(key, data, ttl or TTLStrategy.RISK_CALCULATIONS)
                results[entity_id] = success
            except Exception as e:
                logger.error(f"Failed to warm cache for {entity_id}: {e}")
                results[entity_id] = False
        
        return results
    
    def warm_portfolios(
        self,
        portfolio_ids: list,
        data_loader: Callable[[str], Any],
        ttl: Optional[int] = None
    ) -> Dict[str, bool]:
        """
        Warm cache with portfolio data
        
        Args:
            portfolio_ids: List of portfolio IDs
            data_loader: Function to load data for a portfolio
            ttl: Time to live in seconds
            
        Returns:
            Dictionary of portfolio_id: success status
        """
        results = {}
        for portfolio_id in portfolio_ids:
            try:
                data = data_loader(portfolio_id)
                key = CacheKeyBuilder.portfolio_key(portfolio_id)
                success = self.cache.set(key, data, ttl or TTLStrategy.PORTFOLIO_DATA)
                results[portfolio_id] = success
            except Exception as e:
                logger.error(f"Failed to warm cache for {portfolio_id}: {e}")
                results[portfolio_id] = False
        
        return results


class AdaptiveTTL:
    """
    Adaptive TTL Strategy
    Adjusts TTL based on access patterns
    """
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.access_counts: Dict[str, int] = {}
        self.base_ttl = 300  # 5 minutes
        self.max_ttl = 3600  # 1 hour
        self.min_ttl = 60  # 1 minute
    
    def get_adaptive_ttl(self, key: str) -> int:
        """
        Calculate adaptive TTL based on access frequency
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds
        """
        # Track access
        self.access_counts[key] = self.access_counts.get(key, 0) + 1
        access_count = self.access_counts[key]
        
        # More accesses = longer TTL
        if access_count > 100:
            return self.max_ttl
        elif access_count > 50:
            return self.base_ttl * 2
        elif access_count > 10:
            return self.base_ttl
        else:
            return self.min_ttl
    
    def reset_stats(self) -> None:
        """Reset access statistics"""
        self.access_counts.clear()


# Example usage
if __name__ == '__main__':
    import os
    logging.basicConfig(level=logging.INFO)
    
    # Initialize cache service
    cache_service = CacheService(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379))
    )
    
    try:
        # Cache-Aside example
        cache_aside = CacheAside(cache_service)
        
        def load_portfolio(portfolio_id):
            print(f"Loading portfolio {portfolio_id} from database...")
            return {'id': portfolio_id, 'value': 1000000}
        
        # First call - cache miss
        data1 = cache_aside.get(
            'portfolio:001',
            lambda: load_portfolio('001'),
            ttl=TTLStrategy.PORTFOLIO_DATA
        )
        print(f"First call: {data1}")
        
        # Second call - cache hit
        data2 = cache_aside.get(
            'portfolio:001',
            lambda: load_portfolio('001'),
            ttl=TTLStrategy.PORTFOLIO_DATA
        )
        print(f"Second call: {data2}")
        
        # Cache warming example
        warmer = CacheWarmer(cache_service)
        results = warmer.warm_portfolios(
            ['001', '002', '003'],
            load_portfolio,
            ttl=TTLStrategy.PORTFOLIO_DATA
        )
        print(f"Warming results: {results}")
        
    finally:
        cache_service.close()

# Made with Bob
