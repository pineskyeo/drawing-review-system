---
name: drawing-review-setup
description: 도면 검토 시스템 초기 설치 및 환경 설정을 실행한다.
  trigger when 사용자가 "설치해줘", "셋업해줘", "setup", "환경 설정"을 요청할 때.
---

# Drawing Review Setup

도면 검토 시스템의 초기 설치를 자동으로 수행하는 스킬.

## 실행 순서

### 1. 프로젝트 확인
프로젝트 루트에 `run_review.py`와 `requirements.txt`가 있는지 확인.
없으면 사용자에게 프로젝트 경로 확인 요청.

### 2. Python 확인
```bash
python3 --version || python --version
```
3.9 미만이면 업그레이드 안내.

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 폴더 구조 확인
다음 폴더가 있는지 확인하고 없으면 생성:
- `data/cache/`
- `data/chroma_db/`
- `inbox/`
- `in_progress/`
- `reports/`
- `logs/`
- `standards-vault/10-Rules/`
- `standards-vault/40-Reviews/`

### 5. DWG 변환기 확인
```bash
python -c "from scripts.common.config import DWG2DXF_BIN; print('DWG converter:', DWG2DXF_BIN or 'NOT FOUND')"
```

변환기가 없으면 안내:
- "DWG 변환기가 없어요. 괜찮아요, **AutoCAD에서 DXF로 저장**해서 주시면 됩니다."
- "또는 ODA File Converter를 설치하면 DWG를 직접 쓸 수 있어요."

### 6. RAG 인덱스 빌드
규칙이 있으면 벡터 인덱스 생성:
```bash
python scripts/review/rag_search.py --build-index --vault standards-vault
```

### 7. 설치 완료 안내
사용자에게 안내:
- "설치 완료! 도면 파일(DWG 또는 DXF)을 첨부하고 **'이 도면 검토해줘'**라고 하면 됩니다."
- 현재 규칙 수 표시
- DWG 변환기 상태 표시

## 에러 처리
- pip 실패 → 구체적 에러 메시지 표시, Python 버전 확인 안내
- 권한 문제 → `pip install --user` 제안
- 네트워크 문제 → sentence-transformers 등 큰 패키지는 나중에 설치 안내
