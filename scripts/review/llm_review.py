"""Stage 3: LLM 판단 — 해석 기준에 대해 LLM으로 위반 여부 판단.

멀티 모델 지원: Gemini Flash, Claude, GPT, Ollama(로컬)

Usage:
    python scripts/review/llm_review.py \
        --violations data/cache/violations.json \
        --vault standards-vault \
        --output data/cache/judgments.json \
        --model gemini
"""

import json
import os
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.common.config import VAULT_PATH


# --- 모델 프로바이더 ---

class LLMProvider:
    """LLM 프로바이더 베이스 클래스."""

    def judge(self, prompt):
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """Google Gemini Flash (무료 티어)."""

    def __init__(self, model_name="gemini-2.0-flash"):
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 환경변수를 설정하세요")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name

    def judge(self, prompt):
        response = self.model.generate_content(prompt)
        return response.text


class ClaudeProvider(LLMProvider):
    """Anthropic Claude."""

    def __init__(self, model_name="claude-sonnet-4-20250514"):
        import anthropic
        self.client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용
        self.model_name = model_name

    def judge(self, prompt):
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text


class OpenAIProvider(LLMProvider):
    """OpenAI GPT."""

    def __init__(self, model_name="gpt-4o-mini"):
        import openai
        self.client = openai.OpenAI()  # OPENAI_API_KEY 환경변수 사용
        self.model_name = model_name

    def judge(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content


class OllamaProvider(LLMProvider):
    """Ollama 로컬 LLM."""

    def __init__(self, model_name="llama3"):
        import openai
        self.client = openai.OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
        self.model_name = model_name

    def judge(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content


PROVIDERS = {
    "gemini": GeminiProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def get_provider(model_key, model_name=None):
    """모델 키로 프로바이더 인스턴스 생성."""
    if model_key not in PROVIDERS:
        raise ValueError(f"Unknown model: {model_key}. Options: {list(PROVIDERS.keys())}")
    cls = PROVIDERS[model_key]
    if model_name:
        return cls(model_name=model_name)
    return cls()


# --- 프롬프트 생성 ---

def build_judgment_prompt(violation, related_rules):
    """위반 항목 + 관련 규칙으로 LLM 판단 프롬프트 생성."""
    rules_text = ""
    for r in related_rules:
        rules_text += f"\n### 규칙 {r.get('rule_id', '?')}\n"
        rules_text += r.get("document_preview", "") + "\n"

    prompt = f"""당신은 건축/설비 도면 검토 전문가입니다.

아래 위반 후보 항목을 관련 규칙과 대조하여 판단해주세요.

## 위반 후보
- 규칙 ID: {violation.get('rule_id', '?')}
- 대상: {violation.get('source_entity', '?')}
- 내용: {violation.get('message', '?')}
- 기대값: {violation.get('expected', '?')}
- 실제값: {violation.get('actual', '?')}
- 위치: {violation.get('location', '?')}

## 관련 기준
{rules_text}

## 판단 요청
다음 JSON 형식으로만 답변하세요:
{{
    "judgment": "위반" | "정상" | "검토필요",
    "confidence": 0.0~1.0,
    "reason": "판단 근거 1~2문장"
}}
"""
    return prompt


def parse_judgment(response_text):
    """LLM 응답에서 JSON 판단 결과 파싱."""
    import re
    # JSON 블록 추출
    match = re.search(r'\{[^{}]*"judgment"[^{}]*\}', response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {
        "judgment": "검토필요",
        "confidence": 0.0,
        "reason": f"LLM 응답 파싱 실패: {response_text[:200]}",
    }


# --- 메인 로직 ---

def run_llm_review(violations_data, provider, top_k_rules=5):
    """해석 기준 위반 항목에 대해 LLM 판단 실행."""
    violations = violations_data.get("violations", [])

    judgments = []
    for v in violations:
        related = v.get("related_rules", [])[:top_k_rules]

        prompt = build_judgment_prompt(v, related)

        try:
            response = provider.judge(prompt)
            judgment = parse_judgment(response)
        except Exception as e:
            judgment = {
                "judgment": "검토필요",
                "confidence": 0.0,
                "reason": f"LLM 호출 실패: {str(e)[:100]}",
            }

        judgments.append({
            **v,
            "llm_judgment": judgment,
            "llm_model": getattr(provider, "model_name", "unknown"),
        })

    return {
        **violations_data,
        "violations": judgments,
        "llm_reviewed": True,
        "llm_model": getattr(provider, "model_name", "unknown"),
    }


@click.command()
@click.option("--violations", required=True, help="Violations JSON (with RAG enrichment)")
@click.option("--output", required=True, help="Output judgments JSON")
@click.option("--model", default="gemini", help="LLM provider: gemini, claude, openai, ollama")
@click.option("--model-name", default="", help="Specific model name override")
@click.option("--dry-run", is_flag=True, help="Show prompts without calling LLM")
def main(violations, output, model, model_name, dry_run):
    """Stage 3: LLM 판단 실행."""
    with open(violations, encoding="utf-8") as f:
        violations_data = json.load(f)

    v_count = len(violations_data.get("violations", []))
    if v_count == 0:
        click.echo("No violations to judge. Skipping LLM review.")
        # 그대로 출력
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(violations_data, f, ensure_ascii=False, indent=2)
        return

    click.echo(f"Violations to judge: {v_count}")
    click.echo(f"Model: {model}" + (f" ({model_name})" if model_name else ""))

    if dry_run:
        for v in violations_data["violations"]:
            prompt = build_judgment_prompt(v, v.get("related_rules", []))
            click.echo(f"\n--- {v.get('source_entity', '?')} ---")
            click.echo(prompt[:500])
        return

    provider = get_provider(model, model_name or None)
    result = run_llm_review(violations_data, provider)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    click.echo(f"Output: {out_path}")
    for v in result["violations"]:
        j = v.get("llm_judgment", {})
        click.echo(f"  [{j.get('judgment', '?')}] {v.get('source_entity', '?')}: {j.get('reason', '')}")


if __name__ == "__main__":
    main()
