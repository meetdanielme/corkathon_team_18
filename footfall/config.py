"""Load a local .env file into os.environ.

Design doc section 9 keeps secrets in a local .env that is never committed, and the README tells you to
copy .env.example to .env. Nothing read that file, so a filled-in .env left the LLM silently disabled.
This is a deliberately small stdlib reader: no new dependency, no interpolation, no export semantics.

Real environment variables always win, so `FOOTFALL_LLM=azure python -m scripts.check_llm` still
overrides whatever the file says.
"""
from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ENV_FILE = ".env"


def parse_env(text: str) -> dict[str, str]:
    """Parse .env text into a mapping. Later keys win."""
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            # Strip an unquoted trailing comment: `FOOTFALL_LLM=azure   # primary`.
            # Requires whitespace before the #, so a value containing # survives.
            cut = value.find(" #")
            if cut != -1:
                value = value[:cut].rstrip()
        values[key] = value
    return values


def load_env(path: str | os.PathLike[str] = DEFAULT_ENV_FILE, *, override: bool = False) -> dict[str, str]:
    """Load `path` into os.environ if it exists. Returns the names actually applied.

    A missing file is not an error: prepared mode runs with no .env at all.
    """
    file = Path(path)
    try:
        text = file.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError, PermissionError):
        return {}

    applied: dict[str, str] = {}
    for key, value in parse_env(text).items():
        if override or key not in os.environ:
            os.environ[key] = value
            applied[key] = value
    return applied
