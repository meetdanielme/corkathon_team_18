"""Small model adapter. Azure is primary; Claude is a fallback only when FOOTFALL_LLM=anthropic is set
deliberately (Daniel's call). There is no automatic fallback between providers.

Env:
  FOOTFALL_LLM=azure|anthropic|none   (default none)
  AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION
  ANTHROPIC_API_KEY, ANTHROPIC_MODEL
"""
from __future__ import annotations

import json
import os
import re


class LLMNotConfigured(Exception):
    pass


class LLM:
    def __init__(self, provider: str | None = None):
        self.provider = (provider or os.getenv("FOOTFALL_LLM", "none")).lower()
        self.calls = 0

    @property
    def enabled(self) -> bool:
        return self.provider in ("azure", "anthropic")

    def complete_json(self, system: str, user: str) -> dict:
        if not self.enabled:
            raise LLMNotConfigured("FOOTFALL_LLM is not set to azure or anthropic")
        self.calls += 1
        text = self._azure(system, user) if self.provider == "azure" else self._anthropic(system, user)
        return parse_json(text)

    def _azure(self, system: str, user: str) -> str:
        from openai import AzureOpenAI  # pip install openai

        client = AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                             api_key=os.environ["AZURE_OPENAI_API_KEY"],
                             api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"))
        r = client.chat.completions.create(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"], temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        return r.choices[0].message.content

    def _anthropic(self, system: str, user: str) -> str:
        import anthropic  # pip install anthropic

        client = anthropic.Anthropic()
        r = client.messages.create(model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"), max_tokens=2000,
                                   system=system, messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")


def parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("model returned no JSON object")
    return json.loads(m.group(0))
