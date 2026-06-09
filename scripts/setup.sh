#!/bin/bash

# Setup script for AI Risk Constellation System
# This script sets up the development environment

set -e

echo "🚀 Setting up AI Risk Constellation System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please update it with your configuration."
fi

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Python dependencies installed"

# Set up frontend
echo "⚛️  Setting up frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Frontend dependencies already installed"
fi
cd ..

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d
echo "✅ Docker services started"

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose ps

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Activate Python virtual environment: source venv/bin/activate"
echo "2. Generate synthetic data: python data/synthetic/generate_all.py"
echo "3. Initialize databases: python backend/core/database_init.py"
echo "4. Start backend: cd backend && uvicorn api.main:app --reload"
echo "5. Start frontend: cd frontend && npm run dev"
echo ""
echo "🌐 Access points:"
echo "- Frontend: http://localhost:5173"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- Neo4j Browser: http://localhost:7474"
echo "- MLflow UI: http://localhost:5000"
echo ""

# Made with Bob
