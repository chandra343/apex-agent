"""Smart DOM Extractor & Markdown Converter."""
from __future__ import annotations

import re
from typing import Dict, Tuple


def html_to_markdown(html_text: str) -> str:
    """Convert raw HTML into clean readable markdown without graphic noise."""
    if not html_text:
        return ""

    # 1. Remove script, style, noscript, svg, head
    text = re.sub(r"<(script|style|noscript|svg|head)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Convert headings
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n# \1\n", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n## \1\n", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n### \1\n", text, flags=re.DOTALL | re.IGNORECASE)

    # 3. Convert paragraphs & breaks
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # 4. Convert lists
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"\n• \1", text, flags=re.DOTALL | re.IGNORECASE)

    # 5. Convert links
    text = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.DOTALL | re.IGNORECASE)

    # 6. Remove remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # 7. Collapse spaces and newlines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    clean_lines: list[str] = []
    blank_run = 0
    for line in lines:
        if not line:
            blank_run += 1
            if blank_run <= 2:
                clean_lines.append("")
        else:
            blank_run = 0
            clean_lines.append(line)

    return "\n".join(clean_lines).strip()
