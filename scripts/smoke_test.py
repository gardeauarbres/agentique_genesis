"""Minimal smoke test for a Streamlit + LangChain Core stack.

Usage:
    python scripts/smoke_test.py
"""

from __future__ import annotations

import importlib
import platform
import sys

MIN_PYTHON = (3, 10)


def check_python_version() -> None:
    current = sys.version_info[:3]
    if current < MIN_PYTHON:
        raise RuntimeError(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required for this project; got {current}."
        )


def check_import(module_name: str) -> str:
    module = importlib.import_module(module_name)
    return getattr(module, "__version__", "unknown")


def main() -> int:
    check_python_version()

    print(f"Python: {platform.python_version()}")
    for mod in ("streamlit", "langchain_core"):
        version = check_import(mod)
        print(f"✅ import {mod} ({version})")

    # Ensure key runtime class used by the Streamlit app is importable.
    from langchain_core.messages import HumanMessage  # noqa: F401

    print("✅ import langchain_core.messages.HumanMessage")
    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
