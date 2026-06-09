#!/bin/bash

# Start script for AI Risk Constellation System

set -e

echo "🚀 Starting AI Risk Constellation System..."

# Check if Docker services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "🐳 Starting Docker services..."
    docker-compose up -d
    echo "⏳ Waiting for services to be ready..."
    sleep 10
fi

echo "✅ Docker services are running"

# Start backend in background
echo "🔧 Starting backend API..."
cd backend
source ../venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "⚛️  Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ All services started!"
echo ""
echo "🌐 Access points:"
echo "- Frontend: http://localhost:5173"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- Neo4j Browser: http://localhost:7474 (neo4j/riskpass123)"
echo "- MLflow UI: http://localhost:5000"
echo ""
echo "📋 Process IDs:"
echo "- Backend PID: $BACKEND_PID"
echo "- Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop services, run: ./scripts/stop.sh"
echo "Or press Ctrl+C to stop this script (services will continue running)"
echo ""

# Keep script running
wait

# Made with Bob
