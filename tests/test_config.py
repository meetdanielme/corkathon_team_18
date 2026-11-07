"""Tests for the local .env reader (footfall/config.py)."""
import os

from footfall.config import load_env, parse_env


def test_parse_env_handles_comments_quotes_and_export():
    text = "\n".join([
        "# a comment",
        "",
        "FOOTFALL_LLM=azure            # primary channel",
        "export FLASK_SECRET_KEY=shhh",
        'AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com/"',
        "AZURE_OPENAI_DEPLOYMENT='gpt-4o-demo'",
        "EMPTY=",
        "not a pair",
    ])
    assert parse_env(text) == {
        "FOOTFALL_LLM": "azure",
        "FLASK_SECRET_KEY": "shhh",
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/",
        "AZURE_OPENAI_DEPLOYMENT": "gpt-4o-demo",
        "EMPTY": "",
    }


def test_parse_env_keeps_hash_inside_a_value():
    # A key or password may legitimately contain '#'. Only " #" starts a comment.
    assert parse_env("AZURE_OPENAI_API_KEY=abc#def")["AZURE_OPENAI_API_KEY"] == "abc#def"
    assert parse_env('AZURE_OPENAI_API_KEY="abc # def"')["AZURE_OPENAI_API_KEY"] == "abc # def"


def test_load_env_does_not_override_a_real_environment_variable(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("FOOTFALL_LLM=none\nFOOTFALL_DB=from-file.sqlite3\n", encoding="utf-8")
    monkeypatch.setenv("FOOTFALL_LLM", "azure")
    monkeypatch.delenv("FOOTFALL_DB", raising=False)

    applied = load_env(env_file)

    assert os.environ["FOOTFALL_LLM"] == "azure"      # shell wins
    assert os.environ["FOOTFALL_DB"] == "from-file.sqlite3"  # file fills the gap
    assert applied == {"FOOTFALL_DB": "from-file.sqlite3"}


def test_load_env_with_override_replaces_the_environment(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("FOOTFALL_LLM=none\n", encoding="utf-8")
    monkeypatch.setenv("FOOTFALL_LLM", "azure")

    load_env(env_file, override=True)

    assert os.environ["FOOTFALL_LLM"] == "none"


def test_load_env_is_a_no_op_when_the_file_is_missing(tmp_path):
    assert load_env(tmp_path / "does-not-exist") == {}


def test_env_example_parses_to_the_documented_keys():
    # The file teammates copy to .env must round-trip through the reader.
    parsed = parse_env(open(".env.example", encoding="utf-8").read())
    assert parsed["FOOTFALL_LLM"] == "none"          # inline comment stripped
    assert parsed["FOOTFALL_DB"] == "footfall.sqlite3"
    assert parsed["AZURE_OPENAI_API_VERSION"] == "2024-10-21"
    assert parsed["AZURE_OPENAI_API_KEY"] == ""      # placeholder only, no real secret
