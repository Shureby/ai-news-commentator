"""Commentary generation — calls the LLM API with a pluggable persona to write news commentary."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from llm_client import LLMClient, Provider

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"

DEFAULT_PERSONA = "lu_xun"
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")


def _load_system_prompt(persona: str = DEFAULT_PERSONA) -> str:
    prompt_path = PROMPTS_DIR / f"{persona}_system.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Persona file not found: {prompt_path}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def _build_user_prompt(news_item: dict) -> str:
    title = news_item.get("title", "")
    summary = news_item.get("summary", "")
    link = news_item.get("link", "")

    lines = [
        "请对以下新闻撰写一篇评论。",
        "",
        f"新闻标题：{title}",
    ]
    if summary:
        lines.append(f"新闻摘要：{summary}")
    if link:
        lines.append(f"新闻链接：{link}")
    return "\n".join(lines)


def generate_commentary(
    news_item: dict,
    model: str | None = None,
    provider: str | None = None,
    base_url: str | None = None,
    persona: str = DEFAULT_PERSONA,
) -> str:
    """Generate a single commentary for a news item.

    Args:
        news_item: {"title": str, "summary": str, "link": str, "source": str}
        model: Model ID. Defaults to LLM_MODEL env var.
        provider: Backend type (anthropic / openai / openai_compat). Defaults to LLM_PROVIDER env var.
        base_url: Custom API address for routing or local models.
        persona: Commentator persona name, maps to prompts/{persona}_system.md.
    Returns:
        Generated commentary (markdown).
    """
    model = model or DEFAULT_MODEL
    provider = provider or DEFAULT_PROVIDER

    client = LLMClient(
        provider=Provider(provider),
        model=model,
        base_url=base_url,
    )
    system_prompt = _load_system_prompt(persona)
    user_prompt = _build_user_prompt(news_item)
    return client.chat(system_prompt, user_prompt)


def batch_generate(
    items: list[dict],
    model: str | None = None,
    provider: str | None = None,
    base_url: str | None = None,
    persona: str = DEFAULT_PERSONA,
) -> list[dict]:
    """Batch generate commentaries. Returns [{news: ..., commentary: ..., model: ..., persona: ...}, ...]"""
    results = []
    for item in items:
        try:
            text = generate_commentary(
                item, model=model, provider=provider, base_url=base_url, persona=persona
            )
            results.append(
                {
                    "news": item,
                    "commentary": text,
                    "model": model or DEFAULT_MODEL,
                    "persona": persona,
                }
            )
            print(f"[generate] ✓ {item['title'][:40]}...")
        except Exception as e:
            print(f"[generate] ✗ {item['title'][:40]}...: {e}", file=sys.stderr)
    return results


def save_commentary(results: list[dict]):
    """Save results to JSON and markdown files under data/."""
    import json
    from datetime import datetime

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    json_path = OUTPUT_DIR / f"output_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[generate] saved: {json_path}")

    md_path = OUTPUT_DIR / f"output_{timestamp}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        for r in results:
            persona_label = r.get("persona", "")
            f.write(f"---\n")
            f.write(f"# {r['news']['title']}\n")
            f.write(f"来源: {r['news']['source']} | 人格: {persona_label} | 模型: {r['model']}\n\n")
            f.write(r["commentary"])
            f.write("\n\n")
    print(f"[generate] saved: {md_path}")


# ── CLI ──
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI News Commentator")
    parser.add_argument("--title", type=str, help="News headline")
    parser.add_argument("--summary", type=str, default="", help="News summary")
    parser.add_argument("--link", type=str, default="", help="News link")
    parser.add_argument("--model", type=str, default=None, help="Model ID")
    parser.add_argument("--provider", type=str, default=None, help="Backend: anthropic / openai / openai_compat")
    parser.add_argument("--base-url", type=str, default=None, help="Custom API base URL for routing or local models")
    parser.add_argument("--persona", type=str, default=DEFAULT_PERSONA, help="Commentator persona name")
    args = parser.parse_args()

    if not args.title:
        print("Usage: python generate.py --title 'Headline' [--summary 'Summary'] [--link 'url'] [--persona lu_xun] [--provider openai_compat --base-url http://localhost:11434/v1]")
        sys.exit(1)

    item = {"title": args.title, "summary": args.summary, "link": args.link}
    print("Generating commentary...\n")
    result = generate_commentary(
        item,
        model=args.model,
        provider=args.provider,
        base_url=args.base_url,
        persona=args.persona,
    )
    print(result)
