@echo off
:: ============================================================================
::  HCP CRM AI — Stop All Servers
::  Kills any running uvicorn and node processes for this project.
:: ============================================================================

echo.
echo  Stopping HCP CRM AI servers...
echo.

:: Kill uvicorn (backend)
taskkill /FI "WINDOWTITLE eq HCP-CRM Backend*" /T /F >nul 2>&1
if not errorlevel 1 (
    echo  [OK] Backend server stopped.
) else (
    echo  [--] Backend server was not running.
)

:: Kill React dev server (frontend)
taskkill /FI "WINDOWTITLE eq HCP-CRM Frontend*" /T /F >nul 2>&1
if not errorlevel 1 (
    echo  [OK] Frontend server stopped.
) else (
    echo  [--] Frontend server was not running.
)

echo.
echo  All servers stopped.
echo.
pause
