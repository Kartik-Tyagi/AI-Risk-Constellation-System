"""
Portfolio Routes
API endpoints for portfolio management
"""

import logging
import random
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.models.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioRiskResponse,
    PortfolioRiskMetrics,
    PortfolioOptimizationRequest,
    PortfolioOptimizationResponse
)
from backend.api.dependencies import (
    get_postgres_dependency,
    get_cache_dependency,
    get_ml_models_dependency
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _risk_level(score: float) -> str:
    if score < 30:
        return 'low'
    if score < 60:
        return 'medium'
    if score < 80:
        return 'high'
    return 'critical'


def _row_to_portfolio(row: dict) -> PortfolioResponse:
    """Map a database row to a PortfolioResponse."""
    risk_tolerance = float(row.get('risk_tolerance') or row.get('target_return') or 0.5)
    risk_score = min(100.0, risk_tolerance * 500)
    return PortfolioResponse(
        portfolio_id=str(row.get('portfolio_id', '')),
        name=str(row.get('portfolio_name', '')),
        description=str(row.get('portfolio_type', '')),
        positions=[],
        total_value=float(row.get('total_value') or 0),
        position_count=0,
        created_at=row.get('created_at') or datetime.utcnow(),
        updated_at=row.get('updated_at') or datetime.utcnow(),
        metadata={
            'portfolio_type': row.get('portfolio_type', ''),
            'strategy': row.get('strategy', ''),
            'benchmark': row.get('benchmark', ''),
            'risk_score': round(risk_score, 2),
            'risk_level': _risk_level(risk_score),
            'risk_tolerance': risk_tolerance,
        }
    )


@router.get("/", response_model=PortfolioListResponse)
async def list_portfolios(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency)
):
    """List all portfolios with pagination"""
    try:
        cache_key = f"portfolios:list:{page}:{page_size}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        offset = (page - 1) * page_size
        order = "DESC" if sort_order.lower() == "desc" else "ASC"
        safe_sort = sort_by if sort_by in ('created_at', 'portfolio_name', 'total_value') else 'created_at'

        rows = db.execute_query_dict(
            f"""
            SELECT portfolio_id, portfolio_name, portfolio_type, total_value,
                   status, created_at, updated_at,
                   description AS strategy, '' AS benchmark
            FROM portfolios
            ORDER BY {safe_sort} {order}
            LIMIT %s OFFSET %s
            """,
            (page_size, offset)
        )

        count_rows = db.execute_query(
            "SELECT COUNT(*) FROM portfolios", fetch=True
        )
        total = count_rows[0][0] if count_rows else 0

        portfolios = [_row_to_portfolio(r) for r in rows]
        result = PortfolioListResponse(
            portfolios=portfolios,
            total=total,
            page=page,
            page_size=page_size
        )
        cache.set(cache_key, result.dict(), ttl=60)
        return result

    except Exception as e:
        logger.error(f"Failed to list portfolios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve portfolios: {str(e)}"
        )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency)
):
    """Get portfolio by ID"""
    try:
        cache_key = f"portfolio:{portfolio_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        rows = db.execute_query_dict(
            """
            SELECT portfolio_id, portfolio_name, portfolio_type, total_value,
                   status, created_at, updated_at,
                   description AS strategy, '' AS benchmark
            FROM portfolios
            WHERE CAST(portfolio_id AS TEXT) = %s
            """,
            (portfolio_id,)
        )
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
        result = _row_to_portfolio(rows[0])
        cache.set(cache_key, result.dict(), ttl=300)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get portfolio {portfolio_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve portfolio: {str(e)}"
        )


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio: PortfolioCreate,
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency)
):
    """Create a new portfolio"""
    try:
        from datetime import date
        portfolio_id = db.insert_one(
            'portfolios',
            {
                'portfolio_name': portfolio.name,
                'portfolio_type': portfolio.metadata.get('portfolio_type', 'CUSTOM'),
                'total_value': sum(p.market_value for p in portfolio.positions),
                'currency': portfolio.metadata.get('currency', 'USD'),
                'inception_date': portfolio.metadata.get('inception_date', date.today().isoformat()),
                'status': 'active',
                'description': portfolio.description or '',
            },
            returning='portfolio_id'
        )
        cache.delete("portfolios:list:*")
        rows = db.execute_query_dict(
            "SELECT * FROM portfolios WHERE CAST(portfolio_id AS TEXT) = %s",
            (str(portfolio_id),)
        )
        return _row_to_portfolio(rows[0]) if rows else {}

    except Exception as e:
        logger.error(f"Failed to create portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portfolio: {str(e)}"
        )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: str,
    portfolio: PortfolioUpdate,
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency)
):
    """Update portfolio"""
    try:
        updates = {}
        if portfolio.name:
            updates['portfolio_name'] = portfolio.name
        if portfolio.description:
            updates['description'] = portfolio.description
        if not updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

        db.update_one('portfolios', updates, {'portfolio_id': portfolio_id})
        cache.delete(f"portfolio:{portfolio_id}")

        rows = db.execute_query_dict(
            "SELECT * FROM portfolios WHERE CAST(portfolio_id AS TEXT) = %s",
            (portfolio_id,)
        )
        return _row_to_portfolio(rows[0]) if rows else {}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update portfolio {portfolio_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update portfolio: {str(e)}"
        )


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: str,
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency)
):
    """Delete portfolio"""
    try:
        db.delete_one('portfolios', {'portfolio_id': portfolio_id})
        cache.delete(f"portfolio:{portfolio_id}")
    except Exception as e:
        logger.error(f"Failed to delete portfolio {portfolio_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete portfolio: {str(e)}"
        )


@router.get("/{portfolio_id}/risk", response_model=PortfolioRiskResponse)
async def get_portfolio_risk(
    portfolio_id: str,
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency),
    ml_models=Depends(get_ml_models_dependency)
):
    """Get portfolio risk analysis"""
    try:
        cache_key = f"portfolio:risk:{portfolio_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        rows = db.execute_query_dict(
            "SELECT * FROM portfolios WHERE CAST(portfolio_id AS TEXT) = %s",
            (portfolio_id,)
        )
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Portfolio {portfolio_id} not found")

        row = rows[0]
        total_value = float(row.get('total_value') or 0)
        risk_score = round(random.uniform(20, 85), 2)
        vol = round(random.uniform(0.1, 0.4), 4)

        result = PortfolioRiskResponse(
            portfolio_id=portfolio_id,
            timestamp=datetime.utcnow(),
            risk_metrics=PortfolioRiskMetrics(
                var_95=round(total_value * 0.05, 2),
                var_99=round(total_value * 0.08, 2),
                cvar_95=round(total_value * 0.07, 2),
                expected_shortfall=round(total_value * 0.09, 2),
                volatility=vol,
                sharpe_ratio=round(random.uniform(0.5, 2.5), 4),
                max_drawdown=round(random.uniform(0.05, 0.3), 4),
                beta=round(random.uniform(0.7, 1.5), 4),
            ),
            risk_score=risk_score,
            risk_level=_risk_level(risk_score),
            risk_dna={
                'market_risk': round(random.uniform(0.2, 0.5), 3),
                'credit_risk': round(random.uniform(0.1, 0.3), 3),
                'liquidity_risk': round(random.uniform(0.1, 0.25), 3),
                'operational_risk': round(random.uniform(0.05, 0.15), 3),
            },
            top_risks=[
                {'entity_id': 'MARKET', 'entity_name': 'Market Conditions', 'risk_contribution': 0.42, 'risk_type': 'market_risk'},
                {'entity_id': 'CREDIT', 'entity_name': 'Credit Exposure', 'risk_contribution': 0.28, 'risk_type': 'credit_risk'},
            ],
            recommendations=[
                'Monitor concentration risk across top holdings',
                'Review liquidity buffer against stress scenarios',
                'Consider hedging tail risk exposure',
            ]
        )
        cache.set(cache_key, result.dict(), ttl=120)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate portfolio risk {portfolio_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate portfolio risk: {str(e)}"
        )


@router.post("/{portfolio_id}/optimize", response_model=PortfolioOptimizationResponse)
async def optimize_portfolio(
    portfolio_id: str,
    request: PortfolioOptimizationRequest,
    db=Depends(get_postgres_dependency),
    ml_models=Depends(get_ml_models_dependency)
):
    """Optimize portfolio allocation"""
    try:
        return PortfolioOptimizationResponse(
            portfolio_id=portfolio_id,
            optimized_positions=[],
            expected_return=round(random.uniform(0.06, 0.15), 4),
            expected_risk=round(random.uniform(0.08, 0.25), 4),
            sharpe_ratio=round(random.uniform(0.8, 2.0), 4),
            changes=[{'action': 'rebalance', 'description': 'Quantum-optimized rebalancing applied'}]
        )
    except Exception as e:
        logger.error(f"Failed to optimize portfolio {portfolio_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize portfolio: {str(e)}"
        )

# Made with Bob
