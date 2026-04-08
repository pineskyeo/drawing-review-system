"""프로젝트 설정 — 크로스플랫폼 (macOS / Windows / Linux)."""

import os
import platform
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

VAULT_PATH = PROJECT_ROOT / "standards-vault"
RULES_PATH = VAULT_PATH / "10-Rules"
REVIEWS_PATH = VAULT_PATH / "40-Reviews"

INBOX_PATH = PROJECT_ROOT / "inbox"
IN_PROGRESS_PATH = PROJECT_ROOT / "in_progress"
REPORTS_PATH = PROJECT_ROOT / "reports"
LOGS_PATH = PROJECT_ROOT / "logs"
DATA_PATH = PROJECT_ROOT / "data"
CACHE_PATH = DATA_PATH / "cache"


# --- DWG→DXF 변환기 자동 감지 ---

def _find_dwg2dxf():
    """DWG→DXF 변환기를 플랫폼별로 찾는다.

    우선순위:
    1. 환경변수 DWG2DXF_PATH
    2. LibreDWG (빌드된 바이너리)
    3. ODA File Converter
    4. None (DXF 직접 입력만 가능)
    """
    # 1. 환경변수
    env_path = os.environ.get("DWG2DXF_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    system = platform.system()

    # 2. LibreDWG
    if system == "Darwin":  # macOS
        candidates = [
            "/tmp/libredwg/build/dwg2dxf",
            "/usr/local/bin/dwg2dxf",
        ]
    elif system == "Windows":
        candidates = [
            str(Path.home() / "libredwg" / "build" / "dwg2dxf.exe"),
            r"C:\libredwg\build\dwg2dxf.exe",
            str(PROJECT_ROOT / "tools" / "dwg2dxf.exe"),
        ]
    else:  # Linux
        candidates = [
            "/tmp/libredwg/build/dwg2dxf",
            "/usr/local/bin/dwg2dxf",
            "/usr/bin/dwg2dxf",
        ]

    for c in candidates:
        if Path(c).exists():
            return c

    # 3. ODA File Converter
    if system == "Windows":
        oda_candidates = [
            r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
            r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe",
        ]
    elif system == "Darwin":
        oda_candidates = [
            "/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter",
        ]
    else:
        oda_candidates = ["/usr/bin/ODAFileConverter"]

    for c in oda_candidates:
        if Path(c).exists():
            return c

    # 4. PATH에서 검색
    found = shutil.which("dwg2dxf") or shutil.which("ODAFileConverter")
    if found:
        return found

    return None


DWG2DXF_BIN = _find_dwg2dxf()

# 기본 LLM 모델 (환경변수 REVIEW_LLM_MODEL로 변경 가능)
# gemini: 무료 (Gemini Flash), claude: Anthropic, openai: GPT, ollama: 로컬
DEFAULT_LLM_MODEL = os.environ.get("REVIEW_LLM_MODEL", "gemini")

# DXF 파싱 설정
PE_BAR_Y_RANGE = (-2500, -2100)
POLE_CIRCLE_RADIUS = (1.0, 2.0)
POLE_GROUP_X_TOLERANCE = 15.0
