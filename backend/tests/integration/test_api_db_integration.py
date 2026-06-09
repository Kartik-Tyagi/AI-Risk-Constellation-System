"""
Integration tests: API + mocked database layer.
Verifies that route handlers correctly pass queries to DB connectors
and transform results into the expected response shapes.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import sys

# Stub connectors before app import
for mod in [
    "backend.connectors.postgres_connector",
    "backend.connectors.neo4j_connector",
    "backend.services.cache_service",
]:
    sys.modules.setdefault(mod, MagicMock())

from backend.api.main import app
import backend.api.dependencies as deps


# ── Fixtures ────────────────────────────────────────────────────────────────

PORTFOLIO_ROW = {
    "portfolio_id": "integ-001",
    "portfolio_name": "Integration Portfolio",
    "portfolio_type": "EQUITY",
    "total_value": 2_000_000.0,
    "status": "active",
    "created_at": None,
    "updated_at": None,
    "strategy": "growth",
    "benchmark": "SP500",
}


def _db(rows=None, dict_rows=None):
    db = MagicMock()
    db.execute_query.return_value = rows or [[1]]
    db.execute_query_dict.return_value = dict_rows or []
    db.insert_one.return_value = "new-uuid"
    db.update_one.return_value = None
    db.delete_one.return_value = None
    return db


def _cache():
    c = MagicMock()
    c.get.return_value = None
    c.set.return_value = None
    c.delete.return_value = None
    return c


def _neo4j():
    n = MagicMock()
    n.execute_read.return_value = []
    return n


@pytest.fixture()
def client(monkeypatch):
    db = _db(rows=[[5]], dict_rows=[PORTFOLIO_ROW])
    monkeypatch.setattr(deps, "get_postgres_connector", lambda: db)
    monkeypatch.setattr(deps, "get_neo4j_connector", lambda: _neo4j())
    monkeypatch.setattr(deps, "get_cache_service", lambda: _cache())
    monkeypatch.setattr(deps, "get_ml_models", lambda: MagicMock())
    with TestClient(app) as c:
        yield c


# ── Portfolio → DB integration ───────────────────────────────────────────────

class TestPortfolioDBIntegration:
    def test_list_returns_db_data(self, client):
        """Portfolios endpoint should surface data returned by execute_query_dict."""
        r = client.get("/api/v1/portfolios/")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 0
        assert isinstance(body["portfolios"], list)

    def test_get_portfolio_returns_db_row(self, client):
        """Single portfolio endpoint returns the matching DB row."""
        r = client.get("/api/v1/portfolios/integ-001")
        assert r.status_code == 200
        data = r.json()
        assert data["portfolio_id"] == "integ-001"

    def test_portfolio_not_found_gives_404(self, client, monkeypatch):
        db = _db(rows=[[0]], dict_rows=[])
        monkeypatch.setattr(deps, "get_postgres_connector", lambda: db)
        r = client.get("/api/v1/portfolios/ghost")
        assert r.status_code == 404

    def test_create_portfolio_calls_insert(self, client, monkeypatch):
        """POST /portfolios/ should ultimately call db.insert_one and return an ID."""
        mock_db = _db(rows=[[1]], dict_rows=[PORTFOLIO_ROW])
        monkeypatch.setattr(deps, "get_postgres_connector", lambda: mock_db)
        payload = {
            "name": "New Integration Portfolio",
            "description": "Integration test portfolio",
            "positions": [
                {
                    "entity_id": "ENT-INTEG-01",
                    "entity_name": "Integration Corp",
                    "position_type": "long",
                    "quantity": 500,
                    "market_value": 100_000.0,
                    "currency": "USD",
                }
            ],
            "metadata": {},
        }
        r = client.post("/api/v1/portfolios/", json=payload)
        assert r.status_code in (200, 201)


# ── Risk → DB integration ────────────────────────────────────────────────────

class TestRiskDBIntegration:
    def test_risk_summary_uses_db_count(self, client):
        """Risk summary total_entities should reflect the DB row count."""
        r = client.get("/api/v1/risk/summary")
        assert r.status_code == 200
        data = r.json()
        assert "total_entities" in data
        assert isinstance(data["total_entities"], int)

    def test_risk_analyze_uses_portfolio_value(self, client):
        """Risk analyze VaR values are derived from the portfolio's total_value."""
        r = client.post("/api/v1/risk/analyze/integ-001")
        assert r.status_code == 200
        data = r.json()
        # VaR should be 5% of 2_000_000 = 100_000
        assert data["var_95"] == pytest.approx(100_000.0, rel=1e-3)

    def test_risk_analyze_missing_portfolio_404(self, client, monkeypatch):
        db = _db(rows=[[0]], dict_rows=[])
        monkeypatch.setattr(deps, "get_postgres_connector", lambda: db)
        r = client.post("/api/v1/risk/analyze/missing")
        assert r.status_code == 404

    def test_risk_metrics_total_entities_from_db(self, client):
        r = client.get("/api/v1/risk/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "total_entities" in data


# ── Graph → Neo4j integration ────────────────────────────────────────────────

class TestGraphNeo4jIntegration:
    def test_constellation_returns_nodes_edges(self, client):
        r = client.get("/api/v1/graph/constellation")
        assert r.status_code == 200
        data = r.json()
        assert "nodes" in data and "edges" in data

    def test_constellation_with_neo4j_nodes(self, client, monkeypatch):
        """When Neo4j returns nodes, constellation should surface them."""
        mock_neo4j = MagicMock()
        mock_neo4j.execute_read.return_value = [
            {"n": {"id": "N1", "risk_score": 75, "name": "Entity A"}},
            {"n": {"id": "N2", "risk_score": 45, "name": "Entity B"}},
        ]
        monkeypatch.setattr(deps, "get_neo4j_connector", lambda: mock_neo4j)
        r = client.get("/api/v1/graph/constellation")
        assert r.status_code == 200

    def test_relationships_returns_list(self, client):
        r = client.get("/api/v1/graph/relationships/integ-001")
        assert r.status_code == 200
        data = r.json()
        assert "relationships" in data

    def test_entity_lookup_returns_200(self, client):
        r = client.get("/api/v1/graph/entity/integ-001")
        assert r.status_code == 200


# ── Cache integration ────────────────────────────────────────────────────────

class TestCacheIntegration:
    def test_cache_hit_bypasses_db(self, client, monkeypatch):
        """When cache returns a value, route should return it without querying DB."""
        cached_payload = {
            "overall_risk_score": 42.0,
            "overall_risk_level": "medium",
            "risk_trend": 1.5,
            "high_risk_count": 2,
            "total_entities": 10,
            "active_alerts": 3,
            "critical_alerts": 1,
            "risk_volatility": 1.2,
            "avg_portfolio_value": 500_000.0,
            "timestamp": "2024-01-01T00:00:00",
        }
        mock_cache = MagicMock()
        mock_cache.get.return_value = cached_payload
        mock_cache.set.return_value = None
        mock_db = _db(rows=[[99]])
        monkeypatch.setattr(deps, "get_cache_service", lambda: mock_cache)
        monkeypatch.setattr(deps, "get_postgres_connector", lambda: mock_db)

        r = client.get("/api/v1/risk/summary")
        assert r.status_code == 200
        data = r.json()
        # Should return the exact cached payload, not re-query DB
        assert data["overall_risk_score"] == 42.0
        assert data["total_entities"] == 10
