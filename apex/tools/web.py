"""Web Search & Content Extraction Tools."""
from __future__ import annotations

import re
import urllib.parse
from typing import Tuple
import requests


def web_search(query: str, max_results: int = 5) -> Tuple[bool, str]:
    """Search the web using DuckDuckGo HTML API."""
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return False, f"Search engine returned status code {resp.status_code}"

        html = resp.text
        # Extract result titles, snippets, and links using regex
        results: list[str] = []
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
        titles = re.findall(r'<a class="result__url[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)

        for idx, snip in enumerate(snippets[:max_results], 1):
            clean_snip = re.sub(r"<[^>]+>", "", snip).strip()
            link_info = titles[idx - 1] if idx - 1 < len(titles) else ("", "")
            clean_title = re.sub(r"<[^>]+>", "", link_info[1]).strip()
            link = link_info[0].strip()

            results.append(f"{idx}. {clean_title}\n   Link: {link}\n   Snippet: {clean_snip}")

        if not results:
            return True, f"No direct web results found for query: '{query}'"

        return True, f"=== Web Search Results: '{query}' ===\n\n" + "\n\n".join(results)
    except Exception as e:
        return False, f"Web search error: {e}"


def fetch_web_page(url: str) -> Tuple[bool, str]:
    """Fetch and strip raw HTML of a web page to extract readable text."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return False, f"Failed to fetch page (HTTP {resp.status_code})"

        html = resp.text
        # Remove script and style elements
        clean = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Remove all HTML tags
        text = re.sub(r"<[^>]+>", " ", clean)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return True, text[:8000]
    except Exception as e:
        return False, f"Failed to fetch web page: {e}"
