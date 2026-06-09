"""
Health Check Service
Performs health checks on system components
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from backend.connectors.postgres_connector import PostgreSQLConnector
from backend.connectors.neo4j_connector import Neo4jConnector
from backend.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckService:
    """Performs health checks on system components"""
    
    def __init__(
        self,
        postgres: Optional[PostgreSQLConnector] = None,
        neo4j: Optional[Neo4jConnector] = None,
        cache: Optional[CacheService] = None
    ):
        self.postgres = postgres
        self.neo4j = neo4j
        self.cache = cache
    
    async def check_database(self) -> Dict[str, Any]:
        """
        Check PostgreSQL database health
        
        Returns:
            Database health status
        """
        if not self.postgres:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'message': 'Database connector not initialized',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Test connection
            is_connected = self.postgres.test_connection()
            
            if is_connected:
                # Get connection pool stats if method exists
                pool_stats = {}
                if hasattr(self.postgres, 'get_pool_stats'):
                    pool_stats = self.postgres.get_pool_stats()
                
                return {
                    'status': HealthStatus.HEALTHY.value,
                    'message': 'Database is healthy',
                    'connection_pool': pool_stats,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': HealthStatus.UNHEALTHY.value,
                    'message': 'Database connection failed',
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'Database health check error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_graph_database(self) -> Dict[str, Any]:
        """
        Check Neo4j graph database health
        
        Returns:
            Graph database health status
        """
        if not self.neo4j:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'message': 'Graph database connector not initialized',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Test connection
            is_connected = self.neo4j.test_connection()
            
            if is_connected:
                # Get database info if method exists
                db_info = {}
                if hasattr(self.neo4j, 'get_database_info'):
                    db_info = self.neo4j.get_database_info()
                
                return {
                    'status': HealthStatus.HEALTHY.value,
                    'message': 'Graph database is healthy',
                    'database_info': db_info,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': HealthStatus.UNHEALTHY.value,
                    'message': 'Graph database connection failed',
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Graph database health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'Graph database health check error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_cache(self) -> Dict[str, Any]:
        """
        Check Redis cache health
        
        Returns:
            Cache health status
        """
        if not self.cache:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'message': 'Cache service not initialized',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Test connection
            is_connected = self.cache.test_connection()
            
            if is_connected:
                # Get cache stats
                stats = self.cache.get_stats()
                info = self.cache.get_info()
                
                # Check memory usage
                memory_used_mb = info.get('used_memory', 0) / (1024 * 1024)
                memory_max_mb = info.get('maxmemory', 0) / (1024 * 1024)
                
                status = HealthStatus.HEALTHY
                if memory_max_mb > 0 and memory_used_mb / memory_max_mb > 0.9:
                    status = HealthStatus.DEGRADED
                
                return {
                    'status': status.value,
                    'message': 'Cache is healthy' if status == HealthStatus.HEALTHY else 'Cache memory usage high',
                    'stats': stats,
                    'memory_used_mb': round(memory_used_mb, 2),
                    'memory_max_mb': round(memory_max_mb, 2) if memory_max_mb > 0 else None,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': HealthStatus.UNHEALTHY.value,
                    'message': 'Cache connection failed',
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'Cache health check error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_ml_models(self) -> Dict[str, Any]:
        """
        Check ML models health
        
        Returns:
            ML models health status
        """
        try:
            # TODO: Implement actual ML model health checks
            # For now, return placeholder
            
            models_status = {
                'risk_calculator': {'loaded': False, 'status': 'not_loaded'},
                'gat_model': {'loaded': False, 'status': 'not_loaded'},
                'temporal_gnn': {'loaded': False, 'status': 'not_loaded'},
                'risk_dna_generator': {'loaded': False, 'status': 'not_loaded'}
            }
            
            # Check if any models are loaded
            any_loaded = any(m['loaded'] for m in models_status.values())
            
            return {
                'status': HealthStatus.DEGRADED.value if not any_loaded else HealthStatus.HEALTHY.value,
                'message': 'ML models not loaded' if not any_loaded else 'ML models are healthy',
                'models': models_status,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"ML models health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'ML models health check error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_all(self) -> Dict[str, Any]:
        """
        Perform all health checks
        
        Returns:
            Complete health status
        """
        database_health = await self.check_database()
        graph_health = await self.check_graph_database()
        cache_health = await self.check_cache()
        ml_health = await self.check_ml_models()
        
        # Determine overall status
        statuses = [
            database_health['status'],
            graph_health['status'],
            cache_health['status'],
            ml_health['status']
        ]
        
        if any(s == HealthStatus.UNHEALTHY.value for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED.value for s in statuses):
            overall_status = HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY.value for s in statuses):
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'components': {
                'database': database_health,
                'graph_database': graph_health,
                'cache': cache_health,
                'ml_models': ml_health
            }
        }
    
    async def get_readiness(self) -> Dict[str, Any]:
        """
        Check if system is ready to serve requests
        
        Returns:
            Readiness status
        """
        health = await self.check_all()
        
        # System is ready if not unhealthy
        is_ready = health['status'] != HealthStatus.UNHEALTHY.value
        
        return {
            'ready': is_ready,
            'status': health['status'],
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_liveness(self) -> Dict[str, Any]:
        """
        Check if system is alive
        
        Returns:
            Liveness status
        """
        # Simple liveness check - if we can respond, we're alive
        return {
            'alive': True,
            'timestamp': datetime.now().isoformat()
        }


# Global health check service instance
_health_check_service: Optional[HealthCheckService] = None


def get_health_check_service(
    postgres: Optional[PostgreSQLConnector] = None,
    neo4j: Optional[Neo4jConnector] = None,
    cache: Optional[CacheService] = None
) -> HealthCheckService:
    """
    Get health check service instance
    
    Args:
        postgres: PostgreSQL connector
        neo4j: Neo4j connector
        cache: Cache service
        
    Returns:
        HealthCheckService instance
    """
    global _health_check_service
    
    if _health_check_service is None:
        _health_check_service = HealthCheckService(postgres, neo4j, cache)
    
    return _health_check_service

# Made with Bob
