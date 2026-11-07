"""Verify the configured model returns JSON. Usage: python -m scripts.check_llm  (reads FOOTFALL_LLM etc.)"""
import sys

from footfall.config import load_env
from footfall.llm import LLM, LLMNotConfigured


def main() -> int:
    load_env()
    llm = LLM()
    try:
        out = llm.complete_json('Return JSON {"ok": true} and nothing else.', "ping")
    except LLMNotConfigured as e:
        print(f"NOT CONFIGURED: {e}")
        return 2
    except Exception as e:
        print(f"FAILED ({llm.provider}): {type(e).__name__}: {e}")
        return 1
    print(f"OK ({llm.provider}): {out}")
    return 0 if out.get("ok") is True else 1


if __name__ == "__main__":
    sys.exit(main())
