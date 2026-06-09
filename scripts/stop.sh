#!/bin/bash

# Stop script for AI Risk Constellation System

echo "🛑 Stopping AI Risk Constellation System..."

# Stop backend (uvicorn)
echo "Stopping backend..."
pkill -f "uvicorn backend.api.main:app" || pkill -f "uvicorn.*8000" || echo "Backend not running"

# Stop frontend (vite)
echo "Stopping frontend..."
pkill -f "vite" || echo "Frontend not running"

# Stop Docker services
echo "Stopping Docker services..."
docker-compose down

echo "✅ All services stopped"

# Made with Bob
