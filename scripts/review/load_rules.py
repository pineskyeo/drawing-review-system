"""Obsidian vault에서 검수완료 규칙 로드.

Usage:
    python scripts/review/load_rules.py --vault standards-vault --output data/cache/rules.json
"""

import json
import sys
from pathlib import Path

import click
import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.common.config import RULES_PATH


def load_rule(file_path: Path) -> dict:
    """단일 규칙 파일에서 frontmatter + 본문 로드."""
    try:
        post = frontmatter.load(str(file_path))
    except Exception as e:
        return None

    meta = dict(post.metadata)
    meta["_file"] = str(file_path.relative_to(file_path.parent.parent))
    meta["_body"] = post.content
    return meta


def load_all_rules(vault_path: Path, status_filter: str = "검수완료") -> list:
    """vault에서 조건에 맞는 규칙 전부 로드."""
    rules_dir = vault_path / "10-Rules"
    if not rules_dir.exists():
        return []

    rules = []
    for md_file in sorted(rules_dir.glob("*.md")):
        rule = load_rule(md_file)
        if rule is None:
            continue
        if status_filter and rule.get("status") != status_filter:
            continue
        rules.append(rule)

    return rules


@click.command()
@click.option("--vault", default=str(RULES_PATH.parent), help="Vault root path")
@click.option("--status", default="검수완료", help="Filter by status")
@click.option("--output", "output_path", required=True, help="Output JSON path")
@click.option("--all", "load_all", is_flag=True, help="Load all rules regardless of status")
def main(vault: str, status: str, output_path: str, load_all: bool):
    """Vault에서 규칙 로드."""
    vault_path = Path(vault)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    status_filter = "" if load_all else status
    rules = load_all_rules(vault_path, status_filter)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    click.echo(f"Loaded {len(rules)} rules (status={status_filter or 'all'})")
    click.echo(f"Output: {output_file}")

    # 요약
    by_type = {}
    for r in rules:
        t = r.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
    for t, c in sorted(by_type.items()):
        click.echo(f"  {t}: {c}")


if __name__ == "__main__":
    main()
