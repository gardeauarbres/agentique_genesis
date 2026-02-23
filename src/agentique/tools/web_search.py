from __future__ import annotations

from typing import Any

from ddgs import DDGS


def _normalize_result(item: dict[str, Any]) -> dict[str, str]:
    return {
        "title": str(item.get("title", "")),
        "url": str(item.get("href", "")),
        "snippet": str(item.get("body", "")),
    }


def search_web(query: str, max_results: int = 5, retries: int = 2) -> list[dict[str, str]]:
    """Run a DuckDuckGo text search and return normalized result entries.

    The function is defensive by design:
    - empty query => []
    - invalid max_results => []
    - transient/search backend failure => retries then []
    """
    cleaned_query = query.strip()
    if not cleaned_query or max_results <= 0:
        return []

    attempts = max(1, retries + 1)
    for _ in range(attempts):
        try:
            with DDGS() as ddgs:
                raw_results = ddgs.text(cleaned_query, max_results=max_results)
                return [_normalize_result(item) for item in raw_results]
        except Exception:
            continue

    return []
