"""Provider selection and the local Ollama adapter. No network: urlopen is stubbed."""
import json
import io
import urllib.error

import pytest

from footfall import llm as llm_mod
from footfall.llm import LLM, LLMNotConfigured


@pytest.mark.parametrize("provider,enabled", [
    ("azure", True), ("ollama", True), ("anthropic", True), ("none", False), ("", False),
])
def test_only_named_providers_are_enabled(provider, enabled):
    assert LLM(provider).enabled is enabled


def test_disabled_provider_names_every_option(monkeypatch):
    monkeypatch.delenv("FOOTFALL_LLM", raising=False)
    with pytest.raises(LLMNotConfigured) as e:
        LLM("none").complete_json("sys", "user")
    for name in ("azure", "ollama", "anthropic"):
        assert name in str(e.value)


def test_ollama_sends_json_mode_and_returns_the_message(monkeypatch):
    sent = {}

    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=None):
        sent["url"] = req.full_url
        sent["body"] = json.loads(req.data)
        sent["timeout"] = timeout
        return Resp(json.dumps({"message": {"content": '{"ok": true}'}}).encode())

    monkeypatch.setattr(llm_mod.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434/")
    monkeypatch.setenv("OLLAMA_MODEL", "test-model")

    out = LLM("ollama").complete_json("be strict", "the page")

    assert out == {"ok": True}
    assert sent["url"] == "http://localhost:11434/api/chat"   # trailing slash trimmed
    assert sent["body"]["format"] == "json"                    # JSON mode requested
    assert sent["body"]["stream"] is False
    assert sent["body"]["options"]["temperature"] == 0         # deterministic for extraction
    assert sent["body"]["model"] == "test-model"
    assert [m["role"] for m in sent["body"]["messages"]] == ["system", "user"]


def test_ollama_counts_calls_like_the_real_adapter(monkeypatch):
    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(llm_mod.urllib.request, "urlopen",
                        lambda req, timeout=None: Resp(b'{"message": {"content": "{\\"ok\\": true}"}}'))
    model = LLM("ollama")
    model.complete_json("s", "u"); model.complete_json("s", "u")
    assert model.calls == 2


def test_ollama_unreachable_is_an_actionable_error(monkeypatch):
    def boom(req, timeout=None):
        raise urllib.error.URLError("connection refused")
    monkeypatch.setattr(llm_mod.urllib.request, "urlopen", boom)
    with pytest.raises(RuntimeError, match="Ollama unreachable"):
        LLM("ollama").complete_json("s", "u")
