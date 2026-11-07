"""Verify the Azure request remains bounded and supports reasoning deployments."""
import sys
from types import SimpleNamespace
from footfall.llm import LLM


def test_azure_request_has_limits_and_explicit_reasoning(monkeypatch):
    observed = {}
    def create(**kwargs):
        observed['request'] = kwargs
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}'))])
    def client(**kwargs):
        observed['client'] = kwargs
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setitem(sys.modules, 'openai', SimpleNamespace(AzureOpenAI=client))
    for key, value in {'AZURE_OPENAI_ENDPOINT':'https://example.openai.azure.com/',
                       'AZURE_OPENAI_API_KEY':'test-placeholder', 'AZURE_OPENAI_DEPLOYMENT':'gpt-6-luna',
                       'AZURE_OPENAI_REASONING_EFFORT':'none',
                       'AZURE_OPENAI_MAX_COMPLETION_TOKENS':'2048'}.items():
        monkeypatch.setenv(key, value)
    assert LLM('azure').complete_json('JSON only', 'ping') == {'ok': True}
    assert observed['client']['timeout'] == 60
    assert observed['client']['max_retries'] == 0
    assert observed['request']['max_completion_tokens'] == 2048
    assert observed['request']['reasoning_effort'] == 'none'
    assert 'temperature' not in observed['request']
