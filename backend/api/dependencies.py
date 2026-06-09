"""
FastAPI Dependencies
Dependency injection for database connections, cache, and ML models
"""

import logging
from typing import Optional, Generator
from functools import lru_cache

from backend.connectors.postgres_connector import PostgreSQLConnector
from backend.connectors.neo4j_connector import Neo4jConnector
from backend.services.cache_service import CacheService

logger = logging.getLogger(__name__)


# Singleton instances
_postgres_connector: Optional[PostgreSQLConnector] = None
_neo4j_connector: Optional[Neo4jConnector] = None
_cache_service: Optional[CacheService] = None


@lru_cache()
def get_postgres_connector() -> PostgreSQLConnector:
    """
    Get PostgreSQL connector instance
    
    Returns:
        PostgreSQLConnector instance
    """
    global _postgres_connector
    
    if _postgres_connector is None:
        _postgres_connector = PostgreSQLConnector(
            host="localhost",
            port=5432,
            database="risk_constellation",
            user="postgres",
            password="postgres"
        )
        logger.info("PostgreSQL connector initialized")
    
    return _postgres_connector


@lru_cache()
def get_neo4j_connector() -> Neo4jConnector:
    """
    Get Neo4j connector instance
    
    Returns:
        Neo4jConnector instance
    """
    global _neo4j_connector
    
    if _neo4j_connector is None:
        _neo4j_connector = Neo4jConnector(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="neo4jpassword"
        )
        logger.info("Neo4j connector initialized")
    
    return _neo4j_connector


@lru_cache()
def get_cache_service() -> CacheService:
    """
    Get cache service instance
    
    Returns:
        CacheService instance
    """
    global _cache_service
    
    if _cache_service is None:
        _cache_service = CacheService(
            host="localhost",
            port=6379,
            db=0
        )
        logger.info("Cache service initialized")
    
    return _cache_service


def get_db_session() -> Generator:
    """
    Get database session
    Yields database connection and ensures cleanup
    """
    postgres = get_postgres_connector()
    try:
        yield postgres
    finally:
        # Connection cleanup handled by connector
        pass


def get_graph_session() -> Generator:
    """
    Get graph database session
    Yields Neo4j connection and ensures cleanup
    """
    neo4j = get_neo4j_connector()
    try:
        yield neo4j
    finally:
        # Connection cleanup handled by connector
        pass


def get_cache() -> Generator:
    """
    Get cache service
    Yields cache service instance
    """
    cache = get_cache_service()
    try:
        yield cache
    finally:
        # Cache connection handled by service
        pass


class MLModelDependency:
    """Dependency for ML models"""
    
    def __init__(self):
        self.models = {}
        self._load_models()
    
    def _load_models(self):
        """Load ML models"""
        try:
            # TODO: Load actual models
            logger.info("Loading ML models...")
            
            # Placeholder for model loading
            self.models = {
                "risk_calculator": None,
                "gat_model": None,
                "temporal_gnn": None,
                "risk_dna_generator": None
            }
            
            logger.info("ML models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            raise
    
    def get_risk_calculator(self):
        """Get risk calculator model"""
        return self.models.get("risk_calculator")
    
    def get_gat_model(self):
        """Get GAT model"""
        return self.models.get("gat_model")
    
    def get_temporal_gnn(self):
        """Get Temporal GNN model"""
        return self.models.get("temporal_gnn")
    
    def get_risk_dna_generator(self):
        """Get Risk DNA generator"""
        return self.models.get("risk_dna_generator")


# Singleton ML model dependency
_ml_models: Optional[MLModelDependency] = None


@lru_cache()
def get_ml_models() -> MLModelDependency:
    """
    Get ML models dependency
    
    Returns:
        MLModelDependency instance
    """
    global _ml_models
    
    if _ml_models is None:
        _ml_models = MLModelDependency()
        logger.info("ML models dependency initialized")
    
    return _ml_models


def cleanup_dependencies():
    """
    Cleanup all dependencies
    Called on application shutdown
    """
    global _postgres_connector, _neo4j_connector, _cache_service, _ml_models
    
    logger.info("Cleaning up dependencies...")
    
    if _postgres_connector:
        _postgres_connector.close()
        _postgres_connector = None
        logger.info("PostgreSQL connector closed")
    
    if _neo4j_connector:
        _neo4j_connector.close()
        _neo4j_connector = None
        logger.info("Neo4j connector closed")
    
    if _cache_service:
        _cache_service.close()
        _cache_service = None
        logger.info("Cache service closed")
    
    if _ml_models:
        _ml_models = None
        logger.info("ML models unloaded")
    
    logger.info("Dependencies cleanup complete")


# Dependency functions for FastAPI
async def get_postgres_dependency():
    """Async dependency for PostgreSQL"""
    return get_postgres_connector()


async def get_neo4j_dependency():
    """Async dependency for Neo4j"""
    return get_neo4j_connector()


async def get_cache_dependency():
    """Async dependency for cache"""
    return get_cache_service()


async def get_ml_models_dependency():
    """Async dependency for ML models"""
    return get_ml_models()

# Made with Bob
