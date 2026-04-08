---
name: standards-vault-authoring
description: vault 내 규칙 작성, 검수, 관리를 지원한다.
  trigger when 사용자가 "규칙 검수", "새 규칙 추가", "규칙 수정", "vault 정리", "규칙 상태"를 요청할 때.
---

# Standards Vault Authoring

Obsidian vault의 규칙 작성, 검수, 관리를 도와주는 스킬.

## 목적
- 새 검토 규칙을 올바른 템플릿으로 작성
- 기존 규칙의 검수 진행 지원
- vault 상태 점검 (미검수 규칙, 링크 누락 등)
- RAG 인덱스 갱신

## 전제 조건
- 프로젝트: `~/drawing-review-system/`
- `standards-vault/` 폴더 존재

## 기능

### 1. 새 규칙 추가
사용자가 새 검토 기준을 알려주면:
1. 기존 규칙과 중복 확인 (rule_id, 내용)
2. 적절한 check 핸들러 선택
3. 템플릿 기반으로 규칙 파일 생성
4. status를 "초안"으로 설정
5. 관련 기준 링크 자동 추천

**규칙 파일 경로**: `standards-vault/10-Rules/{rule_id}-{제목}.md`
**rule_id 규칙**:
- PE-NNN: PE BAR 관련
- SC-NNN: SCHEMATIC 관련
- LO-NNN: LAYOUT 관련
- GN-NNN: 일반 규칙

### 2. 규칙 검수 지원
사용자가 "규칙 검수"를 요청하면:
1. status가 "초안" 또는 "검수중"인 규칙 목록 표시
2. 선택한 규칙의 검수 체크리스트 표시
3. 각 항목 확인 후 체크 표시
4. 모든 항목 통과 시 status → "검수완료" 변경 제안

### 3. Vault 상태 점검
```bash
python3 ~/drawing-review-system/scripts/review/load_rules.py \
  --vault ~/drawing-review-system/standards-vault \
  --all \
  --output /dev/stdout
```
표시 항목:
- 총 규칙 수 (상태별)
- auto_check 가능 규칙 vs 해석 규칙
- 링크 누락 (관련 기준 없음)
- 카테고리별 분포

### 4. RAG 인덱스 갱신
규칙 추가/수정 후:
```bash
python3 ~/drawing-review-system/scripts/review/rag_search.py \
  --build-index --vault ~/drawing-review-system/standards-vault
```

### 5. 사용 가능한 check 핸들러
새 규칙 작성 시 아래 핸들러 중 선택:

| 핸들러 | 용도 | 파라미터 |
|--------|------|----------|
| cross_check_existence | 텍스트 존재 크로스체크 | source_bar, exceptions |
| pole_count_match | POLE 수 비교 | bar_name, expected_poles |
| part_name_match | 파츠명 매칭 | pe_to_part_map |
| layout_qty_match | LAYOUT 수량 비교 | layout_area_y |
| bar_pair_pole_check | BAR 쌍 POLE 합산 | expected_poles (by type) |
| schematic_cp_existence | CP 번호 확인 | cp_to_function |
| inverter_cross_check | 인버터명 크로스체크 | inverter_list |

기존 핸들러로 안 되면:
1. 사용자에게 새 핸들러 필요 안내
2. `rule_engine.py`에 함수 추가
3. CHECK_HANDLERS dict에 등록

## 금지 사항
- ⛔ 사용자 확인 없이 status를 "검수완료"로 변경 금지
- ⛔ 기존 규칙의 rule_id 변경 금지
- ⛔ 검수완료 규칙의 check 조건을 사용자 확인 없이 수정 금지
