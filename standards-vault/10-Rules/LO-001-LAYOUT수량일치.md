---
rule_id: "LO-001"
title: "LAYOUT PB 수량 vs LAYOUT LIST 수량 일치"
status: "검수완료"
type: "numeric"
severity: "major"
category: ["LAYOUT", "수량"]

check:
  type: "layout_qty_match"
  layout_area_y: [-800, -500]
  layout_list_area_y: [-600, -400]

auto_check: true
---

# LO-001 LAYOUT PB 수량 vs LAYOUT LIST 수량 일치

## 원문
> ELECTRIC ZONE LAYOUT에서 발견된 PB 수량은 LAYOUT LIST의 해당 항목 수량과 일치해야 한다.

## 해석 노트
- LAYOUT 도면에서 PB 텍스트 위치를 찾아 개수를 셈
- MAIN PB: LAYOUT LIST에서 MAINPB 항목의 수량 = 1EA
- MAIN PB가 아닌 PB: POLE 수가 같은 PB끼리 그룹핑
  - PB 도면 형상의 작은 원 개수 = POLE 수
  - 같은 POLE 수의 PB 수량을 세서 LAYOUT LIST와 비교
- WSOLVENT 기준:
  - MAIN PB: 7P, 1EA
  - PB01-06: 15P, 6EA (CONTROL PANEL)
  - PB10-13: 5P, 4EA (INVERTER PANEL)

## 관련 기준
- [[PE-002-POLE수일치]]

## 카테고리
[[LAYOUT]] · [[수량]]

## 검수 체크리스트
- [x] LAYOUT 영역의 PB 텍스트 카운트 확인
- [x] MAIN PB 식별 로직 확인
- [x] POLE 수 기반 그룹핑 확인
- [x] WSOLVENT 샘플에서 수량 일치 확인

## 검수 메모
2026-04-08 검수 완료. LAYOUT LIST 텍스트 파싱이 복잡하여 PDF 기반 검증과 병행 권장.
