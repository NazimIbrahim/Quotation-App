@echo off
setlocal
echo =====================================================================
echo  AMA Ceramics Quotation Management System - Full Setup Builder
echo =====================================================================
echo.

REM 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM 2. Check/Install PyInstaller
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM 3. Run PyInstaller Build
echo.
echo [Step 1/2] Compiling Standalone Application with PyInstaller...
pyinstaller --clean -y build_app.spec
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)
echo [PASS] Standalone application built successfully in dist\AMA_Ceramics_Quotation\

REM 4. Compile Inno Setup Installer
echo.
echo [Step 2/2] Compiling Windows Setup Installer with Inno Setup...
set "ISCC=C:\Users\Administrator\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    for /f "tokens=*" %%i in ('where ISCC.exe 2^>nul') do set "ISCC=%%i"
)

if not exist "%ISCC%" (
    echo [WARNING] Inno Setup compiler (ISCC.exe) not found.
    echo Standalone application folder is available in: dist\AMA_Ceramics_Quotation\
    pause
    exit /b 0
)

"%ISCC%" installer.iss
if %errorlevel% neq 0 (
    echo [ERROR] Inno Setup compilation failed.
    pause
    exit /b 1
)

echo.
echo =====================================================================
echo  BUILD COMPLETE!
echo  Installer created at: dist_installer\AMA_Ceramics_Quotation_Setup_v1.0.exe
echo =====================================================================
pause
