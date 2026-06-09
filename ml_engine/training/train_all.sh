#!/bin/bash

# Master Training Script for AI Risk Constellation System
# This script trains all models in sequence with proper logging

set -e          # Exit on error
set -o pipefail # Catch errors in pipes

echo "=========================================="
echo "AI Risk Constellation System - Training"
echo "=========================================="
echo ""

# Set up directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_DIR="$PROJECT_ROOT/logs/training"
mkdir -p "$LOG_DIR"

# Timestamp for this training run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/train_all_$TIMESTAMP.log"

echo "Project Root: $PROJECT_ROOT"
echo "Log Directory: $LOG_DIR"
echo "Log File: $LOG_FILE"
echo ""

# Function to log messages
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

# Function to train a model
# Usage: train_model <model_name> <script_name> [extra args...]
train_model() {
    local model_name=$1
    local script_name=$2
    shift 2
    local extra_args="$*"

    log "=========================================="
    log "Training: $model_name"
    log "=========================================="

    if [ -f "$SCRIPT_DIR/$script_name" ]; then
        python "$SCRIPT_DIR/$script_name" $extra_args 2>&1 | tee -a "$LOG_FILE"

        if [ $? -eq 0 ]; then
            log "✓ $model_name training completed successfully"
        else
            log "✗ $model_name training failed"
            return 1
        fi
    else
        log "⚠ Script not found: $script_name"
        return 1
    fi

    log ""
}

# Start training
log "Starting training pipeline..."
log ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    log "✗ Python not found. Please install Python 3.8+"
    exit 1
fi

log "Python version: $(python --version)"
log ""

# Train models in sequence
MODELS_TRAINED=0
MODELS_FAILED=0

# 1. Train Quantum Optimizer
if train_model "Quantum Risk Optimizer" "train_quantum_optimizer.py"; then
    ((MODELS_TRAINED++))
else
    ((MODELS_FAILED++))
fi

# 2. Train GAT
if train_model "Graph Attention Network" "train_gat.py"; then
    ((MODELS_TRAINED++))
else
    ((MODELS_FAILED++))
fi

# 3. Train Temporal GNN (already exists)
TEMPORAL_DATA_DIR="$PROJECT_ROOT/data/synthetic"
if train_model "Temporal GNN" "train_temporal_gnn.py" --data_dir "$TEMPORAL_DATA_DIR"; then
    ((MODELS_TRAINED++))
else
    ((MODELS_FAILED++))
fi

# 4. Train Risk DNA
if train_model "Risk DNA Generator" "train_risk_dna.py"; then
    ((MODELS_TRAINED++))
else
    ((MODELS_FAILED++))
fi

# Summary
log "=========================================="
log "Training Summary"
log "=========================================="
log "Models Trained Successfully: $MODELS_TRAINED"
log "Models Failed: $MODELS_FAILED"
log "Total Time: $SECONDS seconds"
log ""

if [ $MODELS_FAILED -eq 0 ]; then
    log "✓ All models trained successfully!"
    exit 0
else
    log "⚠ Some models failed to train. Check logs for details."
    exit 1
fi

# Made with Bob
