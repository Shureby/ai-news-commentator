# CLAUDE.chs.md

本文件为 `CLAUDE.md` 的简体中文对照翻译。以英文原版为准。

## 项目信息

- 仓库地址：https://github.com/Shureby/ai-news-commentator
- 交流语言：尽量使用中文，代码或无法用中文表达的公式/伪代码除外。

## 评论员可插拔架构

当前使用鲁迅人格，但评论员是可插拔的——更换 System Prompt 文件即可切换人格。未来计划引入多个AI新闻评论员并行、甚至相互辩论的模式。编写代码时需预留扩展空间：

- `generate.py` 不应硬编码鲁迅路径；system prompt 来源应是可配置的。
- `prompts/` 目录下每个评论员人格一个文件（如 `lu_xun_system.md`、`wang_xiaobo_system.md`）。`daily_run.py` 通过 `--persona` 参数选择。
- 多评论员模式需要支持同一条新闻生成多份评论，因此 `batch_generate()` 的输入应为 `[(news_item, persona_name), ...]` 或等价结构。

## 命令

```bash
# 安装
pip install -r requirements.txt
cp .env.example .env   # 编辑 .env，填入 API Key 和 LLM 后端配置

# 单条生成（默认：Anthropic + 鲁迅人格）
python src/generate.py --title "新闻标题" --summary "新闻摘要"

# 单条生成（自定义人格 / 后端 / 模型）
python src/generate.py --title "..." --persona lu_xun --provider openai --model gpt-4o
python src/generate.py --title "..." --provider openai_compat --base-url http://localhost:11434/v1 --model qwen2.5:7b

# 每日批量
python scripts/daily_run.py
python scripts/daily_run.py --hotsearch                    # 微博热搜代替 RSS
python scripts/daily_run.py --top 3                        # 限制数量
python scripts/daily_run.py --persona lu_xun               # 指定人格
python scripts/daily_run.py --provider openai_compat \     # 本地模型
    --base-url http://localhost:11434/v1 --model qwen2.5:7b
```

未配置 linter、formatter 或 test runner。

## 架构

三阶段流水线：采集新闻 → 通过 LLM 生成评论 → （可选）发布到微信公众号。

**LLM 后端** (`src/llm_client.py`)
- 统一的 `LLMClient` 封装三种 provider：`anthropic`（Anthropic SDK）、`openai`（OpenAI SDK）、`openai_compat`（OpenAI SDK 指向自定义 base_url，覆盖 llama.cpp / vllm / ollama / LM Studio 等本地模型）。
- 所有 provider 均支持通过 `base_url` 参数或环境变量配置代理/路由地址。
- 通过 `LLM_PROVIDER` 和 `LLM_MODEL` 环境变量设置默认后端和模型。

**第一阶段 — 采集与筛选** (`src/fetch_news.py`)
- 从 6 个硬编码 RSS 源（澎湃、财新、36氪、极客公园、虎嗅、财联社）聚合新闻，可选微博热搜。
- 通过两个关键词列表筛选：`LU_XUN_KEYWORDS`（值得评论的话题——冲突、劳工、教育、审查等）和 `LU_XUN_UNFIT_KEYWORDS`（纯金融、医学、技术、体育、天气——自动排除）。
- `select_news()` 返回通过关键词筛选的前 N 条候选。

**第二阶段 — 生成** (`src/generate.py`)
- `_load_system_prompt(persona)` 加载 `prompts/{persona}_system.md`，默认为 `lu_xun`。通过 `--persona` 切换人格。
- `generate_commentary()` 创建 `LLMClient`，传入 provider/model/base_url，调用 `client.chat(system, user)`。
- 用户提示词只提供新闻事实（标题、摘要、链接）。所有写作风格和结构要求均由 system prompt 定义。
- 输出保存到 `data/output_YYYYMMDD-HHMM.md` 和 `.json`。

**第三阶段 — 发布** (`src/publish.py`)
- `WeChatClient` 管理 access token 生命周期（获取、缓存并预留 5 分钟安全余量、刷新）。
- 通过 `cgi-bin/draft/add` 创建草稿，再通过 `cgi-bin/freepublish/submit` 发布。
- `_simple_md_to_html()` 做简单的 markdown→HTML 转换。需要在 `.env` 中配置 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`。尚未接入 `daily_run.py`。

**编排器** (`scripts/daily_run.py`)
- 串联三个阶段。将 `src/` 加入 `sys.path`。将 `--provider`、`--base-url`、`--model`、`--persona` 透传给 `batch_generate()`。

## 关键设计要点

- **关键词过滤是唯一的筛选机制。** `fetch_news.py` 中的 `LU_XUN_KEYWORDS` / `LU_XUN_UNFIT_KEYWORDS` 列表是唯一的筛选关口。调整选题范围意味着修改这些列表。
- **System prompt 即产品。** 整个写作风格存在于 `prompts/{persona}_system.md` 中。对语气、结构或主题的修改应在那里进行，而非生成代码中。用户提示词是中性的——只提供新闻事实。
- **所有 provider 均支持可配置的 base_url。** `ANTHROPIC_BASE_URL`、`OPENAI_BASE_URL`、`LLM_BASE_URL` 环境变量加 `--base-url` CLI 参数，支持通过代理和路由层访问。
- **所有本地模型均使用 openai_compat。** llama.cpp server、vllm、ollama、LM Studio 均暴露 `/v1/chat/completions` 接口，统一通过 OpenAI SDK + 自定义 base_url 调用。
- **错误处理为打印并继续。** 批量模式下，单条失败只打印到 stderr，循环继续。没有重试逻辑。
