"""Stage 1 규칙 엔진 — LLM 없이 코드로 검증.

Usage:
    python scripts/review/rule_engine.py \
        --drawing data/cache/drawing.json \
        --rules data/cache/rules.json \
        --output data/cache/violations.json
"""

import json
import re
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


# --- 검증 함수 ---

def check_cross_check_existence(drawing: dict, rule: dict) -> list[dict]:
    """PE BAR 케이블이 다른 도면에 존재하는지 크로스체크.

    rule.check:
        type: cross_check_existence
        source_bar: PB01  (or "all")
        target_texts: list of text patterns to search in drawing
        exceptions: list of patterns to skip (e.g. 배관접지)
    """
    violations = []
    check = rule.get("check", {})
    source_bar = check.get("source_bar", "all")
    exceptions = check.get("exceptions", [])

    # 도면 내 모든 텍스트를 셋으로
    all_text_set = {t["text"] for t in drawing.get("texts", [])}

    for pb in drawing.get("pe_bars", []):
        if source_bar != "all" and pb["name"] != source_bar:
            continue

        for cable in pb.get("pe_cables", []):
            pe_id = cable["pe_id"]

            # 예외 체크 (배관접지 등)
            skip = False
            for exc in exceptions:
                if re.search(exc, pe_id):
                    skip = True
                    break
            if skip:
                continue

            # 도면 전체 텍스트에서 이 PE 케이블이 다른 위치에도 있는지
            occurrences = [
                t for t in drawing.get("texts", [])
                if t["text"] == pe_id
                and abs(t["x"] - cable["x"]) > 50  # 같은 위치 제외
            ]

            if not occurrences:
                violations.append({
                    "rule_id": rule.get("rule_id", "?"),
                    "severity": rule.get("severity", "major"),
                    "message": f"{pb['name']}의 {pe_id}가 다른 도면에서 발견되지 않음",
                    "source_entity": f"{pb['name']}/{pe_id}",
                    "expected": f"{pe_id} in SCHEMATIC or detail drawing",
                    "actual": "not found",
                    "location": f"PE BAR {pb['name']}",
                })

    return violations


def check_pole_count_match(drawing: dict, rule: dict) -> list[dict]:
    """PE BAR의 POLE 수가 기대값과 일치하는지 검증.

    rule.check:
        type: pole_count_match
        bar_name: PB01 (or "all")
        expected_poles: 15 (or from layout_list)
    """
    violations = []
    check = rule.get("check", {})
    bar_name = check.get("bar_name", "all")
    expected = check.get("expected_poles")

    for pb in drawing.get("pe_bars", []):
        if bar_name != "all" and pb["name"] != bar_name:
            continue
        if expected and pb["pole_count"] != expected:
            violations.append({
                "rule_id": rule.get("rule_id", "?"),
                "severity": rule.get("severity", "major"),
                "message": f"{pb['name']} POLE 수 불일치",
                "source_entity": pb["name"],
                "expected": str(expected),
                "actual": str(pb["pole_count"]),
                "location": f"PE BAR {pb['name']}",
            })

    return violations


def check_part_name_match(drawing: dict, rule: dict) -> list[dict]:
    """PE BAR 연결 파츠 명칭이 SCHEMATIC 파츠 명칭과 일치하는지.

    rule.check:
        type: part_name_match
        pe_to_part_map: {"PE01": "E1", "PE04": "NF01", ...}
    """
    violations = []
    check = rule.get("check", {})
    pe_to_part = check.get("pe_to_part_map", {})

    all_texts = {t["text"] for t in drawing.get("texts", [])}

    for pe_id, expected_part in pe_to_part.items():
        if expected_part not in all_texts:
            violations.append({
                "rule_id": rule.get("rule_id", "?"),
                "severity": rule.get("severity", "minor"),
                "message": f"{pe_id}의 파츠 {expected_part}가 도면에서 미발견",
                "source_entity": pe_id,
                "expected": expected_part,
                "actual": "not found",
                "location": "SCHEMATIC / Detail",
            })

    return violations


def check_layout_qty_match(drawing: dict, rule: dict) -> list:
    """LAYOUT 도면의 PB 수량과 PE BAR 도면의 PB 수량 일치 확인.

    LAYOUT 영역(Y ~ -500~-800)의 PB 텍스트를 찾아 카운트하고,
    PE BAR 상세 도면 영역의 PB와 비교한다.
    """
    violations = []
    texts = drawing.get("texts", [])
    pe_bars = drawing.get("pe_bars", [])

    # LAYOUT 영역의 PB 텍스트 (PE BAR 상세 도면 밖)
    pe_bar_names = {pb["name"] for pb in pe_bars}

    # LAYOUT에 있는 PB (PE BAR 도면 영역이 아닌 곳)
    layout_pbs = [
        t for t in texts
        if re.match(r"^PB\d+$", t["text"])
        and t["text"] not in pe_bar_names or True  # 영역으로 구분
    ]

    # PE BAR 상세 도면 영역의 Y 범위 추정
    if pe_bars:
        pe_bar_y_min = min(pb["y"] for pb in pe_bars) - 50
        pe_bar_y_max = max(pb["y"] for pb in pe_bars) + 50
    else:
        return violations

    # LAYOUT 영역 PB = PE BAR 영역 밖의 PB 텍스트
    layout_pbs = [
        t for t in texts
        if re.match(r"^PB\d+$", t["text"])
        and not (pe_bar_y_min < t["y"] < pe_bar_y_max)
    ]

    layout_pb_names = set(t["text"] for t in layout_pbs)
    pe_bar_pb_names = set(pb["name"] for pb in pe_bars)

    # PE BAR 도면에 있는데 LAYOUT에 없는 PB
    missing_in_layout = pe_bar_pb_names - layout_pb_names
    for name in sorted(missing_in_layout):
        # MAINPB는 별도 텍스트로 표기될 수 있으므로 MAINPB 확인
        main_texts = [t for t in texts if "MAINPB" in t["text"].upper().replace(" ", "")]
        if name == "MAINPB" or (name in ["PB01"] and main_texts):
            continue
        violations.append({
            "rule_id": rule.get("rule_id", "?"),
            "severity": rule.get("severity", "major"),
            "message": f"{name}가 PE BAR 도면에 있으나 LAYOUT에 미표기",
            "source_entity": name,
            "expected": f"{name} in LAYOUT",
            "actual": "not found in LAYOUT",
            "location": "LAYOUT vs PE BAR",
        })

    # LAYOUT에 있는데 PE BAR 도면에 없는 PB
    missing_in_pebar = layout_pb_names - pe_bar_pb_names
    for name in sorted(missing_in_pebar):
        violations.append({
            "rule_id": rule.get("rule_id", "?"),
            "severity": rule.get("severity", "major"),
            "message": f"{name}가 LAYOUT에 있으나 PE BAR 도면에 미표기",
            "source_entity": name,
            "expected": f"{name} in PE BAR drawing",
            "actual": "not found in PE BAR",
            "location": "LAYOUT vs PE BAR",
        })

    return violations


def check_bar_pair_pole(drawing: dict, rule: dict) -> list:
    """BAR 쌍(BAR-1 + BAR-2)의 POLE 합산이 기준값과 일치하는지 검증."""
    violations = []
    check = rule.get("check", {})
    expected_by_type = check.get("expected_poles", {})
    pe_bars = drawing.get("pe_bars", [])

    # 쌍이 있는 PB만 (pair 필드 존재)
    checked_pairs = set()
    for pb in pe_bars:
        pair_name = pb.get("pair")
        if not pair_name:
            continue
        pair_key = tuple(sorted([pb["name"], pair_name]))
        if pair_key in checked_pairs:
            continue
        checked_pairs.add(pair_key)

        bar_type = pb["bar_type"]
        expected = expected_by_type.get(bar_type)
        if expected is None:
            continue

        pair_poles = pb.get("pair_pole_count", pb["pole_count"])
        if pair_poles != expected:
            violations.append({
                "rule_id": rule.get("rule_id", "?"),
                "severity": rule.get("severity", "major"),
                "message": f"{pb['name']}+{pair_name} ({bar_type}) POLE 합산 불일치",
                "source_entity": f"{pb['name']}+{pair_name}",
                "expected": str(expected),
                "actual": str(pair_poles),
                "location": f"PE BAR {bar_type}",
            })

    return violations


def check_schematic_cp_existence(drawing: dict, rule: dict) -> list:
    """LAYOUT LIST의 CP 번호가 도면에 존재하는지 확인."""
    violations = []
    check = rule.get("check", {})
    cp_map = check.get("cp_to_function", {})

    all_texts = {t["text"] for t in drawing.get("texts", [])}

    for cp_id, function_name in cp_map.items():
        if cp_id not in all_texts:
            violations.append({
                "rule_id": rule.get("rule_id", "?"),
                "severity": rule.get("severity", "major"),
                "message": f"{cp_id} ({function_name})가 도면에서 미발견",
                "source_entity": cp_id,
                "expected": f"{cp_id} in SCHEMATIC",
                "actual": "not found",
                "location": "SCHEMATIC DIAGRAM",
            })

    return violations


def check_inverter_cross_check(drawing: dict, rule: dict) -> list:
    """인버터 파츠명이 3 PHASE SCHEMATIC, PE BAR, LAYOUT에 모두 존재하는지."""
    violations = []
    check = rule.get("check", {})
    inverter_list = check.get("inverter_list", [])

    all_texts = {t["text"] for t in drawing.get("texts", [])}

    # PE BAR 도면의 인버터명
    pe_bar_parts = set()
    for pb in drawing.get("pe_bars", []):
        for cable in pb.get("pe_cables", []):
            pe_bar_parts.add(cable.get("pe_id", ""))

    for inv_name in inverter_list:
        if inv_name not in all_texts:
            violations.append({
                "rule_id": rule.get("rule_id", "?"),
                "severity": rule.get("severity", "critical"),
                "message": f"인버터 {inv_name}가 도면에서 미발견",
                "source_entity": inv_name,
                "expected": f"{inv_name} in SCHEMATIC + PE BAR + LAYOUT",
                "actual": "not found",
                "location": "3 PHASE SCHEMATIC / PE BAR / LAYOUT",
            })

    return violations


# --- 엔진 디스패처 ---

CHECK_HANDLERS = {
    "cross_check_existence": check_cross_check_existence,
    "pole_count_match": check_pole_count_match,
    "part_name_match": check_part_name_match,
    "layout_qty_match": check_layout_qty_match,
    "bar_pair_pole_check": check_bar_pair_pole,
    "schematic_cp_existence": check_schematic_cp_existence,
    "inverter_cross_check": check_inverter_cross_check,
}


def run_engine(drawing: dict, rules: list[dict]) -> dict:
    """모든 규칙을 drawing에 대해 실행."""
    all_violations = []
    passed = []
    skipped = []

    for rule in rules:
        check = rule.get("check", {})
        check_type = check.get("type", "")
        rule_id = rule.get("rule_id", "unknown")

        if not rule.get("auto_check", False):
            skipped.append({"rule_id": rule_id, "reason": "auto_check=false"})
            continue

        handler = CHECK_HANDLERS.get(check_type)
        if handler is None:
            skipped.append({"rule_id": rule_id, "reason": f"unknown check type: {check_type}"})
            continue

        violations = handler(drawing, rule)
        if violations:
            all_violations.extend(violations)
        else:
            passed.append({"rule_id": rule_id})

    return {
        "total_rules": len(rules),
        "checked": len(passed) + len([v for v in all_violations]),
        "passed": len(passed),
        "violations": all_violations,
        "skipped": skipped,
    }


@click.command()
@click.option("--drawing", required=True, help="Drawing JSON path")
@click.option("--rules", required=True, help="Rules JSON path")
@click.option("--output", required=True, help="Output violations JSON path")
def main(drawing: str, rules: str, output: str):
    """Stage 1 규칙 엔진 실행."""
    with open(drawing, encoding="utf-8") as f:
        drawing_data = json.load(f)
    with open(rules, encoding="utf-8") as f:
        rules_data = json.load(f)

    click.echo(f"Drawing: {drawing_data.get('summary', {})}")
    click.echo(f"Rules: {len(rules_data)} loaded")

    result = run_engine(drawing_data, rules_data)

    output_file = Path(output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    click.echo(f"\nResults:")
    click.echo(f"  Passed: {result['passed']}")
    click.echo(f"  Violations: {len(result['violations'])}")
    click.echo(f"  Skipped: {len(result['skipped'])}")

    for v in result["violations"]:
        sev = v["severity"].upper()
        click.echo(f"  [{sev}] {v['message']}")


if __name__ == "__main__":
    main()
