@echo off
setlocal

cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker was not found. Install and start Docker Desktop first.
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo Docker Desktop is not running. Start it, wait until it is ready, and try again.
    exit /b 1
)

if not exist ".env" (
    echo Missing .env file.
    echo Copy .env.example to .env, set the database password and URL, then run this script again.
    exit /b 1
)

echo Starting MediSync containers...
docker compose up --build -d
if errorlevel 1 (
    echo MediSync could not be started.
    exit /b 1
)

echo.
echo MediSync is starting.
echo Frontend: http://localhost:3000
echo API:      http://localhost:8000/docs
echo Use stop_project.bat to stop the containers.
exit /b 0
