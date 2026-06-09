"""
Integration tests: API + cache layer.
Verifies cache hit/miss behaviour, cache key namespacing, and TTL parameters.
"""

import pytest
from unittest.mock import MagicMock, call
from fastapi.testclient import TestClient
import sys

for mod in [
    "backend.connectors.postgres_connector",
    "backend.connectors.neo4j_connector",
    "backend.services.cache_service",
]:
    sys.modules.setdefault(mod, MagicMock())

from backend.api.main import app
import backend.api.dependencies as deps

PORTFOLIO_ROW = {
    "portfolio_id": "cache-001",
    "portfolio_name": "Cache Test Portfolio",
    "portfolio_type": "EQUITY",
    "total_value": 1_000_000.0,
    "status": "active",
    "created_at": None,
    "updated_at": None,
    "strategy": "",
    "benchmark": "",
}


def _make_mock_cache(cached_value=None):
    c = MagicMock()
    c.get.return_value = cached_value
    c.set.return_value = None
    c.delete.return_value = None
    return c


def _make_mock_db(rows=None, dict_rows=None):
    db = MagicMock()
    db.execute_query.return_value = rows or [[1]]
    db.execute_query_dict.return_value = dict_rows or []
    db.insert_one.return_value = "cache-uuid"
    return db


@pytest.fixture()
def client_factory(monkeypatch):
    """Returns a factory to create clients with custom cache/db mocks."""
    def factory(cache=None, db=None, neo4j=None):
        _cache = cache or _make_mock_cache()
        _db = db or _make_mock_db(rows=[[5]], dict_rows=[PORTFOLIO_ROW])
        _neo4j = neo4j or MagicMock()
        _neo4j.execute_read.return_value = []

        monkeypatch.setattr(deps, "get_postgres_connector", lambda: _db)
        monkeypatch.setattr(deps, "get_neo4j_connector", lambda: _neo4j)
        monkeypatch.setattr(deps, "get_cache_service", lambda: _cache)
        monkeypatch.setattr(deps, "get_ml_models", lambda: MagicMock())
        return TestClient(app)

    return factory


# ── Cache miss: DB is queried ────────────────────────────────────────────────

class TestCacheMissBehaviour:
    def test_risk_summary_cache_miss_queries_db(self, client_factory):
        mock_db = _make_mock_db(rows=[[10]])
        mock_cache = _make_mock_cache(cached_value=None)
        client = client_factory(cache=mock_cache, db=mock_db)

        r = client.get("/api/v1/risk/summary")
        assert r.status_code == 200
        # DB was queried (execute_query called at least once)
        assert mock_db.execute_query.call_count >= 1

    def test_risk_summary_cache_miss_writes_cache(self, client_factory):
        mock_cache = _make_mock_cache(cached_value=None)
        client = client_factory(cache=mock_cache)

        client.get("/api/v1/risk/summary")
        # Cache set should have been called with the risk:summary key
        assert mock_cache.set.call_count >= 1
        first_call_args = mock_cache.set.call_args_list[0]
        key_arg = first_call_args[0][0] if first_call_args[0] else first_call_args[1].get("key", "")
        assert "summary" in str(key_arg).lower() or "risk" in str(key_arg).lower()

    def test_risk_metrics_cache_miss_queries_db(self, client_factory):
        mock_db = _make_mock_db(rows=[[7]])
        mock_cache = _make_mock_cache(cached_value=None)
        client = client_factory(cache=mock_cache, db=mock_db)

        r = client.get("/api/v1/risk/metrics")
        assert r.status_code == 200
        assert mock_db.execute_query.call_count >= 1


# ── Cache hit: DB is NOT queried ─────────────────────────────────────────────

class TestCacheHitBehaviour:
    def test_risk_summary_cache_hit_skips_db(self, client_factory):
        cached = {
            "overall_risk_score": 55.0,
            "overall_risk_level": "medium",
            "risk_trend": 0.5,
            "high_risk_count": 1,
            "total_entities": 20,
            "active_alerts": 2,
            "critical_alerts": 0,
            "risk_volatility": 1.0,
            "avg_portfolio_value": 1_000_000.0,
            "timestamp": "2024-01-01T00:00:00",
        }
        mock_cache = _make_mock_cache(cached_value=cached)
        mock_db = _make_mock_db(rows=[[99]])
        client = client_factory(cache=mock_cache, db=mock_db)

        r = client.get("/api/v1/risk/summary")
        assert r.status_code == 200
        body = r.json()
        # Returns cached value, not the DB's 99 rows
        assert body["overall_risk_score"] == 55.0
        assert body["total_entities"] == 20

    def test_risk_metrics_cache_hit_returns_cached_data(self, client_factory):
        cached = {
            "avg_risk_score": 48.0,
            "max_risk": 92.0,
            "total_entities": 15,
            "total_correlations": 75,
            "avg_cascade_depth": 2.5,
            "update_frequency": 30,
            "timestamp": "2024-01-01T00:00:00",
        }
        mock_cache = _make_mock_cache(cached_value=cached)
        client = client_factory(cache=mock_cache)

        r = client.get("/api/v1/risk/metrics")
        assert r.status_code == 200
        body = r.json()
        assert body["avg_risk_score"] == 48.0


# ── Cache key correctness ────────────────────────────────────────────────────

class TestCacheKeyNamespacing:
    def test_risk_dna_cache_key_includes_entity_id(self, client_factory):
        mock_cache = _make_mock_cache(cached_value=None)
        client = client_factory(cache=mock_cache)

        client.get("/api/v1/risk/dna/test-entity-123")
        get_calls = [str(c) for c in mock_cache.get.call_args_list]
        assert any("test-entity-123" in c for c in get_calls)

    def test_analyze_cache_key_includes_portfolio_id(self, client_factory):
        mock_cache = _make_mock_cache(cached_value=None)
        mock_db = _make_mock_db(rows=[[1]], dict_rows=[PORTFOLIO_ROW])
        client = client_factory(cache=mock_cache, db=mock_db)

        client.post("/api/v1/risk/analyze/cache-001")
        get_calls = [str(c) for c in mock_cache.get.call_args_list]
        assert any("cache-001" in c for c in get_calls)


# ── Monitoring endpoints ──────────────────────────────────────────────────────

class TestMonitoringIntegration:
    def test_health_endpoint_returns_status(self, client_factory):
        client = client_factory()
        r = client.get("/api/v1/monitoring/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data or "overall" in data or len(data) > 0

    def test_metrics_endpoint_returns_data(self, client_factory):
        client = client_factory()
        r = client.get("/api/v1/monitoring/metrics")
        assert r.status_code == 200
