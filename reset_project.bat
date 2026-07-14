@echo off
:: ============================================================================
::  HCP CRM AI — Reset Project
::  Deletes venv, node_modules, and database so you can start fresh.
::  Run setup_and_run.bat after this to rebuild everything.
:: ============================================================================

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║           HCP CRM AI — Project Reset                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo  This will DELETE the following:
echo    - backend\venv           (Python virtual environment)
echo    - backend\hcp_crm.db     (SQLite database)
echo    - backend\__pycache__    (Python cache)
echo    - frontend\node_modules  (npm packages)
echo.
echo  Your .env files will be PRESERVED.
echo.

set /p "CONFIRM=  Are you sure? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo.
    echo  Cancelled. Nothing was deleted.
    echo.
    pause
    exit /b 0
)

echo.

:: Remove Python venv
if exist "%BACKEND_DIR%\venv" (
    echo  Removing backend\venv...
    rmdir /s /q "%BACKEND_DIR%\venv"
    echo  [OK] Removed.
)

:: Remove SQLite database
if exist "%BACKEND_DIR%\hcp_crm.db" (
    echo  Removing backend\hcp_crm.db...
    del /q "%BACKEND_DIR%\hcp_crm.db"
    echo  [OK] Removed.
)

:: Remove Python caches
for /d /r "%BACKEND_DIR%" %%d in (__pycache__) do (
    if exist "%%d" (
        echo  Removing %%d...
        rmdir /s /q "%%d"
    )
)

:: Remove node_modules
if exist "%FRONTEND_DIR%\node_modules" (
    echo  Removing frontend\node_modules...
    rmdir /s /q "%FRONTEND_DIR%\node_modules"
    echo  [OK] Removed.
)

echo.
echo  Reset complete. Run setup_and_run.bat to rebuild the project.
echo.
pause
