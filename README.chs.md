# AI 新闻评论员

> 本文件为 `README.md` 的简体中文对照翻译。以英文原版为准。

可插拔的 AI 新闻评论员，支持多评论员人格。

当前首发鲁迅人格（杂文风格，800–1200 字：白描事实 → 深挖病根 → 警句收束）。后续将引入更多评论员人格，并支持多AI评论员并行讨论/辩论模式。

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env    # 编辑 .env，填入 API Key
```

### 单条生成

```bash
python src/generate.py --title "劝阻吸烟反遭掌掴 上海迪士尼游客冲突" --summary "近日一名游客在上海迪士尼劝阻另一吸烟男子，反遭对方殴打。被打者全程未还手，最终赔钱和解。"
```

### 每日批量

```bash
python scripts/daily_run.py              # 从 RSS 聚合新闻
python scripts/daily_run.py --hotsearch  # 从微博热搜
python scripts/daily_run.py --top 3      # 限制数量
```

评论生成在 `data/output_YYYYMMDD-HHMM.md`。

## 项目结构

```
├── src/
│   ├── fetch_news.py     # 新闻采集（RSS / 微博热搜）
│   ├── generate.py       # LLM 驱动评论生成
│   ├── publish.py        # 公众号发布（开发中）
│   └── llm_client.py     # 统一 LLM 后端（Anthropic / OpenAI / 本地模型）
├── prompts/
│   ├── lu_xun_system.md  # 鲁迅人格 System Prompt
│   └── ...               # 其他评论员人格（可插拔）
├── scripts/
│   └── daily_run.py      # 一键每日流水线
├── examples/
│   └── sample_commentary.md
└── data/                 # 输出存档
```

## 自动化路线

| 级别 | 内容 | 状态 |
|------|------|------|
| 1 | 手动选新闻 → CLI 生成 → 手动发布 | ✅ 已就绪 |
| 2 | Python 脚本调用 API → 手动发布 | ✅ 已就绪 |
| 3 | 对接微信公众号发布 API | `publish.py` 骨架已完成，需配置 `WECHAT_APP_ID/SECRET` |
| 4 | 定时任务 + 自动审核 + 推送通知 | 计划中 |

## 评论员人格

评论员是可插拔的：在 `prompts/` 目录下添加新的 System Prompt 文件即可引入新人格。多评论员并行讨论/辩论模式正在计划中。详见 `CLAUDE.md`。

鲁迅人格基于 `lu-xun-perspective` skill 蒸馏提炼，素材来源于 16 部杂文集、3 部小说集、164 封书信、22 场演讲和 3 场重要论战。详见 [女娲·Skill造人术](https://github.com/alchaincyf/nuwa-skill)。

## 许可证

MIT
