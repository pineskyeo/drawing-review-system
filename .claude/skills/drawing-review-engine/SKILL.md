---
name: drawing-review-engine
description: AutoCAD 도면(DWG/DXF)을 기준 vault와 대조하여 자동 검토하고 리포트를 생성한다.
  trigger when 사용자가 "도면 검토", "DWG 검사", "규격 대조", "이 도면 확인해줘"를 요청할 때.
---

# Drawing Review Engine

AutoCAD 도면을 자동 검토하는 스킬.

## 실행

사용자가 도면 파일을 첨부하거나 경로를 알려주면:

```bash
python run_review.py {도면파일경로}
```

이 한 줄이면 된다. 내부적으로:
1. DWG면 DXF로 변환 (DXF면 그대로)
2. 도면에서 텍스트, 원, 블록 등 엔티티 추출
3. vault의 검수완료 규칙으로 자동 검증
4. 위반이 있으면 → 관련 규칙 검색 + LLM 판단까지 자동
5. 위반이 없으면 → 코드 검증만으로 끝
6. Markdown 리포트 생성 → vault에 자동 저장

## 검토 중 새 기준 발견 시
사용자가 "이런 것도 확인해야 하는데"라고 하면:
1. `standards-vault-authoring` 스킬로 규칙 파일 생성
2. 다음 검토부터 자동 적용

## LLM 모델 변경
기본: Gemini Flash (무료). 변경: `--model claude` 또는 환경변수 `REVIEW_LLM_MODEL=claude`

## 리포트 위치
- `standards-vault/40-Reviews/` (Obsidian에서 열림)
- `reports/날짜/` (백업)

## 금지 사항
- ⛔ 도면 원본 수정 금지
- ⛔ vault 규칙 파일 수정 금지 (읽기만)
