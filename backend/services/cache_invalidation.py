"""
Cache Invalidation
Handles cache invalidation triggers and strategies
"""

import logging
from typing import List, Optional, Set, Dict, Any, Callable
from datetime import datetime
from enum import Enum

from backend.services.cache_service import CacheService
from backend.services.cache_strategies import CacheKeyBuilder

logger = logging.getLogger(__name__)


class InvalidationTrigger(Enum):
    """Cache invalidation trigger types"""
    DATA_UPDATE = "data_update"
    TIME_BASED = "time_based"
    MANUAL = "manual"
    DEPENDENCY = "dependency"


class CacheInvalidation:
    """Manages cache invalidation"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.dependencies: Dict[str, Set[str]] = {}
    
    def invalidate_key(self, key: str, trigger: InvalidationTrigger = InvalidationTrigger.MANUAL) -> bool:
        """
        Invalidate a single cache key
        
        Args:
            key: Cache key to invalidate
            trigger: Invalidation trigger type
            
        Returns:
            True if successful
        """
        logger.info(f"Invalidating cache key: {key} (trigger: {trigger.value})")
        success = self.cache.delete(key)
        
        # Invalidate dependent keys
        if key in self.dependencies:
            for dependent_key in self.dependencies[key]:
                self.cache.delete(dependent_key)
                logger.debug(f"Invalidated dependent key: {dependent_key}")
        
        return success
    
    def invalidate_pattern(self, pattern: str, trigger: InvalidationTrigger = InvalidationTrigger.MANUAL) -> int:
        """
        Invalidate keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., 'market_data:*')
            trigger: Invalidation trigger type
            
        Returns:
            Number of keys invalidated
        """
        logger.info(f"Invalidating cache pattern: {pattern} (trigger: {trigger.value})")
        return self.cache.delete_pattern(pattern)
    
    def invalidate_market_data(self, asset_id: Optional[str] = None) -> int:
        """
        Invalidate market data cache
        
        Args:
            asset_id: Specific asset ID or None for all
            
        Returns:
            Number of keys invalidated
        """
        if asset_id:
            pattern = f"market_data:{asset_id}:*"
        else:
            pattern = "market_data:*"
        
        return self.invalidate_pattern(pattern, InvalidationTrigger.DATA_UPDATE)
    
    def invalidate_risk_calculations(self, entity_id: Optional[str] = None) -> int:
        """
        Invalidate risk calculation cache
        
        Args:
            entity_id: Specific entity ID or None for all
            
        Returns:
            Number of keys invalidated
        """
        if entity_id:
            pattern = f"risk_calc:{entity_id}:*"
        else:
            pattern = "risk_calc:*"
        
        return self.invalidate_pattern(pattern, InvalidationTrigger.DATA_UPDATE)
    
    def invalidate_portfolio(self, portfolio_id: str) -> bool:
        """
        Invalidate portfolio cache
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            True if successful
        """
        key = CacheKeyBuilder.portfolio_key(portfolio_id)
        return self.invalidate_key(key, InvalidationTrigger.DATA_UPDATE)
    
    def register_dependency(self, parent_key: str, dependent_key: str) -> None:
        """
        Register cache key dependency
        
        Args:
            parent_key: Parent cache key
            dependent_key: Dependent cache key
        """
        if parent_key not in self.dependencies:
            self.dependencies[parent_key] = set()
        self.dependencies[parent_key].add(dependent_key)
        logger.debug(f"Registered dependency: {parent_key} -> {dependent_key}")
    
    def unregister_dependency(self, parent_key: str, dependent_key: str) -> None:
        """
        Unregister cache key dependency
        
        Args:
            parent_key: Parent cache key
            dependent_key: Dependent cache key
        """
        if parent_key in self.dependencies:
            self.dependencies[parent_key].discard(dependent_key)
            logger.debug(f"Unregistered dependency: {parent_key} -> {dependent_key}")


class SelectiveInvalidation:
    """Selective cache invalidation based on data changes"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.invalidation = CacheInvalidation(cache_service)
    
    def on_transaction_created(self, transaction: Dict[str, Any]) -> None:
        """
        Handle cache invalidation when transaction is created
        
        Args:
            transaction: Transaction data
        """
        portfolio_id = transaction.get('portfolio_id')
        asset_id = transaction.get('asset_id')
        
        # Invalidate portfolio cache
        if portfolio_id:
            self.invalidation.invalidate_portfolio(portfolio_id)
        
        # Invalidate related risk calculations
        if portfolio_id:
            self.invalidation.invalidate_risk_calculations(portfolio_id)
        
        logger.info(f"Invalidated cache for transaction: portfolio={portfolio_id}, asset={asset_id}")
    
    def on_market_data_updated(self, asset_id: str) -> None:
        """
        Handle cache invalidation when market data is updated
        
        Args:
            asset_id: Asset ID
        """
        # Invalidate market data cache
        self.invalidation.invalidate_market_data(asset_id)
        
        # Invalidate risk calculations that depend on this asset
        # This would require tracking which portfolios hold this asset
        logger.info(f"Invalidated cache for market data: asset={asset_id}")
    
    def on_risk_calculation_updated(self, entity_id: str, calculation_type: str) -> None:
        """
        Handle cache invalidation when risk calculation is updated
        
        Args:
            entity_id: Entity ID
            calculation_type: Type of calculation
        """
        key = CacheKeyBuilder.risk_calculation_key(entity_id, calculation_type)
        self.invalidation.invalidate_key(key)
        logger.info(f"Invalidated cache for risk calculation: entity={entity_id}, type={calculation_type}")
    
    def on_portfolio_updated(self, portfolio_id: str) -> None:
        """
        Handle cache invalidation when portfolio is updated
        
        Args:
            portfolio_id: Portfolio ID
        """
        # Invalidate portfolio cache
        self.invalidation.invalidate_portfolio(portfolio_id)
        
        # Invalidate risk calculations
        self.invalidation.invalidate_risk_calculations(portfolio_id)
        
        logger.info(f"Invalidated cache for portfolio: {portfolio_id}")


class CacheRefreshStrategy:
    """Strategies for refreshing stale cache"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    def refresh_on_access(
        self,
        key: str,
        loader: Callable,
        ttl: Optional[int] = None,
        threshold: float = 0.8
    ) -> Any:
        """
        Refresh cache on access if TTL is below threshold
        
        Args:
            key: Cache key
            loader: Function to load fresh data
            ttl: New TTL in seconds
            threshold: Refresh when remaining TTL is below this fraction
            
        Returns:
            Cached or refreshed value
        """
        # Get current value and TTL
        value = self.cache.get(key)
        current_ttl = self.cache.ttl(key)
        
        if value is None:
            # Cache miss - load and cache
            value = loader()
            if value is not None:
                self.cache.set(key, value, ttl)
            return value
        
        # Check if refresh is needed
        if current_ttl and ttl:
            remaining_fraction = current_ttl / ttl
            if remaining_fraction < threshold:
                # Refresh cache
                logger.debug(f"Refreshing cache key: {key} (TTL: {current_ttl}/{ttl})")
                fresh_value = loader()
                if fresh_value is not None:
                    self.cache.set(key, fresh_value, ttl)
                    return fresh_value
        
        return value
    
    def background_refresh(
        self,
        keys: List[str],
        loader_map: Dict[str, Callable],
        ttl_map: Dict[str, int]
    ) -> Dict[str, bool]:
        """
        Refresh multiple keys in background
        
        Args:
            keys: List of cache keys
            loader_map: Map of key to loader function
            ttl_map: Map of key to TTL
            
        Returns:
            Dictionary of key: success status
        """
        results = {}
        for key in keys:
            try:
                if key in loader_map:
                    value = loader_map[key]()
                    ttl = ttl_map.get(key)
                    success = self.cache.set(key, value, ttl)
                    results[key] = success
                else:
                    logger.warning(f"No loader found for key: {key}")
                    results[key] = False
            except Exception as e:
                logger.error(f"Failed to refresh key {key}: {e}")
                results[key] = False
        
        return results


class TimeBasedInvalidation:
    """Time-based cache invalidation"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.invalidation = CacheInvalidation(cache_service)
    
    def invalidate_expired(self) -> int:
        """
        Invalidate expired cache entries
        
        Returns:
            Number of keys invalidated
        """
        # Redis handles expiration automatically
        # This is a placeholder for custom expiration logic
        logger.info("Checking for expired cache entries")
        return 0
    
    def schedule_invalidation(self, key: str, delay_seconds: int) -> bool:
        """
        Schedule cache invalidation
        
        Args:
            key: Cache key
            delay_seconds: Delay before invalidation
            
        Returns:
            True if scheduled successfully
        """
        # Set expiration
        return self.cache.expire(key, delay_seconds)


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
        # Set some test data
        cache_service.set('market_data:AAPL:latest', {'price': 175.50}, ttl=300)
        cache_service.set('market_data:MSFT:latest', {'price': 380.25}, ttl=300)
        cache_service.set('portfolio:001', {'value': 1000000}, ttl=600)
        
        # Test invalidation
        invalidation = CacheInvalidation(cache_service)
        
        # Invalidate specific key
        invalidation.invalidate_key('portfolio:001')
        print("✓ Invalidated portfolio:001")
        
        # Invalidate pattern
        count = invalidation.invalidate_market_data()
        print(f"✓ Invalidated {count} market data keys")
        
        # Test selective invalidation
        selective = SelectiveInvalidation(cache_service)
        selective.on_portfolio_updated('001')
        print("✓ Handled portfolio update")
        
    finally:
        cache_service.close()

# Made with Bob
