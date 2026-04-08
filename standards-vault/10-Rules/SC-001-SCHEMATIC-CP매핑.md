---
rule_id: "SC-001"
title: "SCHEMATIC CP 번호 존재 확인"
status: "검수완료"
type: "existence"
severity: "major"
category: ["SCHEMATIC", "크로스체크"]

check:
  type: "schematic_cp_existence"
  cp_to_function:
    CP01: "TRANSFORMER"
    CP02: "Z-PURGE"
    CP03: "ON/OFF SWITCH"
    CP10: "NOISE FILTER"
    CP15: "POWER SUPPLY (EMS-1)"
    CP16: "POWER SUPPLY (EMS-2)"
    CP17: "POWER SUPPLY (CON-1)"
    CP18: "POWER SUPPLY (CON-2)"
    CP25: "PLC IN/OUT CARD"
    CP26: "PLC POWER"
    CP27: "TOUCH SCREEN"
    CP28: "UNIT INNER SENSOR"
    CP29: "TOWER LAMP & RELAY"
    CP30: "LAMP & FAN"
    CP31: "AD POWER"

auto_check: true
---

# SC-001 SCHEMATIC CP 번호 존재 확인

## 원문
> LAYOUT LIST에 기재된 CP(Circuit Protector) 번호는 SCHEMATIC DIAGRAM에 동일하게 표기되어야 한다.

## 해석 노트
- LAYOUT LIST (p11)의 CP 목록과 SCHEMATIC의 CP 번호를 대조
- CP 번호는 회로보호기로, 각 기기에 1:1 매핑됨
- cp_to_function 맵은 WSOLVENT 기준이며 프로젝트별로 다를 수 있음

## 관련 기준
- [[PE-003-파츠명칭일치]]

## 카테고리
[[SCHEMATIC]] · [[크로스체크]]

## 검수 체크리스트
- [x] LAYOUT LIST CP 목록 추출
- [x] SCHEMATIC에서 CP 텍스트 전수 검색
- [x] WSOLVENT 샘플에서 매핑 확인

## 검수 메모
2026-04-08 검수 완료.
