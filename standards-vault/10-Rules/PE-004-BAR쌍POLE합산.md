---
rule_id: "PE-004"
title: "PE BAR 쌍 POLE 합산 검증"
status: "검수완료"
type: "numeric"
severity: "major"
category: ["PE BAR", "수량"]

check:
  type: "bar_pair_pole_check"
  expected_poles:
    1PHASE: 15
    DC: 15
    AD_SHIELD: 15
    3PHASE: 10

auto_check: true
---

# PE-004 PE BAR 쌍 POLE 합산 검증

## 원문
> 같은 도면 내 BAR-1과 BAR-2의 POLE 원 합산은 해당 타입의 기준 POLE 수와 일치해야 한다.

## 해석 노트
- PB01(BAR-1) + PB02(BAR-2) = 15P (1 PHASE)
- PB03(BAR-1) + PB04(BAR-2) = 15P (DC)
- PB05(AD BAR) + PB06(SHIELD BAR) = 15P (AD_SHIELD)
- PB10(BAR-1) + PB11(BAR-2) = 10P (3 PHASE, 그룹1, 5P x 2열)
- PB12(BAR-1) + PB13(BAR-2) = 10P (3 PHASE, 그룹2, 5P x 2열)
- 원은 한쪽 BAR에만 그려져 있으므로 쌍 합산 필요

## 관련 기준
- [[PE-002-POLE수일치]]

## 카테고리
[[PE BAR]] · [[수량]]

## 검수 체크리스트
- [x] BAR 쌍 매칭 로직 확인
- [x] WSOLVENT 샘플 검증: 1PHASE 15P, DC 15P, AD_SHIELD 15P, 3PHASE 5P

## 검수 메모
2026-04-08 검수 완료. 3 PHASE BAR는 PB10/11 + PB12/13 두 그룹이 각각 5P.
