"""
Cache Monitor
Monitors cache performance metrics including hit/miss rates and size
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from backend.services.cache_service import CacheService

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    timestamp: str
    total_hits: int
    total_misses: int
    hit_rate: float
    total_keys: int
    memory_used_bytes: int
    memory_used_mb: float
    evicted_keys: int
    expired_keys: int
    avg_ttl: float


class CacheMonitor:
    """Monitors cache performance and health"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.metrics_history: List[CacheMetrics] = []
        self.max_history = 1000
    
    def get_current_metrics(self) -> CacheMetrics:
        """
        Get current cache metrics
        
        Returns:
            CacheMetrics object
        """
        try:
            # Get Redis info
            stats = self.cache.get_stats()
            info = self.cache.get_info()
            
            # Calculate metrics
            hits = stats.get('keyspace_hits', 0)
            misses = stats.get('keyspace_misses', 0)
            hit_rate = stats.get('hit_rate', 0.0)
            
            # Memory info
            memory_used = info.get('used_memory', 0)
            memory_used_mb = memory_used / (1024 * 1024)
            
            # Keyspace info
            total_keys = 0
            if 'db0' in info:
                db_info = info['db0']
                if isinstance(db_info, dict):
                    total_keys = db_info.get('keys', 0)
            
            # Eviction and expiration
            evicted = info.get('evicted_keys', 0)
            expired = info.get('expired_keys', 0)
            
            metrics = CacheMetrics(
                timestamp=datetime.now().isoformat(),
                total_hits=hits,
                total_misses=misses,
                hit_rate=hit_rate,
                total_keys=total_keys,
                memory_used_bytes=memory_used,
                memory_used_mb=round(memory_used_mb, 2),
                evicted_keys=evicted,
                expired_keys=expired,
                avg_ttl=0.0  # Would need custom tracking
            )
            
            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get cache metrics: {e}")
            return CacheMetrics(
                timestamp=datetime.now().isoformat(),
                total_hits=0,
                total_misses=0,
                hit_rate=0.0,
                total_keys=0,
                memory_used_bytes=0,
                memory_used_mb=0.0,
                evicted_keys=0,
                expired_keys=0,
                avg_ttl=0.0
            )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of cache metrics
        
        Returns:
            Dictionary with metric summaries
        """
        current = self.get_current_metrics()
        
        return {
            'current': asdict(current),
            'health_status': self._assess_health(current),
            'recommendations': self._get_recommendations(current)
        }
    
    def _assess_health(self, metrics: CacheMetrics) -> str:
        """
        Assess cache health based on metrics
        
        Args:
            metrics: Current metrics
            
        Returns:
            Health status string
        """
        if metrics.hit_rate >= 80:
            return 'excellent'
        elif metrics.hit_rate >= 60:
            return 'good'
        elif metrics.hit_rate >= 40:
            return 'fair'
        else:
            return 'poor'
    
    def _get_recommendations(self, metrics: CacheMetrics) -> List[str]:
        """
        Get recommendations based on metrics
        
        Args:
            metrics: Current metrics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if metrics.hit_rate < 50:
            recommendations.append("Low hit rate detected. Consider warming cache or adjusting TTL strategies.")
        
        if metrics.memory_used_mb > 1000:  # > 1GB
            recommendations.append("High memory usage. Consider implementing eviction policies.")
        
        if metrics.evicted_keys > 1000:
            recommendations.append("High eviction rate. Consider increasing cache size or reducing TTL.")
        
        if metrics.total_keys > 100000:
            recommendations.append("Large number of keys. Consider implementing key namespacing and cleanup.")
        
        return recommendations
    
    def get_hit_miss_ratio(self) -> Dict[str, float]:
        """
        Get hit/miss ratio
        
        Returns:
            Dictionary with hit/miss statistics
        """
        metrics = self.get_current_metrics()
        total = metrics.total_hits + metrics.total_misses
        
        if total == 0:
            return {
                'hit_rate': 0.0,
                'miss_rate': 0.0,
                'total_requests': 0
            }
        
        return {
            'hit_rate': (metrics.total_hits / total) * 100,
            'miss_rate': (metrics.total_misses / total) * 100,
            'total_requests': total
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage statistics
        
        Returns:
            Dictionary with memory statistics
        """
        metrics = self.get_current_metrics()
        info = self.cache.get_info()
        
        return {
            'used_memory_mb': metrics.memory_used_mb,
            'used_memory_bytes': metrics.memory_used_bytes,
            'peak_memory_mb': info.get('used_memory_peak', 0) / (1024 * 1024),
            'memory_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0),
            'total_keys': metrics.total_keys
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics
        
        Returns:
            Dictionary with performance metrics
        """
        metrics = self.get_current_metrics()
        info = self.cache.get_info()
        
        return {
            'hit_rate': metrics.hit_rate,
            'total_hits': metrics.total_hits,
            'total_misses': metrics.total_misses,
            'evicted_keys': metrics.evicted_keys,
            'expired_keys': metrics.expired_keys,
            'ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
            'connected_clients': info.get('connected_clients', 0)
        }
    
    def get_trend_analysis(self, minutes: int = 60) -> Dict[str, Any]:
        """
        Analyze trends over time
        
        Args:
            minutes: Number of minutes to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        if not self.metrics_history:
            return {'error': 'No historical data available'}
        
        # Filter recent metrics
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if not recent_metrics:
            return {'error': 'No recent data available'}
        
        # Calculate trends
        hit_rates = [m.hit_rate for m in recent_metrics]
        memory_usage = [m.memory_used_mb for m in recent_metrics]
        
        return {
            'period_minutes': minutes,
            'data_points': len(recent_metrics),
            'hit_rate': {
                'min': min(hit_rates),
                'max': max(hit_rates),
                'avg': sum(hit_rates) / len(hit_rates),
                'current': hit_rates[-1] if hit_rates else 0
            },
            'memory_usage_mb': {
                'min': min(memory_usage),
                'max': max(memory_usage),
                'avg': sum(memory_usage) / len(memory_usage),
                'current': memory_usage[-1] if memory_usage else 0
            }
        }
    
    def check_health(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Dictionary with health check results
        """
        try:
            # Test connection
            is_connected = self.cache.test_connection()
            
            # Get metrics
            metrics = self.get_current_metrics()
            
            # Assess health
            health_status = self._assess_health(metrics)
            
            return {
                'healthy': is_connected and health_status in ['excellent', 'good'],
                'connected': is_connected,
                'status': health_status,
                'hit_rate': metrics.hit_rate,
                'memory_used_mb': metrics.memory_used_mb,
                'total_keys': metrics.total_keys,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'healthy': False,
                'connected': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive monitoring report
        
        Returns:
            Dictionary with complete report
        """
        return {
            'summary': self.get_metrics_summary(),
            'hit_miss_ratio': self.get_hit_miss_ratio(),
            'memory_usage': self.get_memory_usage(),
            'performance': self.get_performance_metrics(),
            'trend_analysis': self.get_trend_analysis(60),
            'health_check': self.check_health()
        }


class CacheAlerts:
    """Alert system for cache issues"""
    
    def __init__(self, monitor: CacheMonitor):
        self.monitor = monitor
        self.thresholds = {
            'min_hit_rate': 50.0,
            'max_memory_mb': 1000.0,
            'max_eviction_rate': 100,
            'max_keys': 100000
        }
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for alert conditions
        
        Returns:
            List of active alerts
        """
        alerts = []
        metrics = self.monitor.get_current_metrics()
        
        # Low hit rate alert
        if metrics.hit_rate < self.thresholds['min_hit_rate']:
            alerts.append({
                'severity': 'warning',
                'type': 'low_hit_rate',
                'message': f"Cache hit rate is {metrics.hit_rate:.1f}% (threshold: {self.thresholds['min_hit_rate']}%)",
                'value': metrics.hit_rate,
                'threshold': self.thresholds['min_hit_rate']
            })
        
        # High memory usage alert
        if metrics.memory_used_mb > self.thresholds['max_memory_mb']:
            alerts.append({
                'severity': 'warning',
                'type': 'high_memory_usage',
                'message': f"Cache memory usage is {metrics.memory_used_mb:.1f}MB (threshold: {self.thresholds['max_memory_mb']}MB)",
                'value': metrics.memory_used_mb,
                'threshold': self.thresholds['max_memory_mb']
            })
        
        # High eviction rate alert
        if metrics.evicted_keys > self.thresholds['max_eviction_rate']:
            alerts.append({
                'severity': 'warning',
                'type': 'high_eviction_rate',
                'message': f"High cache eviction rate: {metrics.evicted_keys} keys evicted",
                'value': metrics.evicted_keys,
                'threshold': self.thresholds['max_eviction_rate']
            })
        
        # Too many keys alert
        if metrics.total_keys > self.thresholds['max_keys']:
            alerts.append({
                'severity': 'info',
                'type': 'high_key_count',
                'message': f"Large number of cache keys: {metrics.total_keys}",
                'value': metrics.total_keys,
                'threshold': self.thresholds['max_keys']
            })
        
        return alerts


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
        # Initialize monitor
        monitor = CacheMonitor(cache_service)
        
        # Get current metrics
        metrics = monitor.get_current_metrics()
        print(f"✓ Current metrics:")
        print(f"  Hit rate: {metrics.hit_rate:.1f}%")
        print(f"  Memory used: {metrics.memory_used_mb:.2f}MB")
        print(f"  Total keys: {metrics.total_keys}")
        
        # Get summary
        summary = monitor.get_metrics_summary()
        print(f"\n✓ Health status: {summary['health_status']}")
        
        if summary['recommendations']:
            print("\n✓ Recommendations:")
            for rec in summary['recommendations']:
                print(f"  - {rec}")
        
        # Check alerts
        alerts_system = CacheAlerts(monitor)
        alerts = alerts_system.check_alerts()
        if alerts:
            print(f"\n⚠ Active alerts: {len(alerts)}")
            for alert in alerts:
                print(f"  [{alert['severity']}] {alert['message']}")
        else:
            print("\n✓ No active alerts")
        
    finally:
        cache_service.close()

# Made with Bob
