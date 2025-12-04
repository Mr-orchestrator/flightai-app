@echo off
echo ========================================
echo  FlightAI - Ultra Premium UI Launcher
echo  CRED-Level + Emirates Luxury Experience
echo ========================================
echo.

echo [1/2] Starting Python FastAPI Backend...
echo.
start "FlightAI Backend" cmd /k "cd /d %~dp0 && python api_server.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Next.js Premium Frontend...
echo.
start "FlightAI Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo  LAUNCH COMPLETE!
echo ========================================
echo.
echo  Backend API:  http://localhost:8000
echo  API Docs:     http://localhost:8000/docs
echo  Frontend UI:  http://localhost:3000
echo.
echo  Open your browser to: http://localhost:3000
echo ========================================
echo.

pause
