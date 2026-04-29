"""News aggregation — fetches candidate news items from RSS feeds and hot search APIs."""

import feedparser
import requests
from datetime import datetime


# ── RSS source config ──
RSS_SOURCES = {
    "thepaper": "https://www.thepaper.cn/rss_subject.xml?subject=1003",  # The Paper · Society
    "caixin": "https://rsshub.app/caixin/latest",  # Caixin · Latest
    "36kr": "https://36kr.com/feed",  # 36Kr
    "jiguang_keji": "https://rsshub.app/geekpark/breakingnews",  # GeekPark
    "huxiu": "https://rsshub.app/huxiu/article",  # Huxiu
    "cls_telegraph": "https://rsshub.app/cls/telegraph",  # CLS Telegraph
}


def fetch_rss_news(source_key: str, max_items: int = 20) -> list[dict]:
    """Fetch news from a single RSS source."""
    url = RSS_SOURCES.get(source_key)
    if not url:
        return []

    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:max_items]:
        items.append({
            "source": source_key,
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry.get("published", ""),
        })
    return items


def fetch_all_news(max_per_source: int = 10) -> list[dict]:
    """Aggregate news from all RSS sources."""
    all_items = []
    for source_key in RSS_SOURCES:
        try:
            items = fetch_rss_news(source_key, max_per_source)
            all_items.extend(items)
        except Exception as e:
            print(f"[fetch_news] warning: {source_key} failed: {e}")
    return all_items


def fetch_weibo_hotsearch() -> list[dict]:
    """Fetch top 20 items from Weibo hot search."""
    try:
        resp = requests.get(
            "https://weibo.com/ajax/side/hotSearch", timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        data = resp.json()
        items = []
        for entry in data.get("data", {}).get("realtime", [])[:20]:
            word = entry.get("word", "")
            if word:
                items.append({
                    "source": "weibo-hotsearch",
                    "title": word,
                    "link": f"https://s.weibo.com/weibo?q={word}",
                    "summary": "",
                    "published": datetime.now().isoformat(),
                })
        return items
    except Exception as e:
        print(f"[fetch_news] Weibo hot search failed: {e}")
        return []


# ── Topic filtering ──

LU_XUN_KEYWORDS = [
    "打人", "互殴", "道歉", "和解", "赔钱", "赔偿",  # conflict & pseudo-reconciliation
    "加班", "996", "猝死", "裁员", "劳动",           # labor
    "教育", "学区", "考研", "考公", "内卷",           # youth predicament
    "彩礼", "婚姻", "生育", "养老",                   # traditional ethics
    "消费", "直播", "打赏", "炫富",                   # consumerist spectacle
    "网络暴力", "键盘侠", "围观", "反转",              # bystander culture
    "专家说", "学者称", "教授建议",                    # "gentlemen" rhetoric
    "禁止", "取缔", "整改", "下架", "封禁",           # power & censorship
    "维权", "投诉", "举报",                           # resistance
    "志愿者", "捐款", "慈善",                         # hypocrisy check
]

LU_XUN_UNFIT_KEYWORDS = [
    "股价", "上市", "融资", "财报", "期货", "币圈",    # pure finance
    "疫苗", "新药", "临床试验",                        # pure medicine
    "5G", "芯片", "算法", "AI模型",                   # pure tech
    "体育", "比赛", "冠军", "联赛",                    # pure sports
    "气象", "天气", "台风", "暴雨",                    # pure nature
]


def is_luxun_material(item: dict) -> bool:
    """Check if a news item is suitable for Lu Xun-style commentary."""
    text = item["title"] + " " + item["summary"]

    for kw in LU_XUN_UNFIT_KEYWORDS:
        if kw in text:
            return False

    for kw in LU_XUN_KEYWORDS:
        if kw in text:
            return True

    return False


def select_news(items: list[dict], top_n: int = 5) -> list[dict]:
    """Filter candidates and return the top N suitable for commentary."""
    candidates = [item for item in items if is_luxun_material(item)]
    return candidates[:top_n]
