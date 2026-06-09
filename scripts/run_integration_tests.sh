#!/usr/bin/env bash
# Run all integration tests for the AI Risk Constellation System.
# Usage: ./scripts/run_integration_tests.sh [--backend-only | --frontend-only]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

BACKEND_ONLY=false
FRONTEND_ONLY=false
BACKEND_FAILED=0
FRONTEND_FAILED=0

for arg in "$@"; do
  case "$arg" in
    --backend-only)  BACKEND_ONLY=true ;;
    --frontend-only) FRONTEND_ONLY=true ;;
  esac
done

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

banner() { echo -e "\n${BLUE}═══ $1 ═══${NC}"; }
ok()     { echo -e "${GREEN}✔ $1${NC}"; }
warn()   { echo -e "${YELLOW}⚠ $1${NC}"; }
fail()   { echo -e "${RED}✘ $1${NC}"; }

banner "AI Risk Constellation — Integration Test Suite"
echo "Project root: $PROJECT_ROOT"
echo "Date: $(date)"

# ── Backend integration tests ────────────────────────────────────────────────
if [ "$FRONTEND_ONLY" = false ]; then
  banner "Backend Integration Tests (FastAPI + mocked connectors)"

  if [ -d "venv" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
  else
    warn "No venv found — using system Python"
  fi

  export PYTHONPATH="$PROJECT_ROOT"

  if PYTHONPATH="$PROJECT_ROOT" pytest \
      backend/tests/integration/ \
      -v \
      --tb=short \
      --color=yes \
      -q 2>&1; then
    ok "Backend integration tests passed"
  else
    fail "Backend integration tests FAILED"
    BACKEND_FAILED=1
  fi
fi

# ── Frontend integration tests ───────────────────────────────────────────────
if [ "$BACKEND_ONLY" = false ]; then
  banner "Frontend Integration Tests (Jest + mocked axios)"

  if [ -d "frontend/node_modules" ]; then
    cd frontend
    if npm test -- --testPathPattern="integration" --watchAll=false --passWithNoTests 2>&1; then
      ok "Frontend integration tests passed"
    else
      fail "Frontend integration tests FAILED"
      FRONTEND_FAILED=1
    fi
    cd "$PROJECT_ROOT"
  else
    warn "frontend/node_modules not found — skipping frontend integration tests"
    warn "Run 'npm install' inside the frontend/ directory first"
  fi
fi

# ── Summary ──────────────────────────────────────────────────────────────────
banner "Summary"
TOTAL_FAILED=$((BACKEND_FAILED + FRONTEND_FAILED))

if [ "$FRONTEND_ONLY" = false ]; then
  if [ "$BACKEND_FAILED" -eq 0 ]; then ok "Backend: PASSED"; else fail "Backend: FAILED"; fi
fi
if [ "$BACKEND_ONLY" = false ]; then
  if [ "$FRONTEND_FAILED" -eq 0 ]; then ok "Frontend: PASSED"; else fail "Frontend: FAILED"; fi
fi

if [ "$TOTAL_FAILED" -eq 0 ]; then
  echo -e "\n${GREEN}All integration tests passed.${NC}"
  exit 0
else
  echo -e "\n${RED}$TOTAL_FAILED test suite(s) failed.${NC}"
  exit 1
fi
