"""Small model adapter. Every provider is chosen deliberately; there is no automatic fallback.

  azure      primary, when a deployment is available
  ollama     a model running locally. Free, spends no API credit and needs no key, so it is the
             option to reach for when Azure is unavailable. Requires Ollama to be running.
  anthropic  a paid fallback, only on Daniel's direction
  none       the app stays fully usable on prepared data

Env:
  FOOTFALL_LLM=azure|ollama|anthropic|none   (default none)
  AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION
  OLLAMA_HOST (default http://127.0.0.1:11434), OLLAMA_MODEL, OLLAMA_TIMEOUT_S
  ANTHROPIC_API_KEY, ANTHROPIC_MODEL
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request


DEFAULT_OLLAMA_MODEL = "qwen3:4b-instruct-2507-q4_K_M"


class LLMNotConfigured(Exception):
    pass


class LLM:
    def __init__(self, provider: str | None = None):
        self.provider = (provider or os.getenv("FOOTFALL_LLM", "none")).lower()
        self.calls = 0

    @property
    def enabled(self) -> bool:
        return self.provider in ("azure", "ollama", "anthropic")

    def complete_json(self, system: str, user: str) -> dict:
        if not self.enabled:
            raise LLMNotConfigured("FOOTFALL_LLM is not set to azure, ollama or anthropic")
        self.calls += 1
        text = {"azure": self._azure, "ollama": self._ollama,
                "anthropic": self._anthropic}[self.provider](system, user)
        return parse_json(text)

    def _azure(self, system: str, user: str) -> str:
        if limit := os.getenv("FOOTFALL_AZURE_CALL_LIMIT"):
            from . import db
            with db.connect(os.getenv("FOOTFALL_DB", "footfall.sqlite3")) as con:
                con.execute("CREATE TABLE IF NOT EXISTS ai_allowance (id INTEGER PRIMARY KEY, calls INTEGER NOT NULL)")
                reserved = con.execute("""INSERT INTO ai_allowance (id,calls) VALUES (1,1)
                    ON CONFLICT(id) DO UPDATE SET calls=calls+1 WHERE calls < ? RETURNING calls""",
                    (int(limit),)).fetchone()
                if reserved is None:
                    raise ValueError("Shared demo AI allowance reached; prepared data remains available")
        from openai import AzureOpenAI  # pip install openai

        client = AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                             api_key=os.environ["AZURE_OPENAI_API_KEY"],
                             api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
                             timeout=60, max_retries=0)
        options = {}
        if effort := os.getenv("AZURE_OPENAI_REASONING_EFFORT"):
            options["reasoning_effort"] = effort
        r = client.chat.completions.create(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            max_completion_tokens=int(os.getenv("AZURE_OPENAI_MAX_COMPLETION_TOKENS", "2048")),
            **options,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        return r.choices[0].message.content

    def _ollama(self, system: str, user: str) -> str:
        """A locally running model via Ollama's chat API. Stdlib only; no key, no billing."""
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        body = json.dumps({
            "model": os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "8192"))},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request(f"{host}/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=float(os.getenv("OLLAMA_TIMEOUT_S", "180"))) as r:
                return json.load(r)["message"]["content"]
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama unreachable at {host}: {e.reason}. Is `ollama serve` running?") from e

    def _anthropic(self, system: str, user: str) -> str:
        import anthropic  # pip install anthropic

        client = anthropic.Anthropic()
        r = client.messages.create(model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5"), max_tokens=2000,
                                   system=system, messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")


def parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("model returned no JSON object")
    return json.loads(m.group(0))
