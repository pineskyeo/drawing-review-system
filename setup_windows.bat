@echo off
REM Drawing Review System - Windows Setup
REM Run this in the project directory

echo === Drawing Review System Setup (Windows) ===
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Create venv
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create directories
echo Creating directories...
if not exist "data\chroma_db" mkdir data\chroma_db
if not exist "data\standards-pdfs" mkdir data\standards-pdfs
if not exist "data\cache" mkdir data\cache
if not exist "inbox" mkdir inbox
if not exist "in_progress" mkdir in_progress
if not exist "reports" mkdir reports
if not exist "logs" mkdir logs

REM Check DWG converter
echo.
echo === DWG Converter Check ===
where dwg2dxf >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] dwg2dxf found in PATH
) else (
    where ODAFileConverter >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] ODA File Converter found in PATH
    ) else (
        echo [WARN] No DWG converter found.
        echo        Options:
        echo        1. Install ODA File Converter (free for personal use)
        echo        2. Set DWG2DXF_PATH environment variable
        echo        3. Export DXF from AutoCAD and use DXF directly
    )
)

echo.
echo === Setup Complete ===
echo.
echo Next steps:
echo   1. Activate venv: venv\Scripts\activate
echo   2. Put DWG files in inbox\
echo   3. Run: python scripts\extract\extract_dwg.py --input inbox\sample.dwg --output data\cache\drawing.json
echo.
pause
