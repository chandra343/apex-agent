"""OAuth and Account Authentication Manager for Subscriptions (Copilot, Claude Code, Cursor)

and Local Engine Auto-Detection.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from apex.config import config


GITHUB_COPILOT_CLIENT_ID = "Iv1.b507a08c87ecfe98"  # Standard VS Code Client ID for Copilot


class OAuthManager:
    """Handles OAuth Device Code flow for GitHub Copilot, local session importing, and auto-discovery."""

    def __init__(self) -> None:
        pass

    # =========================================================================
    # 1. GITHUB COPILOT OAUTH DEVICE CODE FLOW
    # =========================================================================
    def login_github_copilot(self, console: Optional[Console] = None) -> Tuple[bool, str]:
        """Perform OAuth Device Code login for GitHub Copilot.
        
        Prompts user to visit https://github.com/login/device and enter the user code.
        Polls until confirmed, exchanges for Copilot session token, and saves configuration.
        """
        c = console or Console()
        device_code_url = "https://github.com/login/device/code"
        headers = {"Accept": "application/json"}
        payload = {
            "client_id": GITHUB_COPILOT_CLIENT_ID,
            "scope": "read:user"
        }

        try:
            resp = requests.post(device_code_url, data=payload, headers=headers, timeout=10)
            if resp.status_code != 200:
                return False, f"Gagal meminta kode device dari GitHub: {resp.status_code} {resp.text}"

            data = resp.json()
            device_code = data["device_code"]
            user_code = data["user_code"]
            verification_uri = data.get("verification_uri", "https://github.com/login/device")
            interval = max(5, int(data.get("interval", 5)))
            expires_in = int(data.get("expires_in", 900))

            # Display instruction panel to user
            c.print(Panel(
                f"[bold green]AUTENTIKASI AKUN GITHUB COPILOT (OAUTH)[/bold green]\n\n"
                f"1. Buka browser Anda: [bold cyan link={verification_uri}]{verification_uri}[/bold cyan link]\n"
                f"2. Masukkan kode verifikasi: [bold yellow]{user_code}[/bold yellow]\n"
                f"3. Berikan izin otorisasi untuk akun GitHub Anda.\n\n"
                f"[dim]Menunggu konfirmasi dari GitHub (berlaku {expires_in // 60} menit)... Tekan Ctrl+C untuk membatalkan.[/dim]",
                border_style="green",
                expand=True
            ))

            token_url = "https://github.com/login/oauth/access_token"
            token_payload = {
                "client_id": GITHUB_COPILOT_CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }

            gh_oauth_token = ""
            start_poll = time.time()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=c,
                transient=True
            ) as progress:
                task = progress.add_task("[cyan]Menunggu otorisasi browser...[/cyan]", total=None)

                while time.time() - start_poll < expires_in:
                    time.sleep(interval)
                    t_resp = requests.post(token_url, data=token_payload, headers=headers, timeout=10)
                    t_data = t_resp.json()

                    if "access_token" in t_data:
                        gh_oauth_token = t_data["access_token"]
                        break

                    err = t_data.get("error")
                    if err == "authorization_pending":
                        continue
                    elif err == "slow_down":
                        interval += 5
                        continue
                    elif err in ["expired_token", "access_denied"]:
                        return False, f"Otorisasi dibatalkan atau waktu habis ({err})."
                    else:
                        if err:
                            return False, f"Error dari GitHub: {err} ({t_data.get('error_description')})"

            if not gh_oauth_token:
                return False, "Waktu tunggu otorisasi habis."

            # Exchange GitHub OAuth token for Copilot Session Token
            ok, msg, copilot_token, exp = self._exchange_copilot_token(gh_oauth_token)
            if not ok:
                return False, f"Login GitHub berhasil, namun gagal mengaktifkan Copilot: {msg}"

            # Save to config
            providers = config.get("providers", {})
            providers["copilot"] = {
                "api_key": gh_oauth_token,
                "copilot_token": copilot_token,
                "token_expires_at": exp,
                "base_url": "https://api.githubcopilot.com",
                "models": ["claude-3.7-sonnet", "claude-3.5-sonnet", "gpt-4o", "o3-mini", "o1"]
            }
            config.set("providers", providers, auto_save=True)

            return True, f"Login Akun GitHub Copilot Berhasil! Kuota model Claude 3.7 & GPT-4o siap digunakan."
        except KeyboardInterrupt:
            return False, "Login dibatalkan oleh pengguna."
        except Exception as e:
            return False, f"Terjadi kesalahan saat login GitHub: {str(e)}"

    def _exchange_copilot_token(self, gh_oauth_token: str) -> Tuple[bool, str, str, float]:
        """Exchange GitHub OAuth token for temporary Copilot session token."""
        url = "https://api.github.com/copilot_internal/v2/token"
        headers = {
            "Authorization": f"token {gh_oauth_token}",
            "Editor-Version": "vscode/1.85.1",
            "Editor-Plugin-Version": "copilot/1.144.0",
            "User-Agent": "GithubCopilot/1.144.0",
            "Accept": "application/json"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return False, f"HTTP {resp.status_code}: {resp.text[:150]}", "", 0.0

            data = resp.json()
            token = data.get("token", "")
            expires_at = float(data.get("expires_at", time.time() + 1800))
            if not token:
                return False, "Token Copilot kosong dalam respon GitHub", "", 0.0

            return True, "OK", token, expires_at
        except Exception as e:
            return False, str(e), "", 0.0

    def get_valid_copilot_token(self) -> Optional[str]:
        """Return a valid Copilot session token, refreshing automatically if needed."""
        providers = config.get("providers", {})
        copilot_cfg = providers.get("copilot", {})
        gh_key = copilot_cfg.get("api_key", "")
        if not gh_key or "YOUR_" in gh_key:
            return None

        curr_token = copilot_cfg.get("copilot_token", "")
        expires_at = float(copilot_cfg.get("token_expires_at", 0))

        # If current token is valid for at least 2 more minutes, use it
        if curr_token and expires_at > (time.time() + 120):
            return curr_token

        # Otherwise refresh using the saved gh_oauth_token
        ok, msg, new_tok, new_exp = self._exchange_copilot_token(gh_key)
        if ok and new_tok:
            copilot_cfg["copilot_token"] = new_tok
            copilot_cfg["token_expires_at"] = new_exp
            providers["copilot"] = copilot_cfg
            config.set("providers", providers, auto_save=True)
            return new_tok

        return None

    # =========================================================================
    # 2. CLAUDE CODE SESSION IMPORT
    # =========================================================================
    def import_claude_code(self) -> Tuple[bool, str, Optional[str]]:
        """Look for Claude Code CLI credentials in ~/.claude.json or system environment."""
        paths_to_check = [
            Path.home() / ".claude.json",
            Path.home() / ".claude" / "auth.json",
            Path.home() / ".config" / "claude" / "config.json"
        ]

        found_key = ""
        source_desc = ""

        # Check environment first
        env_tok = os.environ.get("CLAUDE_CODE_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
        if env_tok and not env_tok.startswith("YOUR_"):
            found_key = env_tok
            source_desc = "Environment Variable"

        if not found_key:
            for p in paths_to_check:
                if p.exists():
                    try:
                        content = json.loads(p.read_text(encoding="utf-8"))
                        tok = (
                            content.get("oauthToken") or
                            content.get("apiKey") or
                            content.get("token") or
                            content.get("session_token")
                        )
                        if tok and isinstance(tok, str) and not tok.startswith("YOUR_"):
                            found_key = tok
                            source_desc = str(p)
                            break
                    except Exception:
                        pass

        if found_key:
            providers = config.get("providers", {})
            providers["claude-code"] = {
                "api_key": found_key,
                "base_url": "https://api.anthropic.com/v1",
                "models": ["claude-3-7-sonnet-latest", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]
            }
            config.set("providers", providers, auto_save=True)
            return True, f"Berhasil mengimpor session Claude Code dari {source_desc}!", found_key

        return False, "Tidak ditemukan konfigurasi Claude Code aktif di ~/.claude.json atau Environment.", None

    # =========================================================================
    # 3. CURSOR SESSION IMPORT
    # =========================================================================
    def import_cursor(self) -> Tuple[bool, str, Optional[str]]:
        """Look for Cursor IDE session token in globalStorage or system."""
        paths_to_check = [
            Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "storage.json",
            Path.home() / ".cursor" / "auth.json"
        ]

        env_tok = os.environ.get("CURSOR_TOKEN") or os.environ.get("WORKOS_CURSOR_SESSION_TOKEN")
        found_key = env_tok or ""
        source_desc = "Environment Variable" if env_tok else ""

        if not found_key:
            for p in paths_to_check:
                if p.exists():
                    try:
                        content = json.loads(p.read_text(encoding="utf-8"))
                        tok = content.get("workos.sessionToken") or content.get("cursor.auth.token")
                        if tok and isinstance(tok, str):
                            found_key = tok
                            source_desc = str(p)
                            break
                    except Exception:
                        pass

        if found_key:
            providers = config.get("providers", {})
            providers["cursor"] = {
                "api_key": found_key,
                "base_url": "https://api.cursor.com/v1",
                "models": ["cursor-fast", "claude-3.5-sonnet", "gpt-4o"]
            }
            config.set("providers", providers, auto_save=True)
            return True, f"Berhasil mengimpor auth Cursor dari {source_desc}!", found_key

        return False, "Tidak ditemukan kredensial Cursor aktif di sistem.", None

    # =========================================================================
    # 4. AUTO-SCAN LOCAL AI ENGINES
    # =========================================================================
    def scan_local_services(self) -> Dict[str, Dict[str, Any]]:
        """Probe localhost ports for Ollama (11434), LM Studio (1234), vLLM (8000), llama.cpp (8080).
        
        Returns a dict of detected services with their fetched models.
        """
        detected: Dict[str, Dict[str, Any]] = {}

        # 1. Ollama (Port 11434)
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=1.5)
            if r.status_code == 200:
                tags_data = r.json().get("models", [])
                models = [m["name"] for m in tags_data] if tags_data else ["qwen2.5-coder:7b", "llama3.2:3b"]
                detected["ollama"] = {
                    "name": "Ollama (Lokal)",
                    "base_url": "http://localhost:11434/v1",
                    "api_key": "none",
                    "models": models
                }
        except Exception:
            pass

        # 2. LM Studio (Port 1234)
        try:
            r = requests.get("http://localhost:1234/v1/models", timeout=1.5)
            if r.status_code == 200:
                m_data = r.json().get("data", [])
                models = [m["id"] for m in m_data] if m_data else ["local-model"]
                detected["lmstudio"] = {
                    "name": "LM Studio (Lokal)",
                    "base_url": "http://localhost:1234/v1",
                    "api_key": "none",
                    "models": models
                }
        except Exception:
            pass

        # 3. vLLM (Port 8000)
        try:
            r = requests.get("http://localhost:8000/v1/models", timeout=1.5)
            if r.status_code == 200:
                m_data = r.json().get("data", [])
                models = [m["id"] for m in m_data] if m_data else ["vllm-model"]
                detected["vllm"] = {
                    "name": "vLLM Server",
                    "base_url": "http://localhost:8000/v1",
                    "api_key": "none",
                    "models": models
                }
        except Exception:
            pass

        # 4. llama.cpp / llama-server (Port 8080)
        try:
            r = requests.get("http://localhost:8080/v1/models", timeout=1.5)
            if r.status_code == 200:
                m_data = r.json().get("data", [])
                models = [m["id"] for m in m_data] if m_data else ["gguf-model"]
                detected["llamacpp"] = {
                    "name": "llama.cpp (Lokal)",
                    "base_url": "http://localhost:8080/v1",
                    "api_key": "none",
                    "models": models
                }
        except Exception:
            pass

        # If any detected, auto-update config
        if detected:
            providers = config.get("providers", {})
            for svc_id, svc_data in detected.items():
                providers[svc_id] = {
                    "api_key": svc_data["api_key"],
                    "base_url": svc_data["base_url"],
                    "models": svc_data["models"]
                }
            config.set("providers", providers, auto_save=True)

        return detected


# Global instance
oauth_manager = OAuthManager()
