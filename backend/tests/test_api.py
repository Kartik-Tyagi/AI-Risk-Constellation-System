"""
Unit tests for backend API routes.
Uses FastAPI TestClient with mocked database dependencies.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# ── Stub all heavy connectors before the app imports them ──────────────────
import sys
from unittest.mock import MagicMock

for mod in [
    "backend.connectors.postgres_connector",
    "backend.connectors.neo4j_connector",
    "backend.services.cache_service",
]:
    sys.modules.setdefault(mod, MagicMock())


def _make_mock_db(rows=None, dict_rows=None):
    db = MagicMock()
    db.execute_query.return_value = rows or [[1]]
    db.execute_query_dict.return_value = dict_rows or []
    db.insert_one.return_value = "test-uuid"
    db.update_one.return_value = None
    db.delete_one.return_value = None
    return db


def _make_mock_cache():
    cache = MagicMock()
    cache.get.return_value = None
    cache.set.return_value = None
    cache.delete.return_value = None
    return cache


def _make_mock_neo4j():
    neo4j = MagicMock()
    neo4j.execute_read.return_value = []
    return neo4j


# ── App import (after stubs are in place) ──────────────────────────────────
from backend.api.main import app
import backend.api.dependencies as deps


@pytest.fixture()
def client(monkeypatch):
    mock_db = _make_mock_db(
        rows=[[5]],
        dict_rows=[
            {
                "portfolio_id": "p1",
                "portfolio_name": "Test Portfolio",
                "portfolio_type": "EQUITY",
                "total_value": 1_000_000.0,
                "status": "active",
                "created_at": None,
                "updated_at": None,
                "strategy": "",
                "benchmark": "",
            }
        ],
    )
    mock_cache = _make_mock_cache()
    mock_neo4j = _make_mock_neo4j()
    mock_ml = MagicMock()

    monkeypatch.setattr(deps, "get_postgres_connector", lambda: mock_db)
    monkeypatch.setattr(deps, "get_neo4j_connector", lambda: mock_neo4j)
    monkeypatch.setattr(deps, "get_cache_service", lambda: mock_cache)
    monkeypatch.setattr(deps, "get_ml_models", lambda: mock_ml)

    with TestClient(app) as c:
        yield c


# ── Health ─────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_has_status(self, client):
        r = client.get("/health")
        assert "status" in r.json()


# ── Portfolio routes ────────────────────────────────────────────────────────

class TestPortfolioRoutes:
    def test_list_portfolios_200(self, client):
        r = client.get("/api/v1/portfolios/")
        assert r.status_code == 200

    def test_list_portfolios_has_portfolios_key(self, client):
        r = client.get("/api/v1/portfolios/")
        assert "portfolios" in r.json()

    def test_list_portfolios_has_total(self, client):
        r = client.get("/api/v1/portfolios/")
        assert "total" in r.json()

    def test_get_portfolio_found(self, client):
        r = client.get("/api/v1/portfolios/p1")
        assert r.status_code == 200

    def test_get_portfolio_not_found(self, client, monkeypatch):
        mock_db = _make_mock_db(rows=[[0]], dict_rows=[])
        monkeypatch.setattr(deps, "get_postgres_connector", lambda: mock_db)
        r = client.get("/api/v1/portfolios/nonexistent")
        assert r.status_code == 404

    def test_get_portfolio_risk(self, client):
        r = client.get("/api/v1/portfolios/p1/risk")
        assert r.status_code == 200
        data = r.json()
        assert "risk_score" in data
        assert "risk_metrics" in data

    def test_create_portfolio(self, client):
        payload = {
            "name": "New Portfolio",
            "description": "Test",
            "positions": [
                {
                    "entity_id": "ENT001",
                    "entity_name": "Test Corp",
                    "position_type": "long",
                    "quantity": 100,
                    "market_value": 50000.0,
                    "currency": "USD",
                }
            ],
            "metadata": {},
        }
        r = client.post("/api/v1/portfolios/", json=payload)
        assert r.status_code in (200, 201)


# ── Risk routes ─────────────────────────────────────────────────────────────

class TestRiskRoutes:
    def test_risk_summary_200(self, client):
        r = client.get("/api/v1/risk/summary")
        assert r.status_code == 200

    def test_risk_summary_fields(self, client):
        data = client.get("/api/v1/risk/summary").json()
        assert "overall_risk_score" in data
        assert "total_entities" in data
        assert "active_alerts" in data

    def test_risk_metrics_200(self, client):
        r = client.get("/api/v1/risk/metrics")
        assert r.status_code == 200

    def test_risk_metrics_fields(self, client):
        data = client.get("/api/v1/risk/metrics").json()
        assert "avg_risk_score" in data
        assert "max_risk" in data

    def test_risk_analyze_portfolio(self, client):
        r = client.post("/api/v1/risk/analyze/p1")
        assert r.status_code == 200
        data = r.json()
        assert "risk_score" in data
        assert 0 <= data["risk_score"] <= 100

    def test_risk_analyze_not_found(self, client, monkeypatch):
        mock_db = _make_mock_db(rows=[[0]], dict_rows=[])
        monkeypatch.setattr(deps, "get_postgres_connector", lambda: mock_db)
        r = client.post("/api/v1/risk/analyze/nonexistent")
        assert r.status_code == 404

    def test_risk_dna(self, client):
        r = client.get("/api/v1/risk/dna/entity_001")
        assert r.status_code == 200
        data = r.json()
        assert "dna_vector" in data
        assert len(data["dna_vector"]) == 16

    def test_risk_alerts(self, client):
        r = client.get("/api/v1/risk/alerts/entity_001")
        assert r.status_code == 200
        data = r.json()
        assert "alerts" in data

    def test_risk_history(self, client):
        r = client.get("/api/v1/risk/history/entity_001")
        assert r.status_code == 200
        data = r.json()
        assert "history" in data


# ── Graph routes ─────────────────────────────────────────────────────────────

class TestGraphRoutes:
    def test_constellation_200(self, client):
        r = client.get("/api/v1/graph/constellation")
        assert r.status_code == 200

    def test_constellation_has_nodes_edges(self, client):
        data = client.get("/api/v1/graph/constellation").json()
        assert "nodes" in data
        assert "edges" in data

    def test_constellation_nodes_are_list(self, client):
        data = client.get("/api/v1/graph/constellation").json()
        assert isinstance(data["nodes"], list)

    def test_constellation_min_risk_filter(self, client):
        r = client.get("/api/v1/graph/constellation?min_risk_score=50")
        assert r.status_code == 200
        data = r.json()
        for node in data["nodes"]:
            assert node["risk_score"] >= 50

    def test_entity_lookup(self, client):
        r = client.get("/api/v1/graph/entity/entity_001")
        assert r.status_code == 200

    def test_relationships(self, client):
        r = client.get("/api/v1/graph/relationships/entity_001")
        assert r.status_code == 200
        data = r.json()
        assert "relationships" in data


# ── Monitoring routes ────────────────────────────────────────────────────────

class TestMonitoringRoutes:
    def test_health_endpoint(self, client):
        r = client.get("/api/v1/monitoring/health")
        assert r.status_code == 200

    def test_metrics_endpoint(self, client):
        r = client.get("/api/v1/monitoring/metrics")
        assert r.status_code == 200
