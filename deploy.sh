#!/bin/bash

# Deployment script for AI Risk Constellation System
# Steps: setup -> generate data -> train models -> ingest data -> deploy

set -e
set -o pipefail

# Resolve project root relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

cd "$PROJECT_ROOT"

# Load environment variables from .env if present
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env"
    set +a
fi

LOG_DIR="$PROJECT_ROOT/logs/deploy"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/deploy_$TIMESTAMP.log"

log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "AI Risk Constellation System - Deployment"
log "=========================================="
log "Project Root: $PROJECT_ROOT"
log "Log File: $LOG_FILE"
log ""

# ------------------------------------------
# PHASE 1: SETUP
# ------------------------------------------
log "--- Phase 1: Setup ---"

# Check prerequisites
if ! command -v python3 &> /dev/null; then
    log "ERROR: Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

if ! command -v node &> /dev/null; then
    log "ERROR: Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log "ERROR: Docker is not installed. Please install Docker."
    exit 1
fi

log "Prerequisites check passed"

# Create .env from example if missing
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log "Creating .env from .env.example..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    log ".env created. Review and update it before running in production."
fi

# Python virtual environment
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    log "Creating Python virtual environment..."
    python3 -m venv "$PROJECT_ROOT/venv"
fi

log "Activating virtual environment and installing Python dependencies..."
source "$PROJECT_ROOT/venv/bin/activate"
pip install --upgrade pip --quiet
pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
log "Python dependencies installed"

# Frontend dependencies
log "Installing frontend dependencies..."
cd "$PROJECT_ROOT/frontend"
if [ ! -d "node_modules" ]; then
    npm install --silent
fi
cd "$PROJECT_ROOT"
log "Frontend dependencies installed"

# Start Docker services
log "Starting Docker services..."
docker-compose up -d 2>&1 | tee -a "$LOG_FILE"

log "Waiting for Docker services to be healthy..."
RETRIES=60  # Neo4j can take up to 2 min to download plugins and initialize
until docker-compose ps | grep "risk-postgres" | grep -q "healthy" && \
      docker-compose ps | grep "risk-redis"    | grep -q "healthy" && \
      docker-compose ps | grep "risk-neo4j"    | grep -q "healthy"; do
    if [ $RETRIES -eq 0 ]; then
        log "ERROR: Docker services did not become healthy in time."
        docker-compose ps | tee -a "$LOG_FILE"
        exit 1
    fi
    sleep 3
    ((RETRIES--))
done

log "Docker services are running"
log ""

# ------------------------------------------
# PHASE 2: GENERATE SYNTHETIC DATA
# ------------------------------------------
log "--- Phase 2: Generate Synthetic Data ---"

python3 "$PROJECT_ROOT/data/synthetic/generate_all.py" 2>&1 | tee -a "$LOG_FILE"
log "Synthetic data generation complete"
log ""

# ------------------------------------------
# PHASE 3: TRAIN ML MODELS
# ------------------------------------------
log "--- Phase 3: Train ML Models ---"

bash "$PROJECT_ROOT/ml_engine/training/train_all.sh" 2>&1 | tee -a "$LOG_FILE"
log "Model training complete"
log ""

# ------------------------------------------
# PHASE 4: INGEST DATA
# ------------------------------------------
log "--- Phase 4: Ingest Data ---"

# Initialize database schema before ingesting
if [ -f "$PROJECT_ROOT/backend/core/database_init.py" ]; then
    log "Initializing database schema..."
    python3 "$PROJECT_ROOT/backend/core/database_init.py" 2>&1 | tee -a "$LOG_FILE"
    log "Database schema initialized"
fi

TRANSACTIONS_JSON="$PROJECT_ROOT/data/synthetic/transactions.json"
PORTFOLIOS_JSON="$PROJECT_ROOT/data/synthetic/portfolio_metadata.json"

INGEST_ARGS=""
[ -f "$TRANSACTIONS_JSON" ] && INGEST_ARGS="$INGEST_ARGS --transactions $TRANSACTIONS_JSON"
[ -f "$PORTFOLIOS_JSON" ]   && INGEST_ARGS="$INGEST_ARGS --portfolios $PORTFOLIOS_JSON --build-graph $PORTFOLIOS_JSON"

if [ -n "$INGEST_ARGS" ]; then
    python3 "$PROJECT_ROOT/scripts/ingest_all_data.py" $INGEST_ARGS --validate 2>&1 | tee -a "$LOG_FILE"
    log "Data ingestion complete"
else
    log "WARNING: No data files found to ingest (synthetic data generation may have failed)"
fi
log ""

# ------------------------------------------
# PHASE 5: DEPLOY
# ------------------------------------------
log "--- Phase 5: Deploy ---"

# Kill any process already using port 8000
if lsof -ti tcp:8000 &>/dev/null; then
    log "Port 8000 already in use — stopping existing process..."
    kill "$(lsof -ti tcp:8000)" 2>/dev/null || true
    sleep 1
fi

# Start backend
log "Starting backend API..."
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 3

# Verify backend started
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    log "ERROR: Backend failed to start."
    exit 1
fi
log "Backend started (PID: $BACKEND_PID)"

# Kill any process already using port 5173
if lsof -ti tcp:5173 &>/dev/null; then
    log "Port 5173 already in use — stopping existing process..."
    kill "$(lsof -ti tcp:5173)" 2>/dev/null || true
    sleep 1
fi

# Build and serve frontend
log "Building frontend..."
cd "$PROJECT_ROOT/frontend"
npm run build 2>&1 | tee -a "$LOG_FILE"
npm run preview -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
cd "$PROJECT_ROOT"

log "Frontend started (PID: $FRONTEND_PID)"
log ""

# ------------------------------------------
# DONE
# ------------------------------------------
log "=========================================="
log "Deployment Complete"
log "=========================================="
log ""
log "Access points:"
log "  Frontend:      http://localhost:5173"
log "  Backend API:   http://localhost:8000"
log "  API Docs:      http://localhost:8000/docs"
log "  Neo4j Browser: http://localhost:7474"
log "  MLflow UI:     http://localhost:5000"
log ""
log "Process IDs:"
log "  Backend PID:  $BACKEND_PID"
log "  Frontend PID: $FRONTEND_PID"
log ""
log "To stop services, run: ./scripts/stop.sh"
log "Full log: $LOG_FILE"

wait
