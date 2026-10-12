@echo off
title AMA Ceramics - Quotation Management System
cd /d "%~dp0"

echo =====================================================================
echo   AMA CERAMICS PVT LTD - QUOTATION MANAGEMENT SYSTEM
echo =====================================================================
echo.

:: Detect Python executable
set "PYTHON_EXE="

:: Check default path in LocalAppData
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)

:: If not found, check PATH
if "%PYTHON_EXE%"=="" (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python was not found on your system!
    echo Please install Python 3.10+ from python.org or Microsoft Store.
    pause
    exit /b 1
)

echo [INFO] Using Python: %PYTHON_EXE%
echo [INFO] Starting Application...
echo.

"%PYTHON_EXE%" main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Application terminated with error code %errorlevel%.
    pause
)
