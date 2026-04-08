---
rule_id: "PE-002"
title: "PE BAR POLE 수 일치"
status: "검수완료"
type: "numeric"
severity: "major"
category: ["PE BAR", "수량"]

check:
  type: "pole_count_match"
  bar_name: "all"

auto_check: true
---

# PE-002 PE BAR POLE 수 일치

## 원문
> PE BAR 도면 형상의 작은 원(POLE) 개수는 LAYOUT LIST에 기재된 POLE 수와 일치해야 한다.

## 해석 노트
- MAIN PB: 7P (원 7개)
- PB01-06: 15P (원 15개)
- PB10-13: 5P (원 5개)
- 작은 원 = 반지름 약 1.5 단위의 CIRCLE 엔티티
- X 좌표 기준으로 같은 PB에 속하는 원을 그룹핑

## 관련 기준
- [[PE-001-케이블크로스체크]]
- [[LO-001-LAYOUT수량일치]]

## 카테고리
[[PE BAR]] · [[수량]]

## 검수 체크리스트
- [x] DWG에서 원 반지름 1.0~2.0 필터링 확인
- [x] X 좌표 그룹핑 로직 확인
- [x] WSOLVENT 샘플에서 MAIN PB 7P 확인
- [x] PB01-06 각 15P 확인
- [x] PB10-13 각 5P 확인

## 검수 메모
2026-04-08 검수 완료. DWG 파싱으로 POLE 원 자동 카운트 검증됨.
