"""One-click daily pipeline — aggregate news → filter → generate commentary → output markdown.

Usage:
    python scripts/daily_run.py                       # RSS aggregation, default Lu Xun + Anthropic
    python scripts/daily_run.py --hotsearch           # Weibo hot search instead of RSS
    python scripts/daily_run.py --top 3               # Limit to N items
    python scripts/daily_run.py --persona lu_xun      # Select commentator persona
    python scripts/daily_run.py --provider openai_compat --base-url http://localhost:11434/v1 --model qwen2.5:7b
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fetch_news import fetch_all_news, fetch_weibo_hotsearch, select_news
from generate import batch_generate, save_commentary, DEFAULT_PERSONA, DEFAULT_PROVIDER, DEFAULT_MODEL


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI News Daily Commentator")
    parser.add_argument("--hotsearch", action="store_true", help="Use Weibo hot search instead of RSS")
    parser.add_argument("--top", type=int, default=5, help="Number of commentaries to generate")
    parser.add_argument("--model", type=str, default=None, help="Model ID")
    parser.add_argument("--provider", type=str, default=None, help="Backend: anthropic / openai / openai_compat")
    parser.add_argument("--base-url", type=str, default=None, help="Custom API base URL for routing or local models")
    parser.add_argument("--persona", type=str, default=DEFAULT_PERSONA, help="Commentator persona name")
    args = parser.parse_args()

    model = args.model or DEFAULT_MODEL
    provider = args.provider or DEFAULT_PROVIDER
    persona = args.persona

    print("=" * 50)
    print("AI News Commentary · Daily Run")
    print(f"Persona: {persona} | Backend: {provider} | Model: {model}")
    print("=" * 50)

    # Step 1: Fetch news
    print("\n📰 Fetching news...")
    if args.hotsearch:
        items = fetch_weibo_hotsearch()
    else:
        items = fetch_all_news()

    if not items:
        print("No news items fetched. Exiting.")
        return

    print(f"   Fetched {len(items)} news items")

    # Step 2: Filter
    candidates = select_news(items, top_n=args.top)
    print(f"\n🔍 {len(candidates)} items selected for commentary:\n")
    for i, c in enumerate(candidates, 1):
        print(f"   {i}. [{c['source']}] {c['title'][:50]}")

    if not candidates:
        print("No suitable items found. Exiting.")
        return

    # Step 3: Generate
    print(f"\n✍️ Generating commentaries...\n")
    results = batch_generate(
        candidates,
        model=model,
        provider=provider,
        base_url=args.base_url,
        persona=persona,
    )

    # Step 4: Save
    print(f"\n💾 Saving results...")
    save_commentary(results)

    print("\n" + "=" * 50)
    print("Done. See data/output_*.md for results.")
    print("=" * 50)


if __name__ == "__main__":
    main()
