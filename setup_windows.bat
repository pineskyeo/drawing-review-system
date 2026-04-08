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

if not exist "tools\python-win64\python-3.12.8-embed-amd64.zip" (
    echo   [ERROR] tools\python-win64\python-3.12.8-embed-amd64.zip 파일이 없습니다.
    echo   프로젝트를 다시 다운로드해주세요.
    pause
    exit /b 1
)

REM 프로젝트 내에 python 폴더로 압축 해제
if not exist "python" mkdir python
powershell -Command "Expand-Archive -Path 'tools\python-win64\python-3.12.8-embed-amd64.zip' -DestinationPath 'python' -Force"

if not exist "python\python.exe" (
    echo   [ERROR] 압축 해제에 실패했습니다.
    pause
    exit /b 1
)
echo   [OK] Python 설치 완료: %cd%\python\python.exe

REM === 3. pip 활성화 ===
echo.
echo [3/5] pip 설치 중... (잠시 기다려주세요)

REM embeddable Python에서 pip을 쓰려면 ._pth 파일 수정 필요
for %%f in (python\python*._pth) do (
    echo import site>> "%%f"
)

python\python.exe tools\python-win64\get-pip.py --no-warn-script-location >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] pip 설치 실패
    pause
    exit /b 1
)
echo   [OK] pip 설치 완료

REM 이후 python 명령은 내장 python 사용
set "PATH=%cd%\python;%cd%\python\Scripts;%PATH%"

goto :install_packages

:install_packages
REM === 4. 패키지 설치 ===
echo.
echo [4/5] 필요한 패키지 설치 중... (처음에는 2-3분 걸립니다)

pip install -r requirements.txt --no-warn-script-location >nul 2>&1
if %errorlevel% neq 0 (
    echo   일부 패키지 설치 실패. 개별 설치를 시도합니다...
    pip install pymupdf ezdxf python-frontmatter pyyaml click rich --no-warn-script-location >nul 2>&1
    echo   [WARN] 기본 패키지만 설치됨. RAG/LLM 기능은 나중에 추가 설치 필요.
) else (
    echo   [OK] 모든 패키지 설치 완료
)

REM === 5. 폴더 생성 ===
echo.
echo [5/5] 폴더 구조 생성 중...

if not exist "data\cache" mkdir data\cache
if not exist "data\chroma_db" mkdir data\chroma_db
if not exist "data\standards-pdfs" mkdir data\standards-pdfs
if not exist "inbox" mkdir inbox
if not exist "in_progress" mkdir in_progress
if not exist "reports" mkdir reports
if not exist "logs" mkdir logs

echo   [OK] 폴더 생성 완료

REM === 완료 ===
echo.
echo  ========================================
echo   설치 완료!
echo  ========================================
echo.
echo  사용법:
echo    1. AutoCAD에서 도면을 DXF로 저장하세요
echo       (Ctrl+Shift+S → 파일 형식: DXF)
echo.
echo    2. Claude에게 DXF 파일을 주고 말하세요:
echo       "이 도면 검토해줘"
echo.
echo    3. 또는 직접 실행:
if exist "python\python.exe" (
echo       python\python.exe run_review.py 도면파일.dxf
) else (
echo       python run_review.py 도면파일.dxf
)
echo.
pause
