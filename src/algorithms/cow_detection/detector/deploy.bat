@echo off
chcp 65001 >nul
echo ========================================
echo    Cow Detection API - Docker Deploy
echo ========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found! Please install Docker Desktop.
    pause
    exit /b 1
)

echo [1/3] Building Docker image...
docker-compose build
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Starting container...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Start failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Waiting for service to start...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo    Deployment Complete!
echo ========================================
echo.
echo API URL:  http://localhost:8002
echo API Docs: http://localhost:8002/docs
echo Health:   http://localhost:8002/health
echo.
echo Commands:
echo   Stop:    docker-compose stop
echo   Restart: docker-compose restart
echo   Logs:    docker-compose logs -f
echo   Remove:  docker-compose down
echo.
pause