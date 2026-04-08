---
name: drawing-review-setup
description: 도면 검토 시스템 초기 설치 및 환경 설정을 실행한다.
  trigger when 사용자가 "설치해줘", "셋업해줘", "setup", "환경 설정"을 요청할 때.
---

# Drawing Review Setup

도면 검토 시스템의 초기 설치를 수행하는 스킬.

## 실행 순서

### 1. Python 확인
```bash
python --version
```
- **없으면**: 사용자에게 안내 (Claude가 직접 설치할 수 없음)
  - "Python 3.10 이상이 필요합니다."
  - "https://python.org 에서 다운로드해주세요."
  - "**설치할 때 'Add Python to PATH' 체크를 꼭 해주세요!**"
  - "설치 후 터미널을 껐다 켜고 다시 '설치해줘'라고 해주세요."
  - 여기서 멈추고 Python 설치를 기다린다.
- **있으면**: 다음 단계로

### 2. Python 패키지 설치 (자동)
```bash
pip install -r requirements.txt
```
실패하면:
- `pip install --user -r requirements.txt` 시도
- 그래도 실패하면 구체적 에러 메시지 안내

### 3. 폴더 확인 및 생성 (자동)
다음 폴더가 없으면 생성:
- `data/cache/`
- `data/chroma_db/`
- `inbox/`
- `in_progress/`
- `reports/`
- `logs/`

### 4. DWG 변환기 확인 (자동)
```bash
python -c "from scripts.common.config import DWG2DXF_BIN; print(DWG2DXF_BIN or 'NOT FOUND')"
```
- **있으면**: "DWG 파일을 직접 검토할 수 있습니다."
- **없으면**: "DWG 변환기가 없지만 괜찮아요. **AutoCAD에서 '다른 이름으로 저장' → DXF로 저장**해서 주시면 됩니다."

### 5. RAG 인덱스 빌드 (자동)
```bash
python scripts/review/rag_search.py --build-index --vault standards-vault
```

### 6. 완료 안내
"설치 완료! 사용법:
1. AutoCAD에서 도면을 DXF로 저장해주세요
2. DXF 파일을 여기에 첨부하고 **'이 도면 검토해줘'**라고 하면 됩니다
3. 검토하면서 새 기준이 필요하면 말씀해주세요 — 자동으로 규칙이 추가됩니다"

## Claude가 직접 할 수 없는 것 (사용자에게 안내)
- ⛔ Python 설치 → python.org에서 직접 설치 안내
- ⛔ Git 설치 → git-scm.com에서 직접 설치 안내
- ⛔ AutoCAD 설치/실행 → 사용자가 직접
- ⛔ 관리자 권한이 필요한 작업 → 사용자가 직접
