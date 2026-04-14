@echo off
setlocal enabledelayedexpansion

echo.
echo  ========================================
echo   Drawing Review System - Setup
echo  ========================================
echo.

cd /d "%~dp0"

REM === 1. Check Python ===
echo [1/5] Checking Python...

python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Python found.
    for /f "tokens=*" %%i in ('python --version') do echo   %%i
    goto :install_packages
)

echo   Python not found. Installing from embedded ZIP...
echo.

REM === 2. Extract Python ZIP ===
echo [2/5] Extracting Python...

set "PYZIP=%~dp0tools\python-win64\python-3.12.8-embed-amd64.zip"
set "PYDEST=%~dp0python"

if not exist "%PYZIP%" (
    echo   [ERROR] Python ZIP not found: %PYZIP%
    echo   Please re-download the project.
    pause
    exit /b 1
)

if not exist "%PYDEST%" mkdir "%PYDEST%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%PYZIP%' -DestinationPath '%PYDEST%' -Force"

if not exist "%PYDEST%\python.exe" (
    echo   [ERROR] Extraction failed.
    pause
    exit /b 1
)
echo   [OK] Python installed.

REM === 3. Install pip ===
echo.
echo [3/5] Installing pip...

REM Enable pip in embeddable Python
for %%f in ("%PYDEST%\python*._pth") do (
    findstr /C:"import site" "%%f" >nul 2>&1
    if errorlevel 1 (
        echo import site>> "%%f"
    )
)

set "GETPIP=%~dp0tools\python-win64\get-pip.py"
"%PYDEST%\python.exe" "%GETPIP%" --no-warn-script-location >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] pip install failed.
    pause
    exit /b 1
)
echo   [OK] pip installed.

set "PATH=%PYDEST%;%PYDEST%\Scripts;%PATH%"

goto :install_packages

:install_packages
REM === 4. Install packages ===
echo.
echo [4/5] Installing packages... (this may take 2-3 minutes)

pip install -r "%~dp0requirements.txt" --no-warn-script-location >nul 2>&1
if %errorlevel% neq 0 (
    echo   Some packages failed. Installing core packages only...
    pip install pymupdf ezdxf python-frontmatter pyyaml click rich --no-warn-script-location >nul 2>&1
    echo   [WARN] Core packages only. RAG/LLM features need manual install later.
) else (
    echo   [OK] All packages installed.
)

REM === 5. Create folders ===
echo.
echo [5/5] Creating folders...

if not exist "%~dp0data\cache" mkdir "%~dp0data\cache"
if not exist "%~dp0data\chroma_db" mkdir "%~dp0data\chroma_db"
if not exist "%~dp0data\standards-pdfs" mkdir "%~dp0data\standards-pdfs"
if not exist "%~dp0inbox" mkdir "%~dp0inbox"
if not exist "%~dp0in_progress" mkdir "%~dp0in_progress"
if not exist "%~dp0reports" mkdir "%~dp0reports"
if not exist "%~dp0logs" mkdir "%~dp0logs"

echo   [OK] Folders created.

REM === Done ===
echo.
echo  ========================================
echo   Setup Complete!
echo  ========================================
echo.
echo  How to use:
echo    1. Save your drawing as DXF in AutoCAD
echo       (Ctrl+Shift+S - File type: DXF)
echo.
echo    2. Tell Claude:
echo       "review this drawing" + attach DXF file
echo.
if exist "%~dp0python\python.exe" (
echo    3. Or run directly:
echo       python\python.exe run_review.py your_drawing.dxf
)
echo.
pause
