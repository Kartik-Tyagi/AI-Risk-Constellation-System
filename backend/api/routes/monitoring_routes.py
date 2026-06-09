"""
Monitoring Routes
API endpoints for monitoring and observability
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query

from backend.services.metrics_collector import get_metrics_collector
from backend.services.health_check import get_health_check_service
from backend.api.dependencies import (
    get_postgres_dependency,
    get_neo4j_dependency,
    get_cache_dependency
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics")
async def get_metrics(
    period_minutes: int = Query(60, ge=1, le=1440, description="Time period in minutes")
):
    """
    Get application metrics
    
    Args:
        period_minutes: Time period for metrics
        
    Returns:
        Application metrics
    """
    try:
        metrics_collector = get_metrics_collector()
        
        return {
            'summary': metrics_collector.get_summary(),
            'requests': metrics_collector.get_request_metrics(period_minutes),
            'database': metrics_collector.get_database_metrics(period_minutes),
            'ml_inference': metrics_collector.get_ml_metrics(period_minutes),
            'endpoints': metrics_collector.get_endpoint_statistics()
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {
            'error': 'Failed to retrieve metrics',
            'message': str(e)
        }


@router.get("/metrics/requests")
async def get_request_metrics(
    period_minutes: int = Query(60, ge=1, le=1440, description="Time period in minutes")
):
    """
    Get request metrics
    
    Args:
        period_minutes: Time period for metrics
        
    Returns:
        Request metrics
    """
    try:
        metrics_collector = get_metrics_collector()
        return metrics_collector.get_request_metrics(period_minutes)
    except Exception as e:
        logger.error(f"Failed to get request metrics: {e}")
        return {
            'error': 'Failed to retrieve request metrics',
            'message': str(e)
        }


@router.get("/metrics/database")
async def get_database_metrics(
    period_minutes: int = Query(60, ge=1, le=1440, description="Time period in minutes")
):
    """
    Get database metrics
    
    Args:
        period_minutes: Time period for metrics
        
    Returns:
        Database metrics
    """
    try:
        metrics_collector = get_metrics_collector()
        return metrics_collector.get_database_metrics(period_minutes)
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        return {
            'error': 'Failed to retrieve database metrics',
            'message': str(e)
        }


@router.get("/metrics/ml")
async def get_ml_metrics(
    period_minutes: int = Query(60, ge=1, le=1440, description="Time period in minutes")
):
    """
    Get ML inference metrics
    
    Args:
        period_minutes: Time period for metrics
        
    Returns:
        ML inference metrics
    """
    try:
        metrics_collector = get_metrics_collector()
        return metrics_collector.get_ml_metrics(period_minutes)
    except Exception as e:
        logger.error(f"Failed to get ML metrics: {e}")
        return {
            'error': 'Failed to retrieve ML metrics',
            'message': str(e)
        }


@router.get("/metrics/endpoints")
async def get_endpoint_metrics():
    """
    Get endpoint statistics
    
    Returns:
        Endpoint statistics
    """
    try:
        metrics_collector = get_metrics_collector()
        return metrics_collector.get_endpoint_statistics()
    except Exception as e:
        logger.error(f"Failed to get endpoint metrics: {e}")
        return {
            'error': 'Failed to retrieve endpoint metrics',
            'message': str(e)
        }


@router.get("/health")
async def health_check(
    postgres=Depends(get_postgres_dependency),
    neo4j=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency)
):
    """
    Comprehensive health check
    
    Returns:
        System health status
    """
    try:
        health_service = get_health_check_service(postgres, neo4j, cache)
        return await health_service.check_all()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': 'Health check failed',
            'message': str(e)
        }


@router.get("/health/database")
async def database_health(
    postgres=Depends(get_postgres_dependency)
):
    """
    Database health check
    
    Returns:
        Database health status
    """
    try:
        health_service = get_health_check_service(postgres=postgres)
        return await health_service.check_database()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': 'Database health check failed',
            'message': str(e)
        }


@router.get("/health/graph")
async def graph_health(
    neo4j=Depends(get_neo4j_dependency)
):
    """
    Graph database health check
    
    Returns:
        Graph database health status
    """
    try:
        health_service = get_health_check_service(neo4j=neo4j)
        return await health_service.check_graph_database()
    except Exception as e:
        logger.error(f"Graph database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': 'Graph database health check failed',
            'message': str(e)
        }


@router.get("/health/cache")
async def cache_health(
    cache=Depends(get_cache_dependency)
):
    """
    Cache health check
    
    Returns:
        Cache health status
    """
    try:
        health_service = get_health_check_service(cache=cache)
        return await health_service.check_cache()
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': 'Cache health check failed',
            'message': str(e)
        }


@router.get("/health/ml")
async def ml_health():
    """
    ML models health check
    
    Returns:
        ML models health status
    """
    try:
        health_service = get_health_check_service()
        return await health_service.check_ml_models()
    except Exception as e:
        logger.error(f"ML health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': 'ML health check failed',
            'message': str(e)
        }


@router.get("/readiness")
async def readiness_check(
    postgres=Depends(get_postgres_dependency),
    neo4j=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency)
):
    """
    Kubernetes readiness probe
    
    Returns:
        Readiness status
    """
    try:
        health_service = get_health_check_service(postgres, neo4j, cache)
        return await health_service.get_readiness()
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            'ready': False,
            'error': str(e)
        }


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe
    
    Returns:
        Liveness status
    """
    try:
        health_service = get_health_check_service()
        return await health_service.get_liveness()
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return {
            'alive': False,
            'error': str(e)
        }


@router.get("/logs")
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs")
):
    """
    Get recent logs
    
    Args:
        level: Filter by log level
        limit: Maximum number of logs
        
    Returns:
        Recent logs
    """
    try:
        # TODO: Implement log retrieval from log files
        # For now, return placeholder
        return {
            'message': 'Log retrieval not yet implemented',
            'note': 'Logs are written to logs/app.log and logs/error.log'
        }
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        return {
            'error': 'Failed to retrieve logs',
            'message': str(e)
        }


@router.post("/metrics/reset")
async def reset_metrics():
    """
    Reset metrics (for testing/development)
    
    Returns:
        Reset confirmation
    """
    try:
        metrics_collector = get_metrics_collector()
        metrics_collector.reset_metrics()
        return {
            'message': 'Metrics reset successfully'
        }
    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}")
        return {
            'error': 'Failed to reset metrics',
            'message': str(e)
        }

# Made with Bob
