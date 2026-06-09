"""
FastAPI Application
Main entry point for the AI Risk Constellation System API
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

# Load .env from project root if present (before any other imports that read env vars)
_env_path = Path(__file__).resolve().parents[2] / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.api.routes import (
    portfolio_routes,
    risk_routes,
    graph_routes,
    market_routes,
    query_routes,
    monitoring_routes
)
from backend.api.error_handlers import (
    validation_exception_handler,
    general_exception_handler,
    http_exception_handler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting AI Risk Constellation System API...")
    logger.info("Initializing database connections...")
    logger.info("Loading ML models...")
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    logger.info("Closing database connections...")
    logger.info("API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="AI Risk Constellation System",
    description="Advanced risk analysis system using quantum-inspired optimization and graph neural networks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {process_time:.3f}s"
    )
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Error handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "name": "AI Risk Constellation System",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns system health status
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "api": "operational",
            "database": "operational",
            "cache": "operational",
            "ml_models": "operational"
        }
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with component status
    """
    # TODO: Add actual health checks for each component
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "api": {
                "status": "operational",
                "uptime": 0  # TODO: Track actual uptime
            },
            "postgresql": {
                "status": "operational",
                "connection_pool": {
                    "active": 0,
                    "idle": 0
                }
            },
            "neo4j": {
                "status": "operational",
                "connection_pool": {
                    "active": 0,
                    "idle": 0
                }
            },
            "redis": {
                "status": "operational",
                "memory_used_mb": 0,
                "hit_rate": 0
            },
            "ml_models": {
                "status": "operational",
                "loaded_models": []
            }
        }
    }


@app.get("/metrics", tags=["Health"])
async def metrics():
    """
    API metrics endpoint
    """
    return {
        "requests": {
            "total": 0,  # TODO: Track actual metrics
            "success": 0,
            "errors": 0
        },
        "response_times": {
            "avg_ms": 0,
            "p50_ms": 0,
            "p95_ms": 0,
            "p99_ms": 0
        },
        "cache": {
            "hit_rate": 0,
            "total_hits": 0,
            "total_misses": 0
        }
    }


# Include routers
app.include_router(
    portfolio_routes.router,
    prefix="/api/v1/portfolios",
    tags=["Portfolios"]
)

app.include_router(
    risk_routes.router,
    prefix="/api/v1/risk",
    tags=["Risk Analysis"]
)

app.include_router(
    graph_routes.router,
    prefix="/api/v1/graph",
    tags=["Graph Analysis"]
)

app.include_router(
    market_routes.router,
    prefix="/api/v1/market",
    tags=["Market Data"]
)

app.include_router(
    query_routes.router,
    prefix="/api/v1/query",
    tags=["Natural Language Query"]
)

app.include_router(
    monitoring_routes.router,
    prefix="/api/v1/monitoring",
    tags=["Monitoring"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Made with Bob
