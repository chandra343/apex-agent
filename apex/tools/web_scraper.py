"""Structured Web Scraper & Article Extractor Tool for Apex."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
import requests
from lxml import html


def scrape_structured_web(
    url: str,
    extract_links: bool = True,
    max_length: int = 5000
) -> str:
    """Fetch and extract clean, structured Markdown content from any web page.

    Strips ads, scripts, navigation boilerplate, and extracts:
    - Page title and metadata
    - Main body text formatted cleanly in Markdown
    - Outbound hyperlinks and tables

    Args:
        url: Full web URL (must start with http:// or https://).
        extract_links: Whether to list outbound hyperlinks found in the content.
        max_length: Maximum character length for extracted content.

    Returns:
        Structured Markdown summary of the web page.
    """
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(clean_url, headers=headers, timeout=15)
        resp.encoding = resp.apparent_encoding or "utf-8"
        if resp.status_code != 200:
            return f"❌ Gagal mengambil halaman `{clean_url}` (HTTP {resp.status_code})"

        raw_html = resp.text
        tree = html.fromstring(raw_html)

        # 1. Page Title
        title_nodes = tree.xpath("//title/text()")
        title = title_nodes[0].strip() if title_nodes else clean_url

        # 2. Meta description
        meta_desc = ""
        desc_nodes = tree.xpath("//meta[@name='description']/@content") or tree.xpath("//meta[@property='og:description']/@content")
        if desc_nodes:
            meta_desc = desc_nodes[0].strip()

        # 3. Clean unwanted tags
        for bad_elem in tree.xpath("//script | //style | //nav | //footer | //header | //aside | //noscript"):
            parent = bad_elem.getparent()
            if parent is not None:
                parent.remove(bad_elem)

        # 4. Extract headings and body paragraphs
        body_elements = tree.xpath("//h1 | //h2 | //h3 | //h4 | //p | //li | //table")
        body_lines: list[str] = []

        for elem in body_elements:
            tag = elem.tag.lower()
            text = elem.text_content().strip()
            if not text or len(text) < 3:
                continue

            # Collapse multi-spaces
            text = re.sub(r"\s+", " ", text)

            if tag == "h1":
                body_lines.append(f"\n# {text}")
            elif tag == "h2":
                body_lines.append(f"\n## {text}")
            elif tag == "h3":
                body_lines.append(f"\n### {text}")
            elif tag == "li":
                body_lines.append(f"• {text}")
            else:
                body_lines.append(text)

        full_body = "\n\n".join(body_lines)
        if len(full_body) > max_length:
            full_body = full_body[:max_length] + f"\n\n... *(isi dipotong karena melebihi batas {max_length} karakter)*"

        # 5. Extract links
        links_section = ""
        if extract_links:
            raw_links = tree.xpath("//a[@href]/@href")
            unique_links = []
            for l in raw_links:
                if l.startswith("http") and l not in unique_links and l != clean_url:
                    unique_links.append(l)
            if unique_links:
                links_md = "\n".join(f"• <{l}>" for l in unique_links[:10])
                links_section = f"\n\n### 🔗 Tautan Terkait (10 Teratas):\n{links_md}"

        desc_line = f"\n> 📝 *Deskripsi:* {meta_desc}\n" if meta_desc else ""

        return (
            f"🌐 **Ringkasan Konten Web: [{title}]({clean_url})**\n"
            f"{desc_line}\n"
            f"{full_body}"
            f"{links_section}"
        )

    except Exception as e:
        return f"❌ Kesalahan saat scraping `{clean_url}`: {str(e)}"
