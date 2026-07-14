@echo off
setlocal enabledelayedexpansion

:: ============================================================================
::  HCP CRM AI — Complete Project Setup & Launch Script
::  This batch file does EVERYTHING needed to get the project running:
::    1. Checks prerequisites (Python, Node.js, npm)
::    2. Creates Python virtual environment (if not exists)
::    3. Installs Python dependencies
::    4. Sets up backend .env (prompts for Groq API key if needed)
::    5. Seeds the database with demo HCPs
::    6. Installs frontend npm dependencies (if not installed)
::    7. Sets up frontend .env
::    8. Launches backend (FastAPI) and frontend (React) servers
:: ============================================================================

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "VENV_DIR=%BACKEND_DIR%\venv"

:: ---- Colors via ANSI (Windows 10+) ----
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║           HCP CRM AI — Setup ^& Launch Script                ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: ============================================================================
::  STEP 1 — Check Prerequisites
:: ============================================================================
echo [1/8] Checking prerequisites...
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo    [ERROR] Python is not installed or not in PATH.
    echo            Download from https://www.python.org/downloads/
    echo            Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo    [OK] %%i found

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo    [ERROR] Node.js is not installed or not in PATH.
    echo            Download from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo    [OK] Node.js %%i found

:: Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo    [ERROR] npm is not installed or not in PATH.
    echo            It should come with Node.js. Try reinstalling Node.js.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('npm --version 2^>^&1') do echo    [OK] npm %%i found

echo.
echo    All prerequisites satisfied.
echo.

:: ============================================================================
::  STEP 2 — Create Python Virtual Environment
:: ============================================================================
echo [2/8] Setting up Python virtual environment...
echo.

if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo    [SKIP] Virtual environment already exists at backend\venv
) else (
    echo    Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo    [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo    [OK] Virtual environment created at backend\venv
)
echo.

:: ============================================================================
::  STEP 3 — Install Python Dependencies
:: ============================================================================
echo [3/8] Installing Python dependencies...
echo.

call "%VENV_DIR%\Scripts\activate.bat"

pip install -r "%BACKEND_DIR%\requirements.txt" --quiet --disable-pip-version-check
if errorlevel 1 (
    echo    [ERROR] Failed to install Python dependencies.
    echo            Check backend\requirements.txt for issues.
    pause
    exit /b 1
)
echo    [OK] All Python packages installed.
echo.

:: ============================================================================
::  STEP 4 — Configure Backend .env
:: ============================================================================
echo [4/8] Configuring backend environment...
echo.

if not exist "%BACKEND_DIR%\.env" (
    echo    No .env found. Creating from .env.example...
    copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
    echo    [OK] Created backend\.env from template.
    echo.
)

:: Check if Groq API key is set to the placeholder
findstr /C:"your_groq_api_key_here" "%BACKEND_DIR%\.env" >nul 2>&1
if not errorlevel 1 (
    echo    ╔═══════════════════════════════════════════════════════╗
    echo    ║  Groq API key is required for the AI agent to work.  ║
    echo    ║  Get your key at: https://console.groq.com/keys      ║
    echo    ╚═══════════════════════════════════════════════════════╝
    echo.
    set /p "GROQ_KEY=    Enter your Groq API key (or press Enter to skip): "
    if defined GROQ_KEY (
        :: Replace the placeholder with the actual key
        powershell -Command "(Get-Content '%BACKEND_DIR%\.env') -replace 'your_groq_api_key_here', '!GROQ_KEY!' | Set-Content '%BACKEND_DIR%\.env'"
        echo    [OK] Groq API key saved to backend\.env
    ) else (
        echo    [WARN] Skipped. The AI chat features will NOT work without a valid key.
        echo           Edit backend\.env manually to add your GROQ_API_KEY later.
    )
    echo.
)

:: Also check for YOUR_GROQ_API_KEY_HERE (uppercase placeholder)
findstr /C:"YOUR_GROQ_API_KEY_HERE" "%BACKEND_DIR%\.env" >nul 2>&1
if not errorlevel 1 (
    echo    ╔═══════════════════════════════════════════════════════╗
    echo    ║  Groq API key is required for the AI agent to work.  ║
    echo    ║  Get your key at: https://console.groq.com/keys      ║
    echo    ╚═══════════════════════════════════════════════════════╝
    echo.
    set /p "GROQ_KEY=    Enter your Groq API key (or press Enter to skip): "
    if defined GROQ_KEY (
        powershell -Command "(Get-Content '%BACKEND_DIR%\.env') -replace 'YOUR_GROQ_API_KEY_HERE', '!GROQ_KEY!' | Set-Content '%BACKEND_DIR%\.env'"
        echo    [OK] Groq API key saved to backend\.env
    ) else (
        echo    [WARN] Skipped. The AI chat features will NOT work without a valid key.
        echo           Edit backend\.env manually to add your GROQ_API_KEY later.
    )
    echo.
)

echo    [OK] Backend environment configured.
echo.

:: ============================================================================
::  STEP 5 — Seed the Database
:: ============================================================================
echo [5/8] Seeding database with demo HCPs...
echo.

pushd "%BACKEND_DIR%"
python seed.py
if errorlevel 1 (
    echo    [WARN] Seed script encountered an issue (may be fine if already seeded).
) else (
    echo    [OK] Database seeded.
)
popd
echo.

:: ============================================================================
::  STEP 6 — Install Frontend Dependencies
:: ============================================================================
echo [6/8] Installing frontend dependencies...
echo.

if exist "%FRONTEND_DIR%\node_modules\react\package.json" (
    echo    [SKIP] node_modules already present. To reinstall, delete frontend\node_modules first.
) else (
    echo    Running npm install (this may take a minute)...
    pushd "%FRONTEND_DIR%"
    npm install
    if errorlevel 1 (
        echo    [ERROR] npm install failed. Check frontend\package.json for issues.
        popd
        pause
        exit /b 1
    )
    popd
    echo    [OK] Frontend packages installed.
)
echo.

:: ============================================================================
::  STEP 7 — Configure Frontend .env
:: ============================================================================
echo [7/8] Configuring frontend environment...
echo.

if not exist "%FRONTEND_DIR%\.env" (
    copy "%FRONTEND_DIR%\.env.example" "%FRONTEND_DIR%\.env" >nul 2>&1
    if exist "%FRONTEND_DIR%\.env" (
        echo    [OK] Created frontend\.env from template.
    ) else (
        :: Create a minimal .env if no .env.example exists
        echo REACT_APP_API_URL=http://localhost:8000> "%FRONTEND_DIR%\.env"
        echo    [OK] Created frontend\.env with default API URL.
    )
) else (
    echo    [SKIP] frontend\.env already exists.
)
echo.

:: ============================================================================
::  STEP 8 — Launch Both Servers
:: ============================================================================
echo [8/8] Launching servers...
echo.
echo    Backend  : http://localhost:8000  (API docs at http://localhost:8000/docs)
echo    Frontend : http://localhost:3003
echo.
echo    Two new terminal windows will open — one for each server.
echo    Close them (or press Ctrl+C in each) to stop the servers.
echo.

:: Launch Backend (FastAPI with uvicorn) in a new window
start "HCP-CRM Backend (FastAPI)" cmd /k "cd /d "%BACKEND_DIR%" && call venv\Scripts\activate.bat && echo. && echo  ══ Backend server starting... ══ && echo. && uvicorn app.main:app --reload --port 8000"

:: Small delay to let the backend start binding its port
timeout /t 3 /nobreak >nul

:: Launch Frontend (React dev server) in a new window
start "HCP-CRM Frontend (React)" cmd /k "cd /d "%FRONTEND_DIR%" && echo. && echo  ══ Frontend server starting... ══ && echo. && npm start"

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    Setup Complete!                           ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║  Backend  → http://localhost:8000                            ║
echo ║  API Docs → http://localhost:8000/docs                       ║
echo ║  Frontend → http://localhost:3003                            ║
echo ║                                                              ║
echo ║  Both servers launched in separate windows.                  ║
echo ║  Press any key to close this setup window.                   ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
pause
