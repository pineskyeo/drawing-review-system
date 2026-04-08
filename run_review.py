"""도면 검토 전체 파이프라인 — 원커맨드 실행.

Usage:
    python run_review.py input.dwg
    python run_review.py input.dxf
    python run_review.py input.dxf --model claude --model-name claude-haiku-4-5-20251001
    python run_review.py input.dxf --skip-llm
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS = PROJECT_ROOT / "scripts"

# 기본 LLM 모델 (환경변수 또는 여기서 변경)
DEFAULT_LLM_MODEL = os.environ.get("REVIEW_LLM_MODEL", "gemini")


def run_step(description, cmd):
    """단계별 스크립트 실행."""
    click.echo(f"\n{'='*50}")
    click.echo(f"  {description}")
    click.echo(f"{'='*50}")
    result = subprocess.run(
        [sys.executable] + cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=False,
        timeout=600,
    )
    if result.returncode != 0:
        click.echo(f"  [FAIL] {description}")
        return False
    return True


@click.command()
@click.argument("input_file")
@click.option("--name", default="", help="Drawing name for report")
@click.option("--model", default="", help="LLM model override: gemini/claude/openai/ollama")
@click.option("--model-name", default="", help="Specific model name (e.g. claude-haiku-4-5-20251001)")
@click.option("--skip-llm", is_flag=True, help="Skip LLM review even if violations found")
def main(input_file, name, model, model_name, skip_llm):
    """도면 검토 파이프라인.

    기본 동작: 위반 없으면 코드 검증만, 위반 있으면 자동으로 RAG+LLM까지.
    """
    input_path = Path(input_file).resolve()
    if not input_path.exists():
        click.echo(f"File not found: {input_path}")
        sys.exit(1)

    if not name:
        name = input_path.stem

    llm_model = model or DEFAULT_LLM_MODEL

    today = datetime.now().strftime("%Y-%m-%d")
    cache = PROJECT_ROOT / "data" / "cache"
    cache.mkdir(parents=True, exist_ok=True)

    drawing_json = str(cache / "drawing.json")
    rules_json = str(cache / "rules.json")
    violations_json = str(cache / "violations.json")
    rag_json = str(cache / "rag_results.json")
    judgments_json = str(cache / "judgments.json")
    report_path = str(PROJECT_ROOT / "reports" / today / f"{name.replace(' ', '_')}.md")

    # 도면 추출
    ok = run_step(
        "도면 추출 (DWG/DXF → JSON)",
        [str(SCRIPTS / "extract" / "extract_dwg.py"),
         "--input", str(input_path), "--output", drawing_json],
    )
    if not ok:
        sys.exit(1)

    # 규칙 로드
    ok = run_step(
        "규칙 로드 (vault → JSON)",
        [str(SCRIPTS / "review" / "load_rules.py"),
         "--vault", str(PROJECT_ROOT / "standards-vault"),
         "--output", rules_json],
    )
    if not ok:
        sys.exit(1)

    # 코드 검증
    ok = run_step(
        "코드 검증 (규칙 엔진)",
        [str(SCRIPTS / "review" / "rule_engine.py"),
         "--drawing", drawing_json, "--rules", rules_json,
         "--output", violations_json],
    )
    if not ok:
        sys.exit(1)

    # 위반 확인
    with open(violations_json, encoding="utf-8") as f:
        v_data = json.load(f)
    v_count = len(v_data.get("violations", []))

    # 위반이 있으면 자동으로 RAG + LLM까지 실행
    final_violations = violations_json

    if v_count > 0 and not skip_llm:
        # RAG 검색
        rag_ok = run_step(
            f"관련 규칙 검색 ({v_count}개 위반 항목)",
            [str(SCRIPTS / "review" / "rag_search.py"),
             "--violations", violations_json, "--output", rag_json],
        )

        if rag_ok:
            final_violations = rag_json

            # LLM 판단
            llm_cmd = [
                str(SCRIPTS / "review" / "llm_review.py"),
                "--violations", rag_json, "--output", judgments_json,
                "--model", llm_model,
            ]
            if model_name:
                llm_cmd.extend(["--model-name", model_name])

            llm_ok = run_step(
                f"LLM 판단 ({llm_model})",
                llm_cmd,
            )
            if llm_ok:
                final_violations = judgments_json
    elif v_count > 0 and skip_llm:
        click.echo(f"\n  위반 {v_count}개 발견. --skip-llm으로 LLM 판단 건너뜀.")

    # 리포트 생성
    run_step(
        "리포트 생성",
        [str(SCRIPTS / "report" / "generate_report.py"),
         "--violations", final_violations, "--drawing", drawing_json,
         "--output", report_path, "--name", name],
    )

    # 추가 규칙 제안
    suggestions_json = str(cache / "suggestions.json")
    run_step(
        "추가 규칙 제안 분석",
        [str(SCRIPTS / "review" / "suggest_rules.py"),
         "--drawing", drawing_json, "--rules", rules_json,
         "--output", suggestions_json],
    )

    # 최종 결과
    click.echo(f"\n{'='*50}")
    click.echo(f"  검토 완료: {name}")
    click.echo(f"{'='*50}")
    if v_count == 0:
        click.echo(f"  결과: 모든 규칙 통과 ({v_data.get('total_rules', 0)}개)")
    else:
        click.echo(f"  결과: {v_count}개 위반 발견")
    click.echo(f"  리포트: {report_path}")


if __name__ == "__main__":
    main()
