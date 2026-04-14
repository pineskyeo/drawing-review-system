@echo off
chcp 65001 >nul 2>&1
REM ============================================
REM  도면 검토 시스템 - Windows 자동 설치
REM  개발 지식 없이 더블클릭만 하면 됩니다
REM ============================================

echo.
echo  ========================================
echo   도면 검토 시스템 설치를 시작합니다
echo  ========================================
echo.

REM 현재 폴더 기준으로 동작
cd /d "%~dp0"

REM === 1. Python 확인 ===
echo [1/5] Python 확인 중...

python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Python이 이미 설치되어 있습니다.
    for /f "tokens=*" %%i in ('python --version') do echo   %%i
    goto :install_packages
)

REM Python 없으면 내장 ZIP으로 설치
echo   Python이 없습니다. 내장 Python을 설치합니다...
echo.

REM === 2. 내장 Python ZIP 풀기 ===
echo [2/5] Python 압축 해제 중...

set "PYZIP=%~dp0tools\python-win64\python-3.12.8-embed-amd64.zip"
set "PYDEST=%~dp0python"

if not exist "%PYZIP%" (
    echo   [ERROR] Python ZIP 파일이 없습니다.
    echo   프로젝트를 다시 다운로드해주세요.
    pause
    exit /b 1
)

if not exist "%PYDEST%" mkdir "%PYDEST%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%PYZIP%' -DestinationPath '%PYDEST%' -Force"

if not exist "%PYDEST%\python.exe" (
    echo   [ERROR] 압축 해제에 실패했습니다.
    pause
    exit /b 1
)
echo   [OK] Python 설치 완료

REM === 3. pip 활성화 ===
echo.
echo [3/5] pip 설치 중... (잠시 기다려주세요)

REM embeddable Python에서 pip을 쓰려면 ._pth 파일에 import site 추가
for %%f in ("%PYDEST%\python*._pth") do (
    findstr /C:"import site" "%%f" >nul 2>&1
    if errorlevel 1 (
        echo import site>> "%%f"
    )
)

set "GETPIP=%~dp0tools\python-win64\get-pip.py"
"%PYDEST%\python.exe" "%GETPIP%" --no-warn-script-location >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] pip 설치 실패
    pause
    exit /b 1
)
echo   [OK] pip 설치 완료

REM 이후 python/pip 명령은 내장 python 사용
set "PATH=%PYDEST%;%PYDEST%\Scripts;%PATH%"

goto :install_packages

:install_packages
REM === 4. 패키지 설치 ===
echo.
echo [4/5] 필요한 패키지 설치 중... (처음에는 2-3분 걸립니다)

pip install -r "%~dp0requirements.txt" --no-warn-script-location >nul 2>&1
if %errorlevel% neq 0 (
    echo   일부 패키지 설치 실패. 기본 패키지만 설치합니다...
    pip install pymupdf ezdxf python-frontmatter pyyaml click rich --no-warn-script-location >nul 2>&1
    echo   [WARN] 기본 패키지만 설치됨. RAG/LLM 기능은 나중에 추가 설치 필요.
) else (
    echo   [OK] 모든 패키지 설치 완료
)

REM === 5. 폴더 생성 ===
echo.
echo [5/5] 폴더 구조 생성 중...

if not exist "%~dp0data\cache" mkdir "%~dp0data\cache"
if not exist "%~dp0data\chroma_db" mkdir "%~dp0data\chroma_db"
if not exist "%~dp0data\standards-pdfs" mkdir "%~dp0data\standards-pdfs"
if not exist "%~dp0inbox" mkdir "%~dp0inbox"
if not exist "%~dp0in_progress" mkdir "%~dp0in_progress"
if not exist "%~dp0reports" mkdir "%~dp0reports"
if not exist "%~dp0logs" mkdir "%~dp0logs"

echo   [OK] 폴더 생성 완료

REM === 완료 ===
echo.
echo  ========================================
echo   설치 완료!
echo  ========================================
echo.
echo  사용법:
echo    1. AutoCAD에서 도면을 DXF로 저장하세요
echo       (Ctrl+Shift+S - 파일 형식: DXF)
echo.
echo    2. Claude에게 DXF 파일을 주고 말하세요:
echo       "이 도면 검토해줘"
echo.
echo    3. 또는 직접 실행:
if exist "%~dp0python\python.exe" (
echo       python\python.exe run_review.py 도면파일.dxf
) else (
echo       python run_review.py 도면파일.dxf
)
echo.
pause
