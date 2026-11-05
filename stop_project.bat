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

echo Stopping MediSync containers...
docker compose down
if errorlevel 1 (
    echo MediSync containers could not be stopped.
    exit /b 1
)

echo MediSync containers stopped. Database and uploaded files were preserved.
exit /b 0
