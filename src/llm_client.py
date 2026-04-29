"""Unified LLM client — supports Anthropic, OpenAI, and local models via OpenAI-compatible API.

Local model defaults:
  - ollama:       http://localhost:11434/v1
  - llama.cpp:    http://localhost:8080/v1
  - vllm:         http://localhost:8000/v1
  - LM Studio:    http://localhost:1234/v1
  All expose a /v1/chat/completions endpoint. Use openai_compat provider + the appropriate base_url.
"""

import os
from enum import Enum


class Provider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENAI_COMPAT = "openai_compat"


class LLMClient:
    """Unified LLM interface.

    Usage:
        # Anthropic (direct or via proxy with ANTHROPIC_BASE_URL / base_url)
        client = LLMClient(Provider.ANTHROPIC, "claude-sonnet-4-6")
        client = LLMClient(Provider.ANTHROPIC, "claude-sonnet-4-6", base_url="https://your-proxy.com/api")

        # OpenAI (direct or via proxy with OPENAI_BASE_URL / base_url)
        client = LLMClient(Provider.OPENAI, "gpt-4o")
        client = LLMClient(Provider.OPENAI, "gpt-4o", base_url="https://your-proxy.com/v1")

        # ollama
        client = LLMClient(Provider.OPENAI_COMPAT, "qwen2.5:7b", base_url="http://localhost:11434/v1")

        # vllm / llama.cpp / LM Studio
        client = LLMClient(Provider.OPENAI_COMPAT, "meta-llama-3.1-8b", base_url="http://localhost:8000/v1")
    """

    def __init__(
        self,
        provider: Provider,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.provider = provider
        self.model = model
        self._client = None
        self._api_key = api_key
        self._base_url = base_url

    def _get_client(self):
        if self._client is not None:
            return self._client

        if self.provider == Provider.ANTHROPIC:
            import anthropic

            key = self._api_key or os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("ANTHROPIC_API_KEY is not set")
            base = self._base_url or os.getenv("ANTHROPIC_BASE_URL") or None
            self._client = anthropic.Anthropic(api_key=key, base_url=base)

        elif self.provider in (Provider.OPENAI, Provider.OPENAI_COMPAT):
            import openai

            if self.provider == Provider.OPENAI:
                key = self._api_key or os.getenv("OPENAI_API_KEY")
                if not key:
                    raise ValueError("OPENAI_API_KEY is not set")
                base = self._base_url or os.getenv("OPENAI_BASE_URL") or None
            else:
                key = self._api_key or os.getenv("LLM_API_KEY") or "not-needed"
                base = self._base_url or os.getenv("LLM_BASE_URL")
                if not base:
                    raise ValueError(
                        "Local model requires LLM_BASE_URL (e.g. http://localhost:11434/v1)"
                    )

            self._client = openai.OpenAI(api_key=key, base_url=base)

        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        return self._client

    def chat(self, system: str, user_message: str, max_tokens: int = 4096) -> str:
        client = self._get_client()

        if self.provider == Provider.ANTHROPIC:
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        else:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": user_message})
            response = client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
            )
            return response.choices[0].message.content
