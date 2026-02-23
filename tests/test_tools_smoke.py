from __future__ import annotations

from typing import Any

import requests

from agentique.tools.fact_check import FactCheckResult, fact_check
from agentique.tools.web_fetch import fetch_url_text
from agentique.tools.web_search import search_web


def test_fact_check_result_dataclass_shape() -> None:
    result = FactCheckResult(claim="x", verdict="UNKNOWN", sources=[], rationale="n/a")
    assert result.claim == "x"
    assert result.verdict == "UNKNOWN"


def test_search_web_empty_query_returns_empty_list() -> None:
    assert search_web("   ") == []


def test_search_web_handles_exceptions(monkeypatch: Any) -> None:
    class _BoomDDGS:
        def __enter__(self) -> "_BoomDDGS":
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        def text(self, query: str, max_results: int) -> list[dict[str, str]]:
            raise RuntimeError("network down")

    monkeypatch.setattr("agentique.tools.web_search.DDGS", _BoomDDGS)
    assert search_web("OpenAI", max_results=3) == []


def test_fetch_url_text_handles_request_errors(monkeypatch: Any) -> None:
    def _boom_get(*args: Any, **kwargs: Any) -> None:
        raise requests.RequestException("timeout")

    monkeypatch.setattr("agentique.tools.web_fetch.requests.get", _boom_get)
    assert fetch_url_text("https://example.com") == ""


def test_fact_check_supported_with_two_domains(monkeypatch: Any) -> None:
    def _fake_search(query: str, max_results: int = 3, retries: int = 2) -> list[dict[str, str]]:
        return [
            {"title": "A", "url": "https://example.com/a", "snippet": "..."},
            {"title": "B", "url": "https://docs.python.org/3/", "snippet": "..."},
        ]

    monkeypatch.setitem(fact_check.__globals__, "search_web", _fake_search)
    result = fact_check("claim")
    assert result.verdict == "SUPPORTED"
