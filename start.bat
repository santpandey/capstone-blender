@echo off
REM Startup script for 3D Asset Generator (Windows)

echo 🚀 Starting 3D Asset Generator...

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% == 0 (
    docker-compose --version >nul 2>&1
    if %errorlevel% == 0 (
        echo 📦 Using Docker deployment...
        
        REM Build and start services
        docker-compose build
        docker-compose up -d
        
        echo ✅ Services started!
        echo 🌐 Frontend: http://localhost:3000
        echo 🔧 Backend API: http://localhost:8000
        echo 📊 Health check: http://localhost:8000/health
        
        REM Show logs
        echo 📋 Showing logs (Ctrl+C to stop)...
        docker-compose logs -f
        
        goto :end
    )
)

echo ⚠️  Docker not found. Starting in development mode...

REM Check if uv is installed
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔧 Installing uv package manager...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    refreshenv
)

REM Install dependencies using uv
echo 📦 Installing dependencies with uv...
uv sync --extra web --extra mcp --extra vector

REM Start backend
echo 🔧 Starting backend server...
start /B uv run python backend\main.py

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend (simple HTTP server)
echo 🌐 Starting frontend server...
cd front_end
start /B python -m http.server 3000
cd ..

echo ✅ Services started!
echo 🌐 Frontend: http://localhost:3000
echo 🔧 Backend API: http://localhost:8000
echo 📊 Press any key to stop services...

pause >nul

REM Cleanup
echo 🛑 Stopping services...
taskkill /f /im python.exe >nul 2>&1

:end
