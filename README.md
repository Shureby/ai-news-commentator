# AI News Commentator

Pluggable AI-powered news commentary with multiple commentator personas.

The initial persona is Lu Xun (essay style, 800–1200 characters: state the facts → dig into the root cause → end with an epigram). More personas will be added, and multi-commentator parallel discussion / debate mode is planned.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env    # Edit .env with API keys
```

### Single Commentary

```bash
python src/generate.py --title "Tourist beaten after asking smoker to stop at Shanghai Disney" --summary "A tourist was slapped and beaten after asking another visitor to stop smoking in a non-smoking area. The victim did not fight back and ultimately accepted compensation."
```

### Daily Batch

```bash
python scripts/daily_run.py              # Aggregate from RSS
python scripts/daily_run.py --hotsearch  # From Weibo hot search
python scripts/daily_run.py --top 3      # Limit quantity
```

Output is saved to `data/output_YYYYMMDD-HHMM.md`.

## Project Structure

```
├── src/
│   ├── fetch_news.py     # News aggregation (RSS / Weibo hot search)
│   ├── generate.py       # LLM-powered commentary generation
│   ├── publish.py        # WeChat Official Account publishing (WIP)
│   └── llm_client.py     # Unified LLM backend (Anthropic / OpenAI / local)
├── prompts/
│   ├── lu_xun_system.md  # Lu Xun persona system prompt
│   └── ...               # Other commentator personas (pluggable)
├── scripts/
│   └── daily_run.py      # One-click daily pipeline
├── examples/
│   └── sample_commentary.md
└── data/                 # Output archive
```

## Automation Roadmap

| Level | Description | Status |
|-------|-------------|--------|
| 1 | Manual news selection → CLI generation → manual publish | ✅ Ready |
| 2 | Python script calls API → manual publish | ✅ Ready |
| 3 | Connect to WeChat Official Account publishing API | `publish.py` scaffolded, needs `WECHAT_APP_ID/SECRET` |
| 4 | Scheduled tasks + auto review + push notifications | Planned |

## Commentator Personas

Personas are pluggable: add a new system prompt file under `prompts/` to introduce a new voice. Multi-commentator parallel discussion / debate mode is planned. See `CLAUDE.md` for details.

The Lu Xun persona is distilled from the `lu-xun-perspective` skill, based on 16 essay collections, 3 short story collections, 164 letters, 22 speeches, and 3 major debates. See [Nuwa · Skill Creation](https://github.com/alchaincyf/nuwa-skill).

## License

MIT
