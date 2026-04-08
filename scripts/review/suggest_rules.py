"""검토 완료 후 추가 규칙 제안.

도면 데이터를 분석하여 아직 규칙으로 커버되지 않는
검토 포인트를 찾아 제안한다.

Usage:
    python scripts/review/suggest_rules.py \
        --drawing data/cache/drawing.json \
        --rules data/cache/rules.json \
        --output data/cache/suggestions.json
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def analyze_uncovered_patterns(drawing, existing_rules):
    """도면에서 발견되지만 기존 규칙이 커버하지 않는 패턴 분석."""
    suggestions = []
    texts = drawing.get("texts", [])
    pe_bars = drawing.get("pe_bars", [])
    blocks = drawing.get("blocks", [])
    circles = drawing.get("circles", [])

    # 기존 규칙이 커버하는 항목 추출
    covered_checks = set()
    for r in existing_rules:
        covered_checks.add(r.get("check", {}).get("type", ""))

    all_text_values = [t["text"] for t in texts]
    text_counter = Counter(all_text_values)

    # --- 제안 1: 케이블 굵기 크로스체크 ---
    awg_texts = [t for t in texts if re.match(r"AWG\d+", t["text"])]
    if awg_texts:
        awg_types = Counter(t["text"].split()[0] for t in awg_texts)
        suggestions.append({
            "id": "SUG-001",
            "title": "케이블 굵기(AWG) 일관성 확인",
            "description": (
                f"도면에 {len(awg_types)}종의 케이블 굵기가 사용됨: "
                f"{', '.join(f'{k}({v}개)' for k, v in awg_types.most_common(5))}. "
                "PE BAR별 연결 케이블 굵기가 기준과 맞는지 확인하는 규칙 추가 가능."
            ),
            "check_type": "cable_gauge_match",
            "priority": "major",
            "data": dict(awg_types.most_common(10)),
        })

    # --- 제안 2: CP 용량-기기 매칭 ---
    cp_texts = [t for t in texts if re.match(r"^CP\d+$", t["text"])]
    cp_amp_texts = [t for t in texts if re.match(r"LCP\d+FM \d+A", t["text"])]
    if cp_texts and cp_amp_texts and "schematic_cp_existence" in covered_checks:
        amp_types = Counter(t["text"] for t in cp_amp_texts)
        suggestions.append({
            "id": "SUG-002",
            "title": "CP 용량(A)이 기기 전류에 맞는지 확인",
            "description": (
                f"CP가 {len(cp_texts)}개, 용량 종류: "
                f"{', '.join(f'{k}({v}개)' for k, v in amp_types.most_common(5))}. "
                "CP 번호별 용량이 연결 기기의 전류 사양과 맞는지 크로스체크 가능."
            ),
            "check_type": "cp_amperage_match",
            "priority": "major",
            "data": dict(amp_types.most_common(10)),
        })

    # --- 제안 3: 센서 배리어 수량 확인 ---
    barrier_texts = [t for t in texts if re.search(r"BLB\d|SLB\d|DSB\d|LSB\d", t["text"])]
    if barrier_texts:
        barrier_types = Counter(
            re.match(r"[A-Z]+", t["text"]).group() for t in barrier_texts
            if re.match(r"[A-Z]+", t["text"])
        )
        suggestions.append({
            "id": "SUG-003",
            "title": "센서 배리어 수량 크로스체크",
            "description": (
                f"배리어 {len(barrier_texts)}개 발견: "
                f"{', '.join(f'{k}({v}개)' for k, v in barrier_types.most_common())}. "
                "LAYOUT LIST의 배리어 수량과 도면 내 배리어 수가 일치하는지 확인 가능."
            ),
            "check_type": "barrier_qty_match",
            "priority": "major",
            "data": dict(barrier_types.most_common()),
        })

    # --- 제안 4: 터미널 블록 수량 ---
    tb_texts = [t for t in texts if re.match(r"^TB\d+", t["text"])]
    if tb_texts:
        suggestions.append({
            "id": "SUG-004",
            "title": "터미널 블록(TB) 수량 확인",
            "description": (
                f"터미널 블록 {len(set(t['text'] for t in tb_texts))}종 발견. "
                "LAYOUT LIST의 TB 수량과 TERMINAL BLOCK 도면의 TB 수가 일치하는지 확인 가능."
            ),
            "check_type": "tb_qty_match",
            "priority": "minor",
            "data": {"count": len(set(t["text"] for t in tb_texts))},
        })

    # --- 제안 5: 릴레이/안전PLC 존재 확인 ---
    relay_texts = [t for t in texts if re.match(r"^(SR|RL|RR|RM|SP)\d+", t["text"])]
    if relay_texts:
        relay_types = Counter(
            re.match(r"[A-Z]+", t["text"]).group() for t in relay_texts
        )
        suggestions.append({
            "id": "SUG-005",
            "title": "릴레이/안전PLC 존재 및 수량 확인",
            "description": (
                f"릴레이/안전PLC {len(relay_texts)}개 발견: "
                f"{', '.join(f'{k}({v}개)' for k, v in relay_types.most_common())}. "
                "SCHEMATIC과 LAYOUT LIST에서 동일 수량인지 크로스체크 가능."
            ),
            "check_type": "relay_qty_match",
            "priority": "minor",
            "data": dict(relay_types.most_common()),
        })

    # --- 제안 6: PLC I/O 카드 슬롯 확인 ---
    plc_texts = [t for t in texts if re.match(r"^CJ1W-|^CP1W-", t["text"])]
    if plc_texts:
        plc_types = Counter(t["text"] for t in plc_texts)
        suggestions.append({
            "id": "SUG-006",
            "title": "PLC I/O 카드 모듈 수량 확인",
            "description": (
                f"PLC 모듈 {len(plc_types)}종 발견: "
                f"{', '.join(f'{k}({v}개)' for k, v in plc_types.most_common(5))}. "
                "LAYOUT LIST의 PLC 모듈 수량과 SCHEMATIC의 모듈 수가 일치하는지 확인 가능."
            ),
            "check_type": "plc_module_match",
            "priority": "major",
            "data": dict(plc_types.most_common(10)),
        })

    # --- 제안 7: 솔레노이드 밸브 수량 ---
    sv_texts = [t for t in texts if re.match(r"^SV\d+", t["text"])]
    if sv_texts:
        suggestions.append({
            "id": "SUG-007",
            "title": "솔레노이드 밸브(SV) 수량 크로스체크",
            "description": (
                f"솔레노이드 밸브 {len(set(t['text'] for t in sv_texts))}개 발견. "
                "LAYOUT LIST의 SV 수량과 SCHEMATIC의 SV 수가 일치하는지 확인 가능."
            ),
            "check_type": "sv_qty_match",
            "priority": "minor",
            "data": {"count": len(set(t["text"] for t in sv_texts))},
        })

    # --- 제안 8: 도면 번호(DWG NO) 연속성 ---
    dwg_nos = sorted(set(
        t["text"] for t in texts
        if re.match(r"^\d{2}-\d{2}$", t["text"])
    ))
    if dwg_nos:
        # 빠진 번호 찾기
        prefix_groups = {}
        for d in dwg_nos:
            prefix = d.split("-")[0]
            suffix = int(d.split("-")[1])
            prefix_groups.setdefault(prefix, []).append(suffix)

        missing = []
        for prefix, suffixes in prefix_groups.items():
            full_range = set(range(min(suffixes), max(suffixes) + 1))
            gaps = full_range - set(suffixes)
            for g in gaps:
                missing.append(f"{prefix}-{g:02d}")

        if missing:
            suggestions.append({
                "id": "SUG-008",
                "title": "도면 번호(DWG NO) 빠진 번호 확인",
                "description": (
                    f"도면 번호 {len(dwg_nos)}개 중 빠진 번호 발견: "
                    f"{', '.join(missing[:10])}. "
                    "의도적 누락인지 확인 필요."
                ),
                "check_type": "dwg_no_continuity",
                "priority": "minor",
                "data": {"missing": missing},
            })

    return suggestions


def format_suggestions_text(suggestions):
    """제안을 사람이 읽기 좋은 텍스트로 포맷."""
    if not suggestions:
        return "추가 제안 사항이 없습니다."

    lines = [f"## 추가로 확인하면 좋을 기준 ({len(suggestions)}개)\n"]
    for i, s in enumerate(suggestions, 1):
        priority_emoji = {"major": "[중요]", "minor": "[참고]"}.get(s["priority"], "")
        lines.append(f"### {i}. {s['title']} {priority_emoji}")
        lines.append(f"{s['description']}\n")

    lines.append("\n추가할 규칙이 있으면 말씀해주세요. \"응\" 또는 번호로 선택할 수 있습니다.")
    return "\n".join(lines)


@click.command()
@click.option("--drawing", required=True, help="Drawing JSON path")
@click.option("--rules", required=True, help="Rules JSON path")
@click.option("--output", default="", help="Output suggestions JSON path")
def main(drawing, rules, output):
    """도면 분석 후 추가 규칙 제안."""
    with open(drawing, encoding="utf-8") as f:
        drawing_data = json.load(f)
    with open(rules, encoding="utf-8") as f:
        rules_data = json.load(f)

    suggestions = analyze_uncovered_patterns(drawing_data, rules_data)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(suggestions, f, ensure_ascii=False, indent=2)
        click.echo(f"Suggestions saved: {out_path}")

    # 항상 텍스트로도 출력
    click.echo(format_suggestions_text(suggestions))


if __name__ == "__main__":
    main()
