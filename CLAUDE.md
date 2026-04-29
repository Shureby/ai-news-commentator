# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Info

- Repository: https://github.com/Shureby/ai-news-commentator
- Communication: Use Chinese for discussion. Code, formulas, and pseudocode that cannot be expressed in Chinese are exceptions.

## Pluggable Commentator Architecture

The current commentator persona is Lu Xun, but personas are pluggable — swap the system prompt file to switch voices. Future plans include running multiple AI commentators in parallel and even having them debate one another. Code must reserve space for this extension:

- `generate.py` must not hardcode the Lu Xun path; the system prompt source should be configurable.
- Each persona gets one file under `prompts/` (e.g. `lu_xun_system.md`, `wang_xiaobo_system.md`). `daily_run.py` selects via `--persona`.
- Multi-commentator mode requires generating multiple commentaries for the same news item, so `batch_generate()` input should be `[(news_item, persona_name), ...]` or equivalent.

## Commands

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env   # Edit .env with API keys and LLM backend config

# Single commentary (default: Anthropic + Lu Xun persona)
python src/generate.py --title "Headline" --summary "Summary"

# Single commentary with custom persona / provider / model
python src/generate.py --title "..." --persona lu_xun --provider openai --model gpt-4o
python src/generate.py --title "..." --provider openai_compat --base-url http://localhost:11434/v1 --model qwen2.5:7b

# Daily batch
python scripts/daily_run.py
python scripts/daily_run.py --hotsearch                    # Weibo hot search instead of RSS
python scripts/daily_run.py --top 3                        # Limit to N items
python scripts/daily_run.py --persona lu_xun               # Select persona
python scripts/daily_run.py --provider openai_compat \     # Local model
    --base-url http://localhost:11434/v1 --model qwen2.5:7b
```

No linter, formatter, or test runner is configured.

## Architecture

A 3-stage pipeline: fetch news → generate commentary via LLM → (optionally) publish to a WeChat Official Account.

**LLM Backend** (`src/llm_client.py`)
- Unified `LLMClient` wrapping three providers: `anthropic` (Anthropic SDK), `openai` (OpenAI SDK), `openai_compat` (OpenAI SDK pointed at a custom base_url, covering local models: llama.cpp / vllm / ollama / LM Studio).
- All providers support configuring a proxy/routing address via `base_url` parameter or environment variables.
- Default backend and model are set via `LLM_PROVIDER` and `LLM_MODEL` env vars.

**Stage 1 — Fetch & Filter** (`src/fetch_news.py`)
- Aggregates news from 6 hardcoded RSS sources (The Paper, Caixin, 36Kr, GeekPark, Huxiu, CLS Telegraph) and optionally Weibo hot search.
- Filters candidates through two keyword lists: `LU_XUN_KEYWORDS` (topics worth commenting on — conflict, labor, education, censorship, etc.) and `LU_XUN_UNFIT_KEYWORDS` (pure finance, medicine, tech, sports, weather — automatically excluded).
- `select_news()` returns the top N candidates that pass the keyword filter.

**Stage 2 — Generate** (`src/generate.py`)
- `_load_system_prompt(persona)` loads `prompts/{persona}_system.md`, defaulting to `lu_xun`. Persona is switched via `--persona`.
- `generate_commentary()` creates an `LLMClient` with the given provider/model/base_url, then calls `client.chat(system, user)`.
- The user prompt provides only news facts (title, summary, link). All writing style and structural requirements are defined in the system prompt.
- Output is saved to `data/output_YYYYMMDD-HHMM.md` and `.json`.

**Stage 3 — Publish** (`src/publish.py`)
- `WeChatClient` manages access token lifecycle (fetch, cache with 5-minute safety margin, refresh).
- Creates a draft via `cgi-bin/draft/add`, then publishes via `cgi-bin/freepublish/submit`.
- `_simple_md_to_html()` does a naive markdown→HTML conversion. Requires `WECHAT_APP_ID` and `WECHAT_APP_SECRET` in `.env`. Not yet wired into `daily_run.py`.

**Orchestrator** (`scripts/daily_run.py`)
- Chains the 3 stages. Adds `src/` to `sys.path`. Passes `--provider`, `--base-url`, `--model`, `--persona` through to `batch_generate()`.

## Key Design Details

- **Keyword filtering is the only selection mechanism.** The `LU_XUN_KEYWORDS` / `LU_XUN_UNFIT_KEYWORDS` lists in `fetch_news.py` are the sole gate. Adjusting what gets picked for commentary means editing those lists.
- **System prompt is the product.** The entire writing voice lives in `prompts/{persona}_system.md`. Changes to tone, structure, or subject matter should happen there, not in the generation code. The user prompt is neutral — just news facts.
- **All providers support configurable base_url.** `ANTHROPIC_BASE_URL`, `OPENAI_BASE_URL`, `LLM_BASE_URL` env vars plus `--base-url` CLI flag enable access through proxies and routing layers.
- **All local models use openai_compat.** llama.cpp server, vllm, ollama, and LM Studio all expose `/v1/chat/completions`. They are accessed uniformly via the OpenAI SDK + custom base_url.
- **Error handling is print-and-continue.** In batch mode, individual failures are printed to stderr and the loop continues. There is no retry logic.
