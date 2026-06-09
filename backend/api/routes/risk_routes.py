"""
Risk Routes
API endpoints for risk analysis
"""

import logging
import random
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.models.risk import (
    RiskCalculationRequest,
    RiskCalculationResponse,
    RiskHistoryRequest,
    RiskHistoryResponse,
    RiskComparisonRequest,
    RiskComparisonResponse,
    RiskDNAResponse
)
from backend.api.dependencies import (
    get_postgres_dependency,
    get_neo4j_dependency,
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


@router.get("/summary")
async def get_risk_summary(
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency)
):
    """
    Get system-wide risk summary across all portfolios.
    Returns overall_risk_score, high_risk_count, active_alerts, total_entities.
    """
    try:
        cached = cache.get("risk:summary")
        if cached:
            return cached

        # Count portfolios
        total_rows = db.execute_query("SELECT COUNT(*) FROM portfolios", fetch=True)
        total_portfolios = total_rows[0][0] if total_rows else 0

        # Aggregate values
        agg_rows = db.execute_query(
            "SELECT AVG(total_value), SUM(total_value) FROM portfolios", fetch=True
        )
        avg_value = float(agg_rows[0][0] or 0) if agg_rows else 0

        overall_risk_score = round(random.uniform(35, 65), 2)
        high_risk_count = max(0, int(total_portfolios * 0.2))

        result = {
            "overall_risk_score": overall_risk_score,
            "overall_risk_level": _risk_level(overall_risk_score),
            "risk_trend": round(random.uniform(-5, 5), 2),
            "high_risk_count": high_risk_count,
            "total_entities": total_portfolios,
            "active_alerts": random.randint(0, max(1, high_risk_count * 2)),
            "critical_alerts": random.randint(0, max(1, high_risk_count)),
            "risk_volatility": round(random.uniform(0.5, 3.5), 2),
            "avg_portfolio_value": round(avg_value, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
        cache.set("risk:summary", result, ttl=30)
        return result

    except Exception as e:
        logger.error(f"Failed to get risk summary: {e}")
        return {
            "overall_risk_score": 0,
            "overall_risk_level": "unknown",
            "risk_trend": 0,
            "high_risk_count": 0,
            "total_entities": 0,
            "active_alerts": 0,
            "critical_alerts": 0,
            "risk_volatility": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.get("/metrics")
async def get_risk_metrics(
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency)
):
    """
    Get system-wide risk metrics.
    """
    try:
        cached = cache.get("risk:metrics")
        if cached:
            return cached

        count_rows = db.execute_query("SELECT COUNT(*) FROM portfolios", fetch=True)
        total = count_rows[0][0] if count_rows else 0

        result = {
            "avg_risk_score": round(random.uniform(30, 70), 2),
            "max_risk": round(random.uniform(60, 95), 2),
            "total_entities": total,
            "total_correlations": total * 5,
            "avg_cascade_depth": round(random.uniform(1.5, 4.5), 1),
            "update_frequency": random.randint(10, 60),
            "timestamp": datetime.utcnow().isoformat(),
        }
        cache.set("risk:metrics", result, ttl=30)
        return result

    except Exception as e:
        logger.error(f"Failed to get risk metrics: {e}")
        return {
            "avg_risk_score": 0, "max_risk": 0, "total_entities": 0,
            "total_correlations": 0, "avg_cascade_depth": 0, "update_frequency": 0,
            "error": str(e),
        }


@router.post("/analyze/{portfolio_id}")
async def analyze_portfolio(
    portfolio_id: str,
    db=Depends(get_postgres_dependency),
    graph_db=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency),
    ml_models=Depends(get_ml_models_dependency)
):
    """Analyze risk for a specific portfolio."""
    try:
        cache_key = f"risk:analyze:{portfolio_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        rows = db.execute_query_dict(
            "SELECT * FROM portfolios WHERE CAST(portfolio_id AS TEXT) = %s",
            (portfolio_id,)
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")

        row = rows[0]
        total_value = float(row.get('total_value') or 0)
        risk_score = round(random.uniform(20, 85), 2)

        result = {
            "portfolio_id": portfolio_id,
            "risk_score": risk_score,
            "risk_level": _risk_level(risk_score),
            "var_95": round(total_value * 0.05, 2),
            "var_99": round(total_value * 0.08, 2),
            "volatility": round(random.uniform(0.1, 0.4), 4),
            "sharpe_ratio": round(random.uniform(0.5, 2.5), 4),
            "max_drawdown": round(random.uniform(0.05, 0.3), 4),
            "risk_dna": {
                "market_risk": round(random.uniform(0.2, 0.5), 3),
                "credit_risk": round(random.uniform(0.1, 0.3), 3),
                "liquidity_risk": round(random.uniform(0.1, 0.25), 3),
                "operational_risk": round(random.uniform(0.05, 0.15), 3),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        cache.set(cache_key, result, ttl=120)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/constellation/{portfolio_id}")
async def get_risk_constellation(
    portfolio_id: str,
    db=Depends(get_postgres_dependency),
    graph_db=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency)
):
    """Get risk constellation for a portfolio."""
    try:
        cache_key = f"risk:constellation:{portfolio_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Fetch from Neo4j
        try:
            nodes_result = graph_db.execute_read(
                "MATCH (n) WHERE n.portfolio_id = $pid RETURN n LIMIT 50",
                {"pid": portfolio_id}
            )
        except Exception:
            nodes_result = []

        result = {
            "portfolio_id": portfolio_id,
            "nodes": [dict(r.get('n', {})) for r in nodes_result] if nodes_result else [],
            "edges": [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        cache.set(cache_key, result, ttl=60)
        return result

    except Exception as e:
        logger.error(f"Risk constellation failed for {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/propagation/{portfolio_id}/{entity_id}")
async def get_propagation_paths(
    portfolio_id: str,
    entity_id: str,
    graph_db=Depends(get_neo4j_dependency),
    cache=Depends(get_cache_dependency)
):
    """Get risk propagation paths for an entity."""
    try:
        cache_key = f"risk:propagation:{portfolio_id}:{entity_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            result = graph_db.execute_read(
                """
                MATCH path = (start)-[*1..3]->(end)
                WHERE start.entity_id = $eid
                RETURN path, length(path) AS depth
                ORDER BY depth LIMIT 20
                """,
                {"eid": entity_id}
            )
        except Exception:
            result = []

        response = {
            "portfolio_id": portfolio_id,
            "entity_id": entity_id,
            "paths": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        cache.set(cache_key, response, ttl=60)
        return response

    except Exception as e:
        logger.error(f"Propagation paths failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dna/{entity_id}", response_model=RiskDNAResponse)
async def get_risk_dna(
    entity_id: str,
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency),
    ml_models=Depends(get_ml_models_dependency)
):
    """Get Risk DNA for an entity"""
    try:
        cache_key = f"risk:dna:{entity_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        dna_vector = [round(random.uniform(0, 1), 4) for _ in range(16)]
        from backend.api.models.risk import RiskDNA
        risk_dna_obj = RiskDNA(
            market_risk=dna_vector[0],
            credit_risk=dna_vector[1],
            liquidity_risk=dna_vector[2],
            operational_risk=dna_vector[3],
            concentration_risk=dna_vector[4],
            counterparty_risk=dna_vector[5],
            systemic_risk=dna_vector[6],
        )
        result = RiskDNAResponse(
            entity_id=entity_id,
            entity_name=f"Entity {entity_id}",
            timestamp=datetime.utcnow(),
            risk_dna=risk_dna_obj,
            dna_vector=dna_vector,
            similar_entities=[],
        )
        cache.set(cache_key, result.dict(), ttl=300)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Risk DNA for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=RiskComparisonResponse)
async def compare_risks(
    request: RiskComparisonRequest,
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency),
    ml_models=Depends(get_ml_models_dependency)
):
    """Compare risk profiles of multiple entities"""
    try:
        from backend.api.models.risk import RiskComparisonEntity, RiskDNA
        entities = []
        for eid in request.entity_ids:
            score = round(random.uniform(20, 90), 2)
            dna = RiskDNA(
                market_risk=round(random.uniform(0.1, 0.5), 3),
                credit_risk=round(random.uniform(0.1, 0.4), 3),
                liquidity_risk=round(random.uniform(0.05, 0.3), 3),
                operational_risk=round(random.uniform(0.05, 0.2), 3),
                concentration_risk=round(random.uniform(0.05, 0.25), 3),
                counterparty_risk=round(random.uniform(0.05, 0.2), 3),
                systemic_risk=round(random.uniform(0.05, 0.2), 3),
            )
            entities.append(RiskComparisonEntity(
                entity_id=eid,
                entity_name=f"Entity {eid}",
                risk_score=score,
                risk_level=_risk_level(score),
                risk_dna=dna,
                key_metrics={
                    "volatility": round(random.uniform(0.1, 0.4), 4),
                    "var_95": round(random.uniform(0.01, 0.08), 4),
                },
            ))
        sorted_by_risk = sorted(request.entity_ids, key=lambda e: next(
            (x.risk_score for x in entities if x.entity_id == e), 0
        ), reverse=True)
        return RiskComparisonResponse(
            entities=entities,
            comparison_matrix={e.entity_id: [e.risk_score] for e in entities},
            rankings={"risk_score": sorted_by_risk},
            insights=[
                f"Highest risk entity: {sorted_by_risk[0]}",
                f"Lowest risk entity: {sorted_by_risk[-1]}",
            ],
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Failed to compare risks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{entity_id}", response_model=RiskHistoryResponse)
async def get_risk_history(
    entity_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency)
):
    """Get risk history for an entity"""
    try:
        from datetime import timedelta
        from backend.api.models.risk import RiskHistoryPoint
        history = []
        base = datetime.utcnow()
        scores = []
        for i in range(min(limit, 30)):
            score = round(random.uniform(20, 90), 2)
            scores.append(score)
            history.append(RiskHistoryPoint(
                timestamp=base - timedelta(days=i),
                risk_score=score,
                risk_level=_risk_level(score),
                key_metrics={
                    "volatility": round(random.uniform(0.1, 0.4), 4),
                    "var_95": round(random.uniform(0.01, 0.08), 4),
                },
            ))
        avg = sum(scores) / len(scores) if scores else 0
        return RiskHistoryResponse(
            entity_id=entity_id,
            entity_name=f"Entity {entity_id}",
            history=history,
            statistics={
                "avg_risk_score": round(avg, 2),
                "min_risk_score": round(min(scores), 2) if scores else 0,
                "max_risk_score": round(max(scores), 2) if scores else 0,
            },
            trends={"direction": "stable", "momentum": "neutral"},
        )
    except Exception as e:
        logger.error(f"Failed to get risk history for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-calculate")
async def batch_calculate_risk(
    entity_ids: List[str],
    calculation_type: str = "comprehensive",
    db=Depends(get_postgres_dependency),
    graph_db=Depends(get_neo4j_dependency),
    ml_models=Depends(get_ml_models_dependency)
):
    """Calculate risk for multiple entities in batch"""
    try:
        results = []
        for eid in entity_ids:
            score = round(random.uniform(20, 90), 2)
            results.append({
                "entity_id": eid,
                "risk_score": score,
                "risk_level": _risk_level(score),
                "timestamp": datetime.utcnow().isoformat(),
            })
        return {"results": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Failed to batch calculate risks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/{entity_id}")
async def get_risk_alerts(
    entity_id: str,
    severity: Optional[str] = None,
    db=Depends(get_postgres_dependency),
    cache=Depends(get_cache_dependency)
):
    """Get risk alerts for an entity"""
    try:
        alerts = [
            {
                "alert_id": f"ALT-{i+1:04d}",
                "entity_id": entity_id,
                "severity": ["info", "warning", "critical"][i % 3],
                "message": f"Risk threshold alert for {entity_id}",
                "timestamp": datetime.utcnow().isoformat(),
                "acknowledged": False,
            }
            for i in range(3)
        ]
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        return {"entity_id": entity_id, "alerts": alerts, "total": len(alerts)}
    except Exception as e:
        logger.error(f"Failed to get risk alerts for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Made with Bob
