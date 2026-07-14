@echo off
setlocal enabledelayedexpansion

:: ============================================================================
::  HCP CRM AI — Complete Run Script
::  One-click script that does EVERYTHING:
::    1. Kills any existing server processes (port 8000 & 3003)
::    2. Checks prerequisites (Python, Node.js, npm)
::    3. Creates Python virtual environment (if needed)
::    4. Installs Python dependencies (if needed)
::    5. Configures backend .env (from .env.example if missing)
::    6. Seeds the database with demo HCPs
::    7. Installs frontend npm packages (if needed)
::    8. Configures frontend .env
::    9. Launches backend (FastAPI) and frontend (React) servers
:: ============================================================================

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "VENV_DIR=%BACKEND_DIR%\venv"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"
set "PIP=%VENV_DIR%\Scripts\pip.exe"
set "UVICORN=%VENV_DIR%\Scripts\uvicorn.exe"

echo.
echo ==============================================================
echo           HCP CRM AI — Complete Run Script
echo ==============================================================
echo.

:: ============================================================================
::  STEP 1 — Kill existing processes on ports 8000 and 3003
:: ============================================================================
echo [1/9] Stopping any existing servers...
echo.

:: Kill processes on port 8000 (backend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    echo    Killing process on port 8000 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

:: Kill processes on port 3003 (frontend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3003 " ^| findstr "LISTENING" 2^>nul') do (
    echo    Killing process on port 3003 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

echo    [OK] Ports cleared.
echo.

:: ============================================================================
::  STEP 2 — Check Prerequisites
:: ============================================================================
echo [2/9] Checking prerequisites...
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
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('npm --version 2^>^&1') do echo    [OK] npm %%i found

echo.
echo    All prerequisites satisfied.
echo.

:: ============================================================================
::  STEP 3 — Create Python Virtual Environment
:: ============================================================================
echo [3/9] Setting up Python virtual environment...
echo.

if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo    [SKIP] Virtual environment already exists.
) else (
    echo    Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo    [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo    [OK] Virtual environment created.
)
echo.

:: ============================================================================
::  STEP 4 — Install Python Dependencies
:: ============================================================================
echo [4/9] Installing Python dependencies...
echo.

"%PIP%" install -r "%BACKEND_DIR%\requirements.txt" --quiet --disable-pip-version-check
if errorlevel 1 (
    echo    [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo    [OK] All Python packages installed.
echo.

:: ============================================================================
::  STEP 5 — Configure Backend .env
:: ============================================================================
echo [5/9] Configuring backend environment...
echo.

if not exist "%BACKEND_DIR%\.env" (
    if exist "%BACKEND_DIR%\.env.example" (
        copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
        echo    [OK] Created backend\.env from .env.example
    ) else (
        (
            echo GROQ_API_KEY=your_groq_api_key_here
            echo GROQ_MODEL=gemma2-9b-it
            echo GROQ_MODEL_FALLBACK=llama-3.3-70b-versatile
            echo DATABASE_URL=sqlite:///./hcp_crm.db
            echo CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3003
        ) > "%BACKEND_DIR%\.env"
        echo    [OK] Created backend\.env with defaults.
    )
    echo.

    :: Prompt for Groq API key
    echo    ========================================================
    echo      Groq API key is required for AI features.
    echo      Get your key at: https://console.groq.com/keys
    echo    ========================================================
    echo.
    set /p "GROQ_KEY=    Enter your Groq API key (or press Enter to skip): "
    if defined GROQ_KEY (
        powershell -Command "(Get-Content '%BACKEND_DIR%\.env') -replace 'your_groq_api_key_here', '!GROQ_KEY!' | Set-Content '%BACKEND_DIR%\.env'"
        powershell -Command "(Get-Content '%BACKEND_DIR%\.env') -replace 'YOUR_GROQ_API_KEY_HERE', '!GROQ_KEY!' | Set-Content '%BACKEND_DIR%\.env'"
        echo    [OK] Groq API key saved.
    ) else (
        echo    [WARN] Skipped. Edit backend\.env manually to add your key later.
    )
) else (
    echo    [SKIP] backend\.env already exists.
)
echo.

:: ============================================================================
::  STEP 6 — Seed the Database
:: ============================================================================
echo [6/9] Seeding database with demo HCPs...
echo.

pushd "%BACKEND_DIR%"
"%PYTHON%" seed.py
if errorlevel 1 (
    echo    [WARN] Seed script had an issue (may be fine if already seeded).
) else (
    echo    [OK] Database seeded successfully.
)
popd
echo.

:: ============================================================================
::  STEP 7 — Install Frontend Dependencies
:: ============================================================================
echo [7/9] Installing frontend dependencies...
echo.

if exist "%FRONTEND_DIR%\node_modules\react\package.json" (
    echo    [SKIP] node_modules already present.
) else (
    echo    Running npm install (this may take a minute)...
    pushd "%FRONTEND_DIR%"
    npm install
    if errorlevel 1 (
        echo    [ERROR] npm install failed.
        popd
        pause
        exit /b 1
    )
    popd
    echo    [OK] Frontend packages installed.
)
echo.

:: ============================================================================
::  STEP 8 — Configure Frontend .env
:: ============================================================================
echo [8/9] Configuring frontend environment...
echo.

if not exist "%FRONTEND_DIR%\.env" (
    if exist "%FRONTEND_DIR%\.env.example" (
        copy "%FRONTEND_DIR%\.env.example" "%FRONTEND_DIR%\.env" >nul
        echo    [OK] Created frontend\.env from .env.example
    ) else (
        echo PORT=3003> "%FRONTEND_DIR%\.env"
        echo    [OK] Created frontend\.env with PORT=3003
    )
) else (
    echo    [SKIP] frontend\.env already exists.
)
echo.

:: ============================================================================
::  STEP 9 — Launch Both Servers
:: ============================================================================
echo [9/9] Launching servers...
echo.

:: Launch Backend (FastAPI with uvicorn)
start "HCP-CRM Backend" cmd /k "cd /d "%BACKEND_DIR%" && call venv\Scripts\activate.bat && echo. && echo  ============================================ && echo    Backend server starting on port 8000... && echo  ============================================ && echo. && uvicorn app.main:app --reload --port 8000"

:: Wait for backend to bind
timeout /t 3 /nobreak >nul

:: Launch Frontend (React dev server)
start "HCP-CRM Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && echo. && echo  ============================================ && echo    Frontend server starting on port 3003... && echo  ============================================ && echo. && npm start"

echo.
echo ==============================================================
echo                     Setup Complete!
echo ==============================================================
echo.
echo   Backend  : http://localhost:8000
echo   API Docs : http://localhost:8000/docs
echo   Frontend : http://localhost:3003
echo.
echo   Both servers launched in separate windows.
echo   Close them (or press Ctrl+C) to stop the servers.
echo.
echo ==============================================================
echo.
pause
