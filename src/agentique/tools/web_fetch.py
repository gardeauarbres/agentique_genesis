from __future__ import annotations

from bs4 import BeautifulSoup
import requests


def fetch_url_text(url: str, timeout_s: int = 10, max_chars: int = 4000) -> str:
    """Fetch an URL and return readable text content.

    Returns an empty string when the URL is invalid or unreachable.
    """
    if not url.strip() or max_chars <= 0:
        return ""

    try:
        response = requests.get(url, timeout=timeout_s)
        response.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())
    return text[:max_chars]
