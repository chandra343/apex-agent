"""Lightpanda Headless Browser Lifecycle Manager & CDP Controller."""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple
import requests

from apex.browser.cdp_client import CDPClient
from apex.browser.scraper import html_to_markdown
from apex.config import DATA_DIR


class LightpandaBrowser:
    """Manages the ~20MB RAM Lightpanda browser daemon and CDP interaction."""

    def __init__(self, port: int = 9222) -> None:
        self.port = port
        self.ws_url = f"ws://127.0.0.1:{port}"
        self.proc: Optional[subprocess.Popen] = None
        self.cdp_client: Optional[CDPClient] = None

    def start_daemon(self) -> bool:
        """Start Lightpanda binary if installed on system or in bin/."""
        bin_path = shutil.which("lightpanda")
        local_bin = DATA_DIR / "bin" / "lightpanda"
        if not bin_path and local_bin.exists():
            bin_path = str(local_bin)

        if not bin_path:
            return False

        try:
            cmd = [bin_path, "serve", f"--port={self.port}"]
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(0.5)
            self.cdp_client = CDPClient(self.ws_url)
            return self.cdp_client.connect()
        except Exception:
            return False

    def browse(self, url: str) -> Tuple[bool, str]:
        """Navigate to URL and extract page markdown.

        Uses Lightpanda CDP if running; otherwise gracefully falls back
        to direct HTTP fetching with smart DOM parsing.
        """
        # 1. Try CDP if client is connected
        if self.cdp_client and self.cdp_client.connect():
            ok, nav_msg = self.cdp_client.navigate(url)
            if ok:
                time.sleep(1.0)  # Wait for JS hydration
                js_ok, page_html = self.cdp_client.evaluate_js("document.documentElement.outerHTML")
                if js_ok and page_html:
                    markdown = html_to_markdown(str(page_html))
                    return True, f"=== Page: {url} (via Lightpanda CDP) ===\n\n" + markdown[:10000]

        # 2. Fast lightweight fallback via requests
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                markdown = html_to_markdown(resp.text)
                return True, f"=== Page: {url} ===\n\n" + markdown[:10000]
            else:
                return False, f"Failed to load page: HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Browser request error: {e}"

    def stop(self) -> None:
        if self.cdp_client:
            self.cdp_client.close()
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None


# Global browser instance
lightpanda_browser = LightpandaBrowser()
