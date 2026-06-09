# UAT Report — AI Risk Constellation System
**Date:** 2026-06-09
**Phase:** 6.6 — User Acceptance Testing

---

## Test Scope

All 6 functional areas tested manually via live API calls and browser walkthrough.

---

## Feature Walkthrough Results

### 1. System Health
| Test | Result | Notes |
|------|--------|-------|
| GET /health returns status:healthy | PASS | All services operational |
| GET /api/v1/monitoring/health | PASS | Returns component statuses |
| GET /api/v1/monitoring/metrics | PASS | Returns request/latency stats |

### 2. Portfolio Management
| Test | Result | Notes |
|------|--------|-------|
| GET /api/v1/portfolios/ returns list | PASS | Returns portfolios + total count |
| GET /api/v1/portfolios/{id} returns single portfolio | PASS | |
| GET /api/v1/portfolios/nonexistent returns 404 | PASS | |
| POST /api/v1/portfolios/ creates new portfolio | PASS (after fix) | **Bug fixed:** inception_date NOT NULL violated — route now defaults to today's date |
| GET /api/v1/portfolios/{id}/risk | PASS | |

### 3. Risk Analysis
| Test | Result | Notes |
|------|--------|-------|
| GET /api/v1/risk/summary | PASS | Returns overall_risk_score, total_entities, active_alerts |
| GET /api/v1/risk/metrics | PASS | Returns avg_risk_score, max_risk, total_entities |
| POST /api/v1/risk/analyze/{portfolio_id} | PASS | Returns risk_score 0-100, var_95, var_99, risk_dna |
| GET /api/v1/risk/dna/{entity_id} | PASS (after fix) | Returns 16-element DNA vector with risk breakdown |
| GET /api/v1/risk/history/{entity_id} | PASS (after fix) | Returns 30 history points with statistics |
| GET /api/v1/risk/alerts/{entity_id} | PASS | Returns alerts list |
| POST /api/v1/risk/compare | PASS (after fix) | Returns entities with risk scores and rankings |

### 4. Graph / Constellation
| Test | Result | Notes |
|------|--------|-------|
| GET /api/v1/graph/constellation | PASS | Returns nodes=4, edges=70 from Neo4j |
| GET /api/v1/graph/entity/{id} | PASS | Returns entity properties |
| GET /api/v1/graph/relationships/{id} | PASS | Returns relationships list |
| min_risk_score filter on constellation | PASS | Filters correctly |

### 5. Frontend Pages
| Page | Result | Notes |
|------|--------|-------|
| /dashboard | PASS | Loads without crash; widgets render |
| /constellation | PASS | D3 force graph renders with nodes/edges |
| /portfolio | PASS | Portfolio list renders |
| /monitoring | PASS | Health status shown |
| /settings | PASS | Page loads |
| Sidebar navigation | PASS | All routes accessible |
| API error handling | PASS | Pages degrade gracefully on 500/404/timeout |

---

## Bugs Found and Fixed

| # | Severity | Description | Fix |
|---|----------|-------------|-----|
| 1 | High | `POST /portfolios/` failed with NOT NULL constraint on `inception_date` | Added `inception_date` defaulting to `date.today()` in route handler |
| 2 | High | `GET /risk/dna/{entity_id}` returned 500 (Pydantic validation error) | Rebuilt response with required `entity_name`, `timestamp`, `risk_dna` fields |
| 3 | High | `GET /risk/history/{entity_id}` returned 500 | Added `key_metrics` to each history point; added `statistics` and `trends` to response |
| 4 | Medium | `POST /risk/compare` returned 500 | Rebuilt response with required `entities`, `comparison_matrix`, `rankings`, `insights` fields |
| 5 | Medium | MD5 used in `query_optimizer.py` and `cache_manager.py` (bandit HIGH) | Added `usedforsecurity=False` to all non-security MD5 calls |

---

## Security Findings

| Tool | Finding | Action |
|------|---------|--------|
| bandit | 3× HIGH: MD5 for cache key hashing | Fixed with `usedforsecurity=False` |
| bandit | Medium: bind 0.0.0.0 in main.py | Acceptable for containerized deployment |
| bandit | Medium: SQL f-string in postgres_connector.py | Table/column names come from internal trusted code only |
| npm audit | 2× moderate: esbuild dev server CORS | Dev-only; no fix to avoid breaking Vite version change |

---

## Performance Results

| Test | Result |
|------|--------|
| API benchmark (all endpoints) | p95 ≤ 2ms — PASS (SLA: 500ms) |
| Load test (10 concurrent users, 10s) | 932 req/s, 0 errors, p95=16ms — PASS |

---

## Test Coverage Summary

| Suite | Tests | Status |
|-------|-------|--------|
| Backend unit tests | 61 passed, 3 skipped | PASS |
| Backend integration tests | 38 passed | PASS |
| ML engine unit tests | 118 passed | PASS |
| E2E Playwright tests | 33 passed | PASS |
| **Total** | **250 passed** | **PASS** |

---

## Sign-off

All 6 Phase 6 testing steps completed. System is ready for Phase 7 production deployment.
