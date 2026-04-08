# 도면 검토 자동화 시스템

AutoCAD 도면(DWG/DXF)을 검토 규칙과 대조하여 위반 사항을 자동으로 찾아주는 도구입니다.

## 이런 분을 위한 도구입니다

- AutoCAD 도면을 수작업으로 크로스체크하는 분
- PE BAR, SCHEMATIC, LAYOUT 간 정합성을 확인하는 분
- 검토 기준을 문서화하고 재사용하고 싶은 분

## 시작하기 (개발 지식 불필요)

### 준비물
- **Claude Code** (설치되어 있어야 함)
- **Python 3.10 이상** (https://python.org 에서 설치)
- **AutoCAD 도면 파일** (DWG 또는 DXF)

### Step 1: 프로젝트 받기

```
git clone https://github.com/your-repo/drawing-review-system.git
```

또는 ZIP으로 다운로드하여 압축 해제.

### Step 2: Claude Code에서 열기

Claude Code를 열고 프로젝트 폴더를 워크스페이스로 설정합니다.

### Step 3: 설치

Claude Code에서 이렇게 말하세요:

> **"설치해줘"**

그러면 Claude가 알아서:
- Python 패키지 설치
- 폴더 구조 확인
- DWG 변환기 확인

### Step 4: 도면 검토

DWG 또는 DXF 파일을 첨부하고 이렇게 말하세요:

> **"이 도면 검토해줘"**

또는 구체적으로:

> **"이 DWG 파일 PE BAR 크로스체크 해줘"**

### Step 5: 결과 확인

검토 결과는 두 곳에 저장됩니다:
- `reports/날짜/도면명.md` — Markdown 리포트
- `standards-vault/40-Reviews/` — Obsidian에서 바로 열림

## 할 수 있는 말들

| 말 | 하는 일 |
|----|--------|
| "설치해줘" | 환경 설정 |
| "이 도면 검토해줘" | 전체 검토 파이프라인 실행 |
| "기준 PDF 처리해줘" | PDF에서 규칙 추출 |
| "새 규칙 추가해줘" | 검토 규칙 추가 |
| "규칙 검수해줘" | 규칙 상태 확인/검수 |
| "vault 상태 보여줘" | 현재 규칙 요약 |

## DWG 변환에 대해

이 시스템은 DWG를 직접 읽지 못하고 DXF로 변환해야 합니다.

**가장 쉬운 방법:** AutoCAD에서 `다른 이름으로 저장` → `DXF` 선택

**DXF를 직접 주면** 변환 과정 없이 바로 검토가 됩니다.

## 현재 검토 규칙 (7개)

| ID | 규칙 | 자동 |
|----|------|------|
| PE-001 | PE BAR 케이블이 SCHEMATIC에 존재하는지 | O |
| PE-002 | PE BAR POLE 수 일치 | O |
| PE-003 | PE BAR 파츠 명칭 일치 | O |
| PE-004 | BAR 쌍 POLE 합산 검증 | O |
| LO-001 | LAYOUT PB 수량 일치 | O |
| SC-001 | SCHEMATIC CP 번호 존재 | O |
| SC-002 | 3 PHASE 인버터 크로스체크 | O |

규칙은 계속 추가할 수 있습니다. "이런 기준도 확인해줘"라고 말하면 됩니다.

## 폴더 구조 (알 필요 없지만 참고용)

```
drawing-review-system/
├── run_review.py          ← 검토 실행 (이것만 알면 됨)
├── standards-vault/       ← 검토 규칙 (Obsidian으로 볼 수 있음)
│   ├── 10-Rules/          ← 규칙 파일들
│   └── 40-Reviews/        ← 검토 리포트
├── inbox/                 ← 검토할 도면 넣는 곳
├── reports/               ← 검토 결과
└── scripts/               ← 내부 스크립트 (건드릴 필요 없음)
```
