# Drawing Review System

AutoCAD 도면(DWG/DXF)을 기준 규칙과 대조하여 자동 검토하는 시스템.

## 사용자가 하는 말 → 실행할 스킬

| 사용자 요청 | 스킬 | 하는 일 |
|------------|------|--------|
| "설치해줘" | drawing-review-setup | 환경 설치 |
| "도면 검토해줘" + 파일 | drawing-review-engine | 전체 검토 파이프라인 |
| "기준 PDF 처리해줘" + PDF | standards-vault-builder | PDF → 규칙 추출 |
| "규칙 추가해줘" / "규칙 검수" | standards-vault-authoring | 규칙 작성/관리 |

## 원커맨드 실행

```bash
python run_review.py 도면.dxf                        # Stage 1만
python run_review.py 도면.dxf --model gemini          # Stage 1+2+3
python run_review.py 도면.dxf --model claude          # Claude로 판단
python run_review.py 도면.dxf --model ollama          # 로컬 LLM
```

## 프로젝트 구조

```
run_review.py              원커맨드 파이프라인
scripts/
  extract/extract_dwg.py   DWG/DXF → JSON
  preprocess/extract_pdf.py PDF → 섹션 추출
  review/
    load_rules.py           vault → 규칙 로드
    rule_engine.py          Stage 1: 코드 검증 (7개 핸들러)
    rag_search.py           Stage 2: RAG 검색 (ChromaDB + BGE-M3)
    llm_review.py           Stage 3: LLM 판단 (Gemini/Claude/GPT/Ollama)
  report/generate_report.py 리포트 생성 (vault 자동 저장)
standards-vault/            Obsidian vault (검토 규칙 + 리포트)
.claude/skills/             Claude Code 스킬 4개
```

## 핵심 원칙

- 복잡한 로직은 Python 스크립트에 위임. Claude Code는 실행 순서만 제어
- 수치/존재 기준은 코드로 검증 (LLM 불필요). 해석 기준만 LLM
- standards-vault 규칙은 읽기 전용 (검토 중 수정 금지)
- 리포트는 `standards-vault/40-Reviews/`에 자동 저장

## DWG 변환

DXF를 직접 주면 변환 불필요. DWG일 경우:
- `config.py`가 LibreDWG / ODA File Converter를 자동 감지
- 환경변수 `DWG2DXF_PATH`로 수동 지정 가능
- 둘 다 없으면 AutoCAD에서 DXF 내보내기 안내

## 규칙 vault (standards-vault/10-Rules/)

- 1규칙 1파일 (`.md` + frontmatter)
- `status: 검수완료`만 엔진에 로드
- `check.type`으로 핸들러 매핑
- 사용 가능 핸들러: cross_check_existence, pole_count_match, part_name_match, layout_qty_match, bar_pair_pole_check, schematic_cp_existence, inverter_cross_check
