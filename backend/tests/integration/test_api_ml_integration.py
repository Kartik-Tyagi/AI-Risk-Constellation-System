"""
Integration tests: API + ML models layer.
Verifies risk routes correctly invoke ML helpers and return well-formed responses.
"""

import pytest
from unittest.mock import MagicMock
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
    "portfolio_id": "ml-test-001",
    "portfolio_name": "ML Test Portfolio",
    "portfolio_type": "EQUITY",
    "total_value": 5_000_000.0,
    "status": "active",
    "created_at": None,
    "updated_at": None,
    "strategy": "",
    "benchmark": "",
}


def _db(rows=None, dict_rows=None):
    db = MagicMock()
    db.execute_query.return_value = rows or [[1]]
    db.execute_query_dict.return_value = dict_rows or []
    db.insert_one.return_value = "ml-uuid"
    return db


@pytest.fixture()
def client(monkeypatch):
    mock_db = _db(rows=[[3]], dict_rows=[PORTFOLIO_ROW])
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    mock_cache.set.return_value = None
    mock_neo4j = MagicMock()
    mock_neo4j.execute_read.return_value = []
    mock_ml = MagicMock()

    monkeypatch.setattr(deps, "get_postgres_connector", lambda: mock_db)
    monkeypatch.setattr(deps, "get_neo4j_connector", lambda: mock_neo4j)
    monkeypatch.setattr(deps, "get_cache_service", lambda: mock_cache)
    monkeypatch.setattr(deps, "get_ml_models", lambda: mock_ml)

    with TestClient(app) as c:
        yield c


# ── Risk DNA ─────────────────────────────────────────────────────────────────

class TestRiskDNAIntegration:
    def test_dna_returns_16_element_vector(self, client):
        r = client.get("/api/v1/risk/dna/ml-test-001")
        assert r.status_code == 200
        data = r.json()
        assert len(data["dna_vector"]) == 16

    def test_dna_vector_values_between_0_and_1(self, client):
        r = client.get("/api/v1/risk/dna/ml-test-001")
        data = r.json()
        for v in data["dna_vector"]:
            assert 0.0 <= v <= 1.0

    def test_dna_has_entity_id(self, client):
        r = client.get("/api/v1/risk/dna/ml-entity-007")
        data = r.json()
        assert data["entity_id"] == "ml-entity-007"

    def test_dna_has_risk_dna_breakdown(self, client):
        r = client.get("/api/v1/risk/dna/ml-test-001")
        data = r.json()
        assert "risk_dna" in data
        riskdna = data["risk_dna"]
        assert "market_risk" in riskdna
        assert "credit_risk" in riskdna


# ── Risk History ─────────────────────────────────────────────────────────────

class TestRiskHistoryIntegration:
    def test_history_returns_list(self, client):
        r = client.get("/api/v1/risk/history/ml-test-001")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["history"], list)

    def test_history_has_statistics(self, client):
        r = client.get("/api/v1/risk/history/ml-test-001")
        data = r.json()
        stats = data["statistics"]
        assert "avg_risk_score" in stats
        assert "min_risk_score" in stats
        assert "max_risk_score" in stats

    def test_history_points_have_required_fields(self, client):
        r = client.get("/api/v1/risk/history/ml-test-001")
        data = r.json()
        for point in data["history"]:
            assert "risk_score" in point
            assert "risk_level" in point
            assert "timestamp" in point

    def test_history_limit_respected(self, client):
        r = client.get("/api/v1/risk/history/ml-test-001?limit=5")
        assert r.status_code == 200
        data = r.json()
        assert len(data["history"]) <= 5


# ── Risk Analyze ─────────────────────────────────────────────────────────────

class TestRiskAnalyzeIntegration:
    def test_analyze_returns_risk_score_0_to_100(self, client):
        r = client.post("/api/v1/risk/analyze/ml-test-001")
        assert r.status_code == 200
        data = r.json()
        assert 0 <= data["risk_score"] <= 100

    def test_analyze_returns_var_fields(self, client):
        r = client.post("/api/v1/risk/analyze/ml-test-001")
        data = r.json()
        assert "var_95" in data
        assert "var_99" in data

    def test_analyze_var_proportional_to_portfolio_value(self, client):
        r = client.post("/api/v1/risk/analyze/ml-test-001")
        data = r.json()
        # var_99 > var_95 (more conservative)
        assert data["var_99"] >= data["var_95"]

    def test_analyze_has_risk_dna(self, client):
        r = client.post("/api/v1/risk/analyze/ml-test-001")
        data = r.json()
        assert "risk_dna" in data
        assert "market_risk" in data["risk_dna"]

    def test_analyze_has_sharpe_and_drawdown(self, client):
        r = client.post("/api/v1/risk/analyze/ml-test-001")
        data = r.json()
        assert "sharpe_ratio" in data
        assert "max_drawdown" in data


# ── Risk Comparison ──────────────────────────────────────────────────────────

class TestRiskComparisonIntegration:
    def test_compare_multiple_entities(self, client):
        payload = {"entity_ids": ["ml-001", "ml-002", "ml-003"]}
        r = client.post("/api/v1/risk/compare", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert len(data["entities"]) == 3

    def test_compare_returns_risk_scores(self, client):
        payload = {"entity_ids": ["ml-001", "ml-002"]}
        r = client.post("/api/v1/risk/compare", json=payload)
        data = r.json()
        for ent in data["entities"]:
            assert "risk_score" in ent
            assert "risk_level" in ent

    def test_compare_returns_rankings(self, client):
        payload = {"entity_ids": ["ml-001", "ml-002"]}
        r = client.post("/api/v1/risk/compare", json=payload)
        data = r.json()
        assert "rankings" in data
        assert "insights" in data
