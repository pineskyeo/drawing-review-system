"""검토 결과를 Markdown 리포트로 생성.

Usage:
    python scripts/report/generate_report.py \
        --violations data/cache/violations.json \
        --drawing data/cache/drawing.json \
        --output reports/2026-04-08/WSOLVENT.md
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def generate_markdown(violations_data: dict, drawing_data: dict, drawing_name: str) -> str:
    """Markdown 리포트 생성 (Obsidian vault 호환)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    today = datetime.now().strftime("%Y-%m-%d")
    violations = violations_data.get("violations", [])
    passed = violations_data.get("passed", 0)
    skipped = violations_data.get("skipped", [])
    total = violations_data.get("total_rules", 0)

    critical = [v for v in violations if v["severity"] == "critical"]
    major = [v for v in violations if v["severity"] == "major"]
    minor = [v for v in violations if v["severity"] == "minor"]

    pe_bars = drawing_data.get("pe_bars", [])
    summary = drawing_data.get("summary", {})

    # 위반된 규칙 ID 수집 (링크용)
    violated_rule_ids = sorted(set(v["rule_id"] for v in violations))

    lines = []
    # Obsidian frontmatter
    lines.append("---")
    lines.append(f"type: 검토리포트")
    lines.append(f"drawing: \"{drawing_name}\"")
    lines.append(f"date: {today}")
    lines.append(f"result: {'PASS' if not violations else 'FAIL'}")
    lines.append(f"violations: {len(violations)}")
    lines.append(f"rules_applied: {total}")
    lines.append("---")
    lines.append(f"")
    lines.append(f"# 도면 검토 리포트: {drawing_name}")
    lines.append(f"")
    lines.append(f"- 검토일시: {now}")
    lines.append(f"- 소스: `{Path(drawing_data.get('source_file', 'N/A')).name}`")
    lines.append(f"- 엔티티: TEXT {summary.get('total_texts', 0)}, "
                 f"CIRCLE {summary.get('total_circles', 0)}, "
                 f"BLOCK {summary.get('total_blocks', 0)}")
    lines.append(f"")

    # 요약
    lines.append(f"## 1. 요약")
    lines.append(f"")
    lines.append(f"| 항목 | 수 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 적용 규칙 | {total} |")
    lines.append(f"| 통과 | {passed} |")
    lines.append(f"| 위반 (Critical) | {len(critical)} |")
    lines.append(f"| 위반 (Major) | {len(major)} |")
    lines.append(f"| 위반 (Minor) | {len(minor)} |")
    lines.append(f"| 건너뜀 | {len(skipped)} |")
    lines.append(f"")

    if not violations:
        lines.append(f"> 모든 규칙을 통과했습니다.")
        lines.append(f"")

    # Critical
    if critical:
        lines.append(f"## 2. Critical 위반")
        lines.append(f"")
        lines.append(f"| 규칙 | 대상 | 내용 | 기대값 | 실제값 |")
        lines.append(f"|------|------|------|--------|--------|")
        for v in critical:
            rid = v['rule_id']
            lines.append(f"| [[{rid}]] | {v['source_entity']} | "
                        f"{v['message']} | {v['expected']} | {v['actual']} |")
        lines.append(f"")

    # Major
    if major:
        lines.append(f"## 3. Major 위반")
        lines.append(f"")
        lines.append(f"| 규칙 | 대상 | 내용 |")
        lines.append(f"|------|------|------|")
        for v in major:
            rid = v['rule_id']
            lines.append(f"| [[{rid}]] | {v['source_entity']} | {v['message']} |")
        lines.append(f"")

    # Minor
    if minor:
        lines.append(f"## 4. Minor 위반")
        lines.append(f"")
        for v in minor:
            rid = v['rule_id']
            lines.append(f"- [[{rid}]] {v['source_entity']}: {v['message']}")
        lines.append(f"")

    # PE BAR 현황
    if pe_bars:
        lines.append(f"## 5. PE BAR 현황")
        lines.append(f"")
        lines.append(f"| PB | 타입 | 쌍 | POLE (개별) | POLE (쌍합) | PE 케이블 수 |")
        lines.append(f"|-----|------|-----|------------|------------|-------------|")
        for pb in sorted(pe_bars, key=lambda p: p["name"]):
            pair = pb.get("pair", "-")
            pair_poles = pb.get("pair_pole_count", "-")
            lines.append(f"| {pb['name']} | {pb['bar_type']} | {pair} | "
                        f"{pb['pole_count']} | {pair_poles} | "
                        f"{len(pb.get('pe_cables', []))} |")
        lines.append(f"")

    # Skipped
    if skipped:
        lines.append(f"## 6. 건너뛴 규칙")
        lines.append(f"")
        for s in skipped:
            lines.append(f"- {s['rule_id']}: {s['reason']}")
        lines.append(f"")

    # 적용 규칙 목록 (Obsidian 링크)
    all_rule_ids = sorted(set(
        [v["rule_id"] for v in violations]
        + [p.get("rule_id", "") for p in violations_data.get("passed_details", [])]
    ))
    # violations_data에 passed_details가 없을 수 있으므로 규칙 ID를 violations + skipped에서 수집
    checked_rules = sorted(set(
        [v["rule_id"] for v in violations]
    ))

    lines.append(f"## 연결")
    lines.append(f"")
    if violated_rule_ids:
        lines.append(f"위반 규칙: {', '.join(f'[[{r}]]' for r in violated_rule_ids)}")
    else:
        lines.append(f"위반 규칙 없음")
    lines.append(f"")

    return "\n".join(lines)


@click.command()
@click.option("--violations", required=True, help="Violations JSON path")
@click.option("--drawing", required=True, help="Drawing JSON path")
@click.option("--output", required=True, help="Output Markdown path (also copies to vault)")
@click.option("--name", default="", help="Drawing name for report title")
def main(violations: str, drawing: str, output: str, name: str):
    """검토 리포트 생성. vault 40-Reviews/에도 자동 저장."""
    with open(violations, encoding="utf-8") as f:
        violations_data = json.load(f)
    with open(drawing, encoding="utf-8") as f:
        drawing_data = json.load(f)

    if not name:
        name = Path(drawing_data.get("source_file", "unknown")).stem

    report = generate_markdown(violations_data, drawing_data, name)

    # 1. reports/ 폴더에 저장
    output_file = Path(output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding="utf-8")
    click.echo(f"Report: {output_file}")

    # 2. vault 40-Reviews/에도 저장
    vault_reviews = Path(__file__).resolve().parent.parent.parent / "standards-vault" / "40-Reviews"
    if vault_reviews.exists():
        today = datetime.now().strftime("%Y-%m-%d")
        vault_file = vault_reviews / f"{today}-{name.replace(' ', '_').replace('/', '_')}.md"
        vault_file.write_text(report, encoding="utf-8")
        click.echo(f"Vault:  {vault_file}")

    v_count = len(violations_data.get("violations", []))
    if v_count == 0:
        click.echo("Result: ALL PASSED")
    else:
        click.echo(f"Result: {v_count} violations found")


if __name__ == "__main__":
    main()
