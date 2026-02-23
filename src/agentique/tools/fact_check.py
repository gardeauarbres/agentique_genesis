from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .web_search import search_web


@dataclass
class FactCheckResult:
    claim: str
    verdict: str
    sources: list[dict[str, str]]
    rationale: str


def _domain_of(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().strip()


def fact_check(claim: str, max_sources: int = 3) -> FactCheckResult:
    """Lightweight fact-check helper based on source diversity.

    This does not prove truth; it gathers sources and provides a conservative verdict.
    """
    results = search_web(claim, max_results=max_sources)

    if not results:
        return FactCheckResult(
            claim=claim,
            verdict="UNKNOWN",
            sources=[],
            rationale="No web sources were found for this claim.",
        )

    unique_domains = {_domain_of(item.get("url", "")) for item in results}
    unique_domains.discard("")

    verdict = "SUPPORTED" if len(unique_domains) >= 2 else "WEAK"
    rationale = (
        "At least two different domains mention the claim."
        if verdict == "SUPPORTED"
        else "Only one source domain found; confidence is low."
    )
    sources = [{"title": item.get("title", ""), "url": item.get("url", "")} for item in results]

    return FactCheckResult(claim=claim, verdict=verdict, sources=sources, rationale=rationale)
