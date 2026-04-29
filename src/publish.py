"""WeChat Official Account publishing — connects to the WeChat public platform API.

Reference: https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/AddDraft.html

Requires developer access to a verified service account or subscription account.
"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")


class WeChatClient:
    """WeChat public platform API client."""

    BASE_URL = "https://api.weixin.qq.com/cgi-bin"

    def __init__(self):
        self._access_token = None
        self._token_expires_at = 0

    def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        resp = requests.get(
            f"{self.BASE_URL}/token",
            params={
                "grant_type": "client_credential",
                "appid": WECHAT_APP_ID,
                "secret": WECHAT_APP_SECRET,
            },
            timeout=10,
        )
        data = resp.json()
        self._access_token = data.get("access_token")
        self._token_expires_at = time.time() + data.get("expires_in", 7200) - 300
        return self._access_token

    def add_draft(self, title: str, content: str) -> str:
        """Create a draft. Returns the media_id."""
        token = self._get_access_token()
        payload = {
            "articles": [
                {
                    "title": title,
                    "content": content,
                    "content_source_url": "",
                    "need_open_comment": 1,
                    "only_fans_can_comment": 0,
                }
            ]
        }
        resp = requests.post(
            f"{self.BASE_URL}/draft/add?access_token={token}",
            json=payload,
            timeout=30,
        )
        data = resp.json()
        if "media_id" not in data:
            raise RuntimeError(f"Failed to create draft: {data}")
        return data["media_id"]

    def publish(self, media_id: str):
        """Publish a draft."""
        token = self._get_access_token()
        payload = {"media_id": media_id}
        resp = requests.post(
            f"{self.BASE_URL}/freepublish/submit?access_token={token}",
            json=payload,
            timeout=30,
        )
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"Publish failed: {data}")
        return data


def create_commentary_draft(title: str, body: str) -> str:
    """Create a WeChat draft from commentary content.

    Args:
        title: Draft title.
        body: Commentary markdown body.
    Returns:
        Draft media_id.
    """
    html_body = _simple_md_to_html(body)
    client = WeChatClient()
    return client.add_draft(title, html_body)


def _simple_md_to_html(md: str) -> str:
    """Minimal markdown → WeChat-compatible HTML."""
    paragraphs = md.strip().split("\n\n")
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith("> "):
            p = p.replace("\n> ", "\n")
            html_parts.append(
                f'<blockquote style="border-left:3px solid #333;padding-left:1em;color:#666;">{p[2:]}</blockquote>'
            )
        else:
            html_parts.append(f"<p>{p}</p>")
    return "".join(html_parts)
