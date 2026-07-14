@echo off
:: ============================================================================
::  HCP CRM AI — Quick Start (assumes setup_and_run.bat was run at least once)
::  Just launches both servers without reinstalling anything.
:: ============================================================================

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"

echo.
echo  Starting HCP CRM AI servers...
echo.

:: Check venv exists
if not exist "%BACKEND_DIR%\venv\Scripts\activate.bat" (
    echo  [ERROR] Backend virtual environment not found!
    echo          Run setup_and_run.bat first to set up the project.
    echo.
    pause
    exit /b 1
)

:: Start backend FastAPI server (with venv activated)
start "HCP-CRM Backend (FastAPI)" cmd /k "cd /d "%BACKEND_DIR%" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

:: Small delay so backend port binds first
timeout /t 2 /nobreak >nul

:: Start frontend React dev server
start "HCP-CRM Frontend (React)" cmd /k "cd /d "%FRONTEND_DIR%" && npm start"

echo  Backend  : http://localhost:8000
echo  Frontend : http://localhost:3003
echo  API Docs : http://localhost:8000/docs
echo.
pause
