---
name: standards-vault-builder
description: 기준 PDF에서 규칙을 추출하여 Obsidian vault를 구축한다.
  trigger when 사용자가 "기준 PDF 처리", "새 규격서 추가", "vault 만들어줘", "규칙 추출"을 요청할 때.
---

# Standards Vault Builder

기준 PDF에서 검토 규칙을 추출하여 Obsidian vault를 구축하는 스킬.

## 목적
기준 규격서 PDF를 분석하여:
1. 섹션별 텍스트 추출
2. 검증 가능한 규칙을 자동 초안 생성
3. Obsidian vault에 1규칙 1파일로 저장
4. 사람 검수 워크플로우 안내

## 전제 조건
- 프로젝트: `~/drawing-review-system/`
- Python 환경에 pymupdf, python-frontmatter 설치
- 기준 PDF 파일 준비

## 실행 순서

### 1. PDF 추출
```bash
python3 ~/drawing-review-system/scripts/preprocess/extract_pdf.py \
  --input {pdf_path} \
  --output ~/drawing-review-system/data/cache/pdf_sections.json
```

### 2. 추출 결과 확인
- 페이지별 타이틀, PE/PB 참조, 파츠 목록 확인
- 누락된 페이지나 잘못 추출된 섹션 체크

### 3. 규칙 초안 작성
추출된 PDF 섹션에서 검증 가능한 규칙을 식별:

- **수치 기준** → type: numeric, auto_check: true
- **존재/형식 기준** → type: existence, auto_check: true
- **해석 기준** → type: interpretive, auto_check: false

각 규칙을 `~/drawing-review-system/standards-vault/10-Rules/` 에 저장.

### 4. 규칙 파일 형식
```markdown
---
rule_id: "XX-NNN"
title: "규칙 제목"
status: "초안"
type: "numeric | existence | format | interpretive"
severity: "critical | major | minor"
category: ["카테고리1", "카테고리2"]
check:
  type: "핸들러_이름"
  # 핸들러별 파라미터
auto_check: true | false
---
# XX-NNN 규칙 제목
## 원문
> 기준 원문 인용
## 해석 노트
## 관련 기준
## 검수 체크리스트
## 검수 메모
```

### 5. 사용 가능한 check 핸들러
| 핸들러 | 용도 |
|--------|------|
| cross_check_existence | 다른 도면에 같은 텍스트 존재 확인 |
| pole_count_match | POLE 수 비교 |
| part_name_match | 파츠명 매칭 (PE→파츠 맵) |
| layout_qty_match | LAYOUT vs PE BAR 수량 비교 |
| bar_pair_pole_check | BAR 쌍 POLE 합산 검증 |
| schematic_cp_existence | CP 번호 존재 확인 |
| inverter_cross_check | 인버터명 크로스체크 |

기존 핸들러로 커버 안 되면 새 핸들러를 `rule_engine.py`에 추가.

### 6. RAG 인덱스 갱신
규칙 추가 후:
```bash
python3 ~/drawing-review-system/scripts/review/rag_search.py \
  --build-index --vault ~/drawing-review-system/standards-vault
```

### 7. 검수 안내
- status를 "초안" → "검수중" → "검수완료"로 변경
- 검수 체크리스트 항목을 하나씩 확인
- 검수 완료되면 엔진이 자동으로 로드

## 금지 사항
- ⛔ 기존 규칙 파일을 사용자 확인 없이 수정 금지
- ⛔ status를 "검수완료"로 직접 변경 금지 (사용자가 검수해야 함)
- ⛔ 기준 PDF 원본 수정 금지
