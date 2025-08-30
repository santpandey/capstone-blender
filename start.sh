#!/bin/bash
# Startup script for 3D Asset Generator

echo "🚀 Starting 3D Asset Generator..."

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "📦 Using Docker deployment..."
    
    # Build and start services
    docker-compose build
    docker-compose up -d
    
    echo "✅ Services started!"
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📊 Health check: http://localhost:8000/health"
    
    # Show logs
    echo "📋 Showing logs (Ctrl+C to stop)..."
    docker-compose logs -f
    
else
    echo "⚠️  Docker not found. Starting in development mode..."
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        echo "🔧 Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
    fi
    
    # Install dependencies using uv
    echo "📦 Installing dependencies with uv..."
    uv sync --extra web --extra mcp --extra vector
    
    # Start backend
    echo "🔧 Starting backend server..."
    cd backend
    uv run python main.py &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend (simple HTTP server)
    echo "🌐 Starting frontend server..."
    cd front_end
    python -m http.server 3000 &
    FRONTEND_PID=$!
    cd ..
    
    echo "✅ Services started!"
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    
    # Cleanup function
    cleanup() {
        echo "🛑 Stopping services..."
        kill $BACKEND_PID 2>/dev/null
        kill $FRONTEND_PID 2>/dev/null
        exit 0
    }
    
    trap cleanup SIGINT SIGTERM
    
    # Wait for services
    wait
fi
