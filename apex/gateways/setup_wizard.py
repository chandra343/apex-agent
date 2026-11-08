"""6-Stage Interactive Setup Wizard with Back/Next navigation & Live Diagnostics."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from apex.config import config, CONFIG_FILE, PKG_ROOT
from apex.gateways.file_picker import pick_file
from apex.router.catalog import FULL_PROVIDER_CATALOG, PROVIDER_CATEGORIES, get_providers_by_category
from apex.router.oauth_manager import oauth_manager
from apex.router.provider_manager import provider_manager


class SetupWizard:
    """Manages the 6-stage interactive onboarding wizard."""

    def __init__(self) -> None:
        self.console = Console()
        self.current_stage = 1
        self.total_stages = 6

    def run(self) -> None:
        self.console.clear()
        self.console.print(Panel.fit(
            "[bold cyan]PROJECT APEX — INTERACTIVE SETUP WIZARD[/bold cyan]\n"
            "[dim]A step-by-step setup guide for configuring your sovereign hybrid AI agent.[/dim]\n"
            "[yellow]Type 'b' at any prompt to go back to the previous stage.[/yellow]",
            border_style="cyan"
        ))

        while 1 <= self.current_stage <= self.total_stages:
            if self.current_stage == 1:
                self.stage_1_environment()
            elif self.current_stage == 2:
                self.stage_2_providers()
            elif self.current_stage == 3:
                self.stage_3_soul_and_agents()
            elif self.current_stage == 4:
                self.stage_4_prompt_injection()
            elif self.current_stage == 5:
                self.stage_5_gateways_and_auth()
            elif self.current_stage == 6:
                self.stage_6_diagnostics()

        config.save()
        self.console.print("\n[bold green]✔ Configuration saved successfully to:[/bold green] " + str(CONFIG_FILE))
        self.console.print("[bold cyan]Setup complete! You can now run 'apex' to start your agent.[/bold cyan]\n")

    def _header(self, title: str) -> None:
        self.console.print()
        self.console.rule(f"[bold yellow]Stage {self.current_stage}/{self.total_stages}: {title}[/bold yellow]")

    # =========================================================================
    # STAGE 1: Environment & Workspace
    # =========================================================================
    def stage_1_environment(self) -> None:
        self._header("Environment & Workspace Configuration")
        curr_ws = str(config.workspace)
        self.console.print(f"Current Workspace Directory: [bold green]{curr_ws}[/bold green]")
        
        val = Prompt.ask("Enter workspace path or press Enter to keep", default=curr_ws)
        if val.strip().lower() == "b":
            return  # Stage 1 has nowhere back
        
        resolved = str(Path(val).expanduser().resolve())
        config.set("paths.workspace", resolved, auto_save=False)
        self.current_stage += 1

    # =========================================================================
    # STAGE 2: AI Providers & Model API Keys (Interactive Shelf - 9Router Pro Style)
    # =========================================================================
    def stage_2_providers(self) -> None:
        self.run_provider_shelf()

    def run_provider_shelf(self, standalone: bool = False) -> None:
        """Interactive Provider Shelf UI/UX ala 9Router Pro & Zeline dengan 35+ Provider dan Login Akun."""
        test_results: Dict[str, Tuple[bool, str, float]] = {}
        current_category = "all"

        while True:
            if not standalone:
                self._header("AI Provider Shelf (Gaya 9Router Pro & Zeline)")
            else:
                self.console.clear()
                self.console.print(Panel.fit(
                    "[bold cyan]AI PROVIDER SHELF & ACCOUNT MANAGER (9Router Pro Style)[/bold cyan]\n"
                    "[dim]Kelola seluruh endpoint, API key, dan login akun (GitHub Copilot, Claude Code, Cursor, Local AI).[/dim]",
                    border_style="cyan"
                ))

            configured_providers = config.get("providers", {})

            # Filter catalog items by current category
            category_catalog = get_providers_by_category(current_category)

            all_shelf_items: list[dict[str, Any]] = []
            known_ids = set()

            for item in category_catalog:
                all_shelf_items.append(dict(item))
                known_ids.add(item["id"])

            # If 'all' or custom items, merge custom user-added providers
            if current_category in ["all", "local"]:
                for c_id, c_data in configured_providers.items():
                    if c_id not in known_ids:
                        all_shelf_items.append({
                            "id": c_id,
                            "name": c_id.upper(),
                            "category": "custom",
                            "icon": "🔌",
                            "auth_type": "custom",
                            "url": c_data.get("base_url", "-"),
                            "models": c_data.get("models", [f"{c_id}-model"]),
                            "description": "Custom registered provider"
                        })

            # Render Category Tabs
            cat_display = f"Kategori Aktif: [bold green]{PROVIDER_CATEGORIES.get(current_category, current_category)}[/bold green]\n"
            cat_display += "[dim]Pilihan Tab [f]: [all] Semua (35+) | [oauth] 🔑 Akun | [frontier] 🏛️ Frontier | [fast] ⚡ Fast | [apac] 🌏 APAC | [agg] 🌐 Aggregator | [local] 🦙 Lokal[/dim]"
            self.console.print(Panel(cat_display, border_style="dim", padding=(0, 1)))

            # Render Table
            table = Table(
                title=f"[bold yellow]Daftar Provider AI — {len(all_shelf_items)} Pilihan[/bold yellow]",
                show_lines=True,
                header_style="bold cyan",
                expand=True
            )
            table.add_column("No", justify="center", style="bold yellow", no_wrap=True, width=3)
            table.add_column("Provider", style="bold", min_width=16)
            table.add_column("Tipe Auth", style="magenta", no_wrap=True, width=13)
            table.add_column("Model Utama", style="cyan", min_width=18)
            table.add_column("Status API Key / Akun", style="bold", min_width=18)

            for idx, item in enumerate(all_shelf_items, 1):
                p_id = item["id"]
                cfg_data = configured_providers.get(p_id, {})
                api_key = cfg_data.get("api_key", "").strip()
                base_url = cfg_data.get("base_url") or item["url"]
                models_list = cfg_data.get("models") or item["models"]
                models_preview = ", ".join(models_list[:2])
                if len(models_list) > 2:
                    models_preview += f" (+{len(models_list) - 2})"

                # Auth Type Label
                auth_type = item.get("auth_type", "api_key")
                if auth_type in ["oauth_device", "oauth_session"]:
                    auth_badge = "🔑 OAuth"
                elif auth_type == "session_import":
                    auth_badge = "📥 Session"
                elif auth_type == "none":
                    auth_badge = "🦙 Lokal"
                else:
                    auth_badge = "🔑 API Key"

                # Check status
                if p_id in test_results:
                    ok, msg, lat = test_results[p_id]
                    if ok:
                        status_str = f"[bold green]🟢 OK ({lat}s)[/bold green]"
                    else:
                        status_str = f"[bold red]✖ {msg[:16]}[/bold red]"
                elif p_id in ["copilot", "antigravity"] and api_key and not api_key.startswith("YOUR_"):
                    status_str = "[bold green]🟢 Akun Aktif[/bold green]"
                elif api_key and not api_key.startswith("YOUR_"):
                    if auth_type == "none" or api_key == "none":
                        status_str = "[bold green]🟢 Aktif (Lokal)[/bold green]"
                    else:
                        masked = api_key[:4] + "..." + api_key[-3:] if len(api_key) > 7 else "••••••"
                        status_str = f"[bold green]🟢 OK ({masked})[/bold green]"
                else:
                    status_str = "[dim]⚪ Belum Diatur[/dim]"

                table.add_row(
                    str(idx),
                    f"{item['icon']} {item['name']}",
                    auth_badge,
                    models_preview,
                    status_str
                )

            self.console.print(table)
            self.console.print(
                "\n[bold cyan]Menu Aksi Cepat (9Router Pro & Zeline):[/bold cyan]\n"
                f" • Masukkan angka [bold yellow]1 - {len(all_shelf_items)}[/bold yellow] : Pilih provider untuk mengatur API Key / URL / Login\n"
                " • Masukkan [bold yellow]a[/bold yellow]       : 🌌 [bold green]Login / Import Google Antigravity OAuth[/bold green] (Gemini 2.0/3 & Claude 3.5)\n"
                " • Masukkan [bold yellow]g[/bold yellow]       : 🐙 [bold green]Login Akun GitHub Copilot[/bold green] (OAuth Device Code — Claude 3.7 & GPT-4o)\n"
                " • Masukkan [bold yellow]c[/bold yellow]       : 🟣 [bold green]Import / Login Claude Code[/bold green] (~/.claude.json atau session)\n"
                " • Masukkan [bold yellow]x[/bold yellow]       : 🟢 [bold green]Import / Login OpenAI Codex & ChatGPT Plus[/bold green] (Session Token)\n"
                " • Masukkan [bold yellow]u[/bold yellow]       : ⚡ [bold green]Import / Login Akun Cursor[/bold green] (WorkOS Session Token)\n"
                " • Masukkan [bold yellow]k[/bold yellow]       : 🎁 [bold green]Login / Import Kiro AI Free Tier[/bold green] (Free Claude & GLM Tokens)\n"
                " • Masukkan [bold yellow]s[/bold yellow]       : 🔍 [bold green]Auto-Scan Local AI[/bold green] (Ollama:11434, LM Studio:1234, vLLM:8000)\n"
                " • Masukkan [bold yellow]f[/bold yellow]       : 📑 [bold cyan]Ganti Kategori / Filter Tab[/bold cyan] (All, OAuth, Frontier, Fast, APAC, Cloud, Local)\n"
                " • Masukkan [bold yellow]+[/bold yellow]       : ➕ Tambah Custom Provider Baru\n"
                " • Masukkan [bold yellow]t[/bold yellow]       : 🧪 Test All (Uji koneksi & latensi semua provider serentak)\n"
                f" • Masukkan [bold yellow]n[/bold yellow]       : {'Selesai / Tutup' if standalone else 'Lanjut ke Tahap Berikutnya [ Next > ]'}\n"
                f" • Masukkan [bold yellow]b[/bold yellow]       : {'Kembali' if standalone else 'Kembali ke Tahap Sebelumnya [ < Back ]'}"
            )

            choice = Prompt.ask("\nPilih aksi").strip().lower()

            if choice == "b":
                if not standalone:
                    self.current_stage = max(1, self.current_stage - 1)
                break

            if choice == "n":
                if not standalone:
                    has_any = any(
                        p.get("api_key") and not p.get("api_key").startswith("YOUR_")
                        for p in configured_providers.values()
                    )
                    if not has_any:
                        proceed = Confirm.ask("[yellow]Peringatan: Belum ada provider yang terkonfigurasi. Tetap lanjut?[/yellow]", default=False)
                        if not proceed:
                            continue
                    self.current_stage += 1
                break

            if choice == "a":
                self.console.print("\n[cyan]Memeriksa kredensial Google Antigravity OAuth di sistem...[/cyan]")
                ok, msg = oauth_manager.import_antigravity(self.console)
                if ok:
                    self.console.print(f"[bold green]✔ {msg}[/bold green]")
                    t_ok, t_msg, t_lat = provider_manager.test_provider("antigravity")
                    test_results["antigravity"] = (t_ok, t_msg, t_lat)
                    if t_ok:
                        self.console.print(f"[bold green]✔ Terverifikasi! Latensi Antigravity: {t_lat}s ({t_msg})[/bold green]")
                    else:
                        self.console.print(f"[yellow]Status koneksi: {t_msg}[/yellow]")
                else:
                    self.console.print(f"[bold red]✖ {msg}[/bold red]")
                    manual_tok = Prompt.ask("Masukkan Access Token Google Cloud / Antigravity OAuth secara manual (Enter untuk batal)", default="").strip()
                    if manual_tok:
                        provider_manager.add_provider("antigravity", manual_tok, "https://cloudcode-pa.googleapis.com/v1internal", ["gemini-2.0-flash", "gemini-2.0-pro-exp", "gemini-1.5-pro", "gemini-3-flash", "claude-3-5-sonnet"])
                        self.console.print("[bold green]✔ Google Antigravity session berhasil disimpan![/bold green]")
                Prompt.ask("\nTekan Enter untuk melanjutkan...")
                continue

            if choice == "x":
                self.console.print("\n[cyan]Memeriksa kredensial OpenAI Codex / ChatGPT di sistem...[/cyan]")
                manual_tok = Prompt.ask("Masukkan Session Token OpenAI Codex / ChatGPT Plus (Enter untuk cek otomatis)", default="").strip()
                ok, msg = oauth_manager.import_codex(manual_tok)
                if ok:
                    self.console.print(f"[bold green]✔ {msg}[/bold green]")
                else:
                    self.console.print(f"[yellow]{msg}[/yellow]")
                Prompt.ask("\nTekan Enter untuk melanjutkan...")
                continue

            if choice == "k":
                self.console.print("\n[cyan]Mengonfigurasi Kiro AI Platform (Free Tier)...[/cyan]")
                ok, msg = oauth_manager.import_kiro()
                self.console.print(f"[bold green]✔ {msg}[/bold green]")
                Prompt.ask("\nTekan Enter untuk melanjutkan...")
                continue

            if choice == "g":
                self.console.print("\n[cyan]Memulai proses login GitHub Copilot OAuth...[/cyan]")
                ok, msg = oauth_manager.login_github_copilot(self.console)
                if ok:
                    self.console.print(f"[bold green]✔ {msg}[/bold green]")
                    # Test connection immediately
                    self.console.print("[dim]Menguji token Copilot...[/dim]")
                    t_ok, t_msg, t_lat = provider_manager.test_provider("copilot")
                    test_results["copilot"] = (t_ok, t_msg, t_lat)
                    if t_ok:
                        self.console.print(f"[bold green]✔ Terverifikasi! Latensi Copilot: {t_lat}s ({t_msg})[/bold green]")
                    else:
                        self.console.print(f"[bold red]✖ Uji koneksi gagal: {t_msg}[/bold red]")
                else:
                    self.console.print(f"[bold red]✖ {msg}[/bold red]")
                Prompt.ask("\nTekan Enter untuk melanjutkan...")
                continue

            if choice == "c":
                self.console.print("\n[cyan]Memeriksa kredensial Claude Code di sistem...[/cyan]")
                ok, msg, tok = oauth_manager.import_claude_code()
                if ok:
                    self.console.print(f"[bold green]✔ {msg}[/bold green]")
                else:
                    self.console.print(f"[yellow]{msg}[/yellow]")
                    manual_tok = Prompt.ask("Masukkan Session Token / API Key Claude Code secara manual (Enter untuk batal)", default="").strip()
                    if manual_tok:
                        provider_manager.add_provider("claude-code", manual_tok, "https://api.anthropic.com/v1", ["claude-3-7-sonnet-latest", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"])
                        self.console.print("[bold green]✔ Claude Code session berhasil disimpan![/bold green]")
                Prompt.ask("\nTekan Enter untuk melanjutkan...")
                continue

            if choice == "u":
                self.console.print("\n[cyan]Memeriksa kredensial Cursor di sistem...[/cyan]")
                ok, msg, tok = oauth_manager.import_cursor()
                if ok:
                    self.console.print(f"[bold green]✔ {msg}[/bold green]")
                else:
                    self.console.print(f"[yellow]{msg}[/yellow]")
                    manual_tok = Prompt.ask("Masukkan WorkOS Cursor Session Token (Enter untuk batal)", default="").strip()
                    if manual_tok:
                        provider_manager.add_provider("cursor", manual_tok, "https://api.cursor.com/v1", ["cursor-fast", "claude-3.5-sonnet", "gpt-4o"])
                        self.console.print("[bold green]✔ Cursor session berhasil disimpan![/bold green]")
                Prompt.ask("\nTekan Enter untuk melanjutkan...")
                continue

            if choice == "s":
                self.console.print("\n[cyan]Memindai engine AI lokal (Ollama:11434, LM Studio:1234, vLLM:8000, llama.cpp:8080)...[/cyan]")
                detected = oauth_manager.scan_local_services()
                if detected:
                    self.console.print(Panel(
                        "\n".join([f"🟢 [bold]{v['name']}[/bold] aktif di [dim]{v['base_url']}[/dim] (Model: {', '.join(v['models'][:3])})" for v in detected.values()]),
                        title="[bold green]Engine AI Lokal Ditemukan & Diaktifkan![/bold green]",
                        border_style="green"
                    ))
                else:
                    self.console.print("[yellow]Tidak ada server lokal yang sedang berjalan di port default.[/yellow]")
                Prompt.ask("\nTekan Enter untuk melanjutkan...")
                continue

            if choice == "f":
                self.console.print("\n[bold cyan]Pilihan Kategori:[/bold cyan]")
                cat_keys = list(PROVIDER_CATEGORIES.keys())
                for i, k in enumerate(cat_keys, 1):
                    self.console.print(f" {i}. [bold yellow]{k}[/bold yellow] - {PROVIDER_CATEGORIES[k]}")
                c_pick = Prompt.ask("\nPilih kategori (nama atau nomor)", default="all").strip().lower()
                if c_pick.isdigit() and 1 <= int(c_pick) <= len(cat_keys):
                    current_category = cat_keys[int(c_pick) - 1]
                elif c_pick in PROVIDER_CATEGORIES:
                    current_category = c_pick
                continue

            if choice == "t":
                self.console.print("\n[cyan]Menguji seluruh koneksi provider yang terkonfigurasi...[/cyan]")
                test_results = provider_manager.test_all()
                continue

            if choice == "+":
                self.console.print(Panel(
                    "[bold cyan]Tambah Custom Provider Baru (Gaya 9Router Pro)[/bold cyan]\n"
                    "[dim]Dukung provider lokal (vLLM, Ollama, LM Studio) atau proxy OpenAI-compatible kustom.[/dim]",
                    border_style="cyan"
                ))
                new_id = Prompt.ask("Nama ID Provider (contoh: vllm, lmstudio, my-proxy)").strip().lower()
                if new_id:
                    new_url = Prompt.ask("Base URL", default="http://localhost:8000/v1").strip()
                    new_key = Prompt.ask("API Key (jika ada, atau 'none')", default="none").strip()
                    new_models_str = Prompt.ask("Daftar Model (pisahkan koma)", default=f"{new_id}-model").strip()
                    new_models = [m.strip() for m in new_models_str.split(",") if m.strip()]

                    provider_manager.add_provider(new_id, new_key, new_url, new_models)
                    self.console.print(f"[bold green]✔ Custom Provider '{new_id}' berhasil ditambahkan ke shelf![/bold green]")
                    time.sleep(1.0)
                continue

            # Check if selection is a number
            if choice.isdigit():
                sel_num = int(choice)
                if 1 <= sel_num <= len(all_shelf_items):
                    target_item = all_shelf_items[sel_num - 1]
                    self._configure_single_provider(target_item, configured_providers, test_results)
                else:
                    self.console.print(f"[red]Nomor {choice} tidak ada dalam daftar.[/red]")
                    time.sleep(1.0)

    def _configure_single_provider(
        self,
        item: Dict[str, Any],
        configured_providers: Dict[str, Any],
        test_results: Dict[str, Tuple[bool, str, float]]
    ) -> None:
        p_id = item["id"]
        p_name = item["name"]
        icon = item["icon"]
        existing = configured_providers.get(p_id, {})
        curr_key = existing.get("api_key", "")
        curr_url = existing.get("base_url") or item["url"]
        curr_models = existing.get("models") or item["models"]

        # Special shortcut for Google Antigravity
        if p_id == "antigravity":
            self.console.print(Panel(
                f"[bold cyan]{icon} {p_name.upper()} (OAUTH & CLOUD CODE ASSIST)[/bold cyan]\n"
                f"Model Tersedia: [yellow]{', '.join(curr_models)}[/yellow]\n"
                f"[dim]Apex dapat mendeteksi session aktif Google Antigravity langsung dari sistem komputer Anda.[/dim]",
                border_style="cyan"
            ))
            do_import = Confirm.ask("Impor session Antigravity dari ~/.gemini/antigravity-cli sekarang?", default=True)
            if do_import:
                ok, msg = oauth_manager.import_antigravity(self.console)
                if ok:
                    self.console.print(f"[bold green]✔ {msg}[/bold green]")
                    t_ok, t_msg, t_lat = provider_manager.test_provider("antigravity")
                    test_results["antigravity"] = (t_ok, t_msg, t_lat)
                    if t_ok:
                        self.console.print(f"[bold green]✔ Terverifikasi! Latensi: {t_lat}s ({t_msg})[/bold green]")
                else:
                    self.console.print(f"[bold red]✖ {msg}[/bold red]")
                Prompt.ask("\nTekan Enter untuk kembali ke shelf...")
                return

        # Special shortcut for OpenAI Codex / ChatGPT Plus
        if p_id == "codex":
            self.console.print(Panel(
                f"[bold cyan]{icon} {p_name.upper()} (CHATGPT PLUS & CODEX SESSION)[/bold cyan]\n"
                f"Model Tersedia: [yellow]{', '.join(curr_models)}[/yellow]\n"
                f"[dim]Gunakan session token ChatGPT Plus Anda untuk model GPT-4o & o1.[/dim]",
                border_style="cyan"
            ))
            tok = Prompt.ask("Masukkan Session Token OpenAI Codex (Enter untuk auto-detect)", default="").strip()
            ok, msg = oauth_manager.import_codex(tok)
            if ok:
                self.console.print(f"[bold green]✔ {msg}[/bold green]")
            else:
                self.console.print(f"[yellow]{msg}[/yellow]")
            Prompt.ask("\nTekan Enter untuk kembali ke shelf...")
            return

        # Special shortcut for Kiro AI
        if p_id == "kiro":
            oauth_manager.import_kiro()
            self.console.print("[bold green]✔ Kiro AI Platform (Free Tier) berhasil diaktifkan![/bold green]")
            Prompt.ask("\nTekan Enter untuk kembali ke shelf...")
            return

        # Special shortcut for GitHub Copilot
        if p_id == "copilot":
            self.console.print(Panel(
                f"[bold cyan]{icon} {p_name.upper()} (OAUTH & LANGGANAN)[/bold cyan]\n"
                f"Model Tersedia: [yellow]{', '.join(curr_models)}[/yellow]\n"
                f"[dim]Anda dapat login otomatis via browser (OAuth Device Code) tanpa perlu mengetik token manual.[/dim]",
                border_style="cyan"
            ))
            do_oauth = Confirm.ask("Mulai login via GitHub OAuth sekarang?", default=True)
            if do_oauth:
                ok, msg = oauth_manager.login_github_copilot(self.console)
                if ok:
                    self.console.print(f"[bold green]✔ {msg}[/bold green]")
                    ok_t, msg_t, lat_t = provider_manager.test_provider("copilot")
                    test_results["copilot"] = (ok_t, msg_t, lat_t)
                    if ok_t:
                        self.console.print(f"[bold green]✔ Terverifikasi! Latensi: {lat_t}s ({msg_t})[/bold green]")
                else:
                    self.console.print(f"[bold red]✖ {msg}[/bold red]")
                Prompt.ask("\nTekan Enter untuk kembali ke shelf...")
                return

        # Special shortcut for local engines (Ollama, LM Studio, etc.)
        if item.get("auth_type") == "none":
            self.console.print(Panel(
                f"[bold cyan]{icon} {p_name.upper()} (LOCAL ENGINE)[/bold cyan]\n"
                f"Default Endpoint: [dim]{item['url']}[/dim]\n"
                f"Model Bawaan: [yellow]{', '.join(curr_models)}[/yellow]\n"
                f"[dim]Engine lokal gratis dan tidak membutuhkan API Key (bebas token).[/dim]",
                border_style="cyan"
            ))
            new_url = Prompt.ask("Base URL Endpoint", default=curr_url).strip()
            new_models_str = Prompt.ask("Daftar Model (pisahkan koma)", default=", ".join(curr_models)).strip()
            new_models = [m.strip() for m in new_models_str.split(",") if m.strip()]

            provider_manager.add_provider(p_id, "none", new_url, new_models)
            self.console.print(f"[bold green]✔ Pengaturan {p_name} tersimpan![/bold green]")

            test_now = Confirm.ask(f"Uji koneksi ke {p_name} sekarang?", default=True)
            if test_now:
                self.console.print(f"[dim]Menguji {p_name}...[/dim]")
                ok, msg, lat = provider_manager.test_provider(p_id)
                test_results[p_id] = (ok, msg, lat)
                if ok:
                    self.console.print(f"[bold green]✔ Berhasil terhubung! Latensi: {lat}s ({msg})[/bold green]")
                else:
                    self.console.print(f"[bold red]✖ Uji koneksi gagal: {msg}[/bold red]")
                Prompt.ask("\nTekan Enter untuk kembali ke daftar provider...")
            return

        # Standard API Key / Session Provider
        self.console.print(Panel(
            f"[bold cyan]Konfigurasi: {icon} {p_name.upper()}[/bold cyan]\n"
            f"Deskripsi: [dim]{item.get('description', '-')}[/dim]\n"
            f"Endpoint Default: [dim]{item['url']}[/dim]\n"
            f"Model Bawaan: [yellow]{', '.join(curr_models)}[/yellow]",
            border_style="cyan"
        ))

        key_prompt = f"API Key untuk {p_name} [Enter untuk simpan yang lama]"
        new_key = Prompt.ask(key_prompt, default=curr_key if not curr_key.startswith("YOUR_") else "").strip()

        url_prompt = f"Base URL Endpoint [Enter untuk tetap: {curr_url}]"
        new_url = Prompt.ask(url_prompt, default=curr_url).strip()

        models_prompt = f"Daftar Model (pisahkan koma) [Enter untuk tetap]"
        new_models_str = Prompt.ask(models_prompt, default=", ".join(curr_models)).strip()
        new_models = [m.strip() for m in new_models_str.split(",") if m.strip()]

        if new_key:
            provider_manager.add_provider(p_id, new_key, new_url, new_models)
            self.console.print(f"[bold green]✔ Pengaturan {p_name} tersimpan![/bold green]")

            # Offer immediate test
            test_now = Confirm.ask(f"Uji koneksi ke {p_name} sekarang?", default=True)
            if test_now:
                self.console.print(f"[dim]Menguji {p_name}...[/dim]")
                ok, msg, lat = provider_manager.test_provider(p_id)
                test_results[p_id] = (ok, msg, lat)
                if ok:
                    self.console.print(f"[bold green]✔ Berhasil terhubung! Latensi: {lat}s ({msg})[/bold green]")
                else:
                    self.console.print(f"[bold red]✖ Uji koneksi gagal: {msg}[/bold red]")
                Prompt.ask("\nTekan Enter untuk kembali ke daftar provider...")
        else:
            self.console.print("[dim]Tidak ada perubahan API Key yang disimpan.[/dim]")
            time.sleep(1.0)

    # =========================================================================
    # STAGE 3: Soul & Identity Manifest
    # =========================================================================
    def stage_3_soul_and_agents(self) -> None:
        self._header("Agent Persona & Soul Configuration")
        default_soul = str(PKG_ROOT / "SOUL.md")
        curr_soul = config.get("paths.soul_path") or default_soul

        self.console.print(f"Active SOUL manifest: [bold green]{curr_soul}[/bold green]")
        self.console.print("1. Keep default High-Agency Engineering SOUL")
        self.console.print("2. Browse / Pick custom SOUL file from disk")
        
        choice = Prompt.ask("Choose option or type 'b' to go back", choices=["1", "2", "b"], default="1")
        if choice == "b":
            self.current_stage -= 1
            return

        if choice == "2":
            picked = pick_file("Select custom SOUL markdown file", default_soul)
            if picked:
                config.set("paths.soul_path", picked, auto_save=False)
                self.console.print(f"[green]Selected: {picked}[/green]")
        else:
            config.set("paths.soul_path", None, auto_save=False)

        self.current_stage += 1

    # =========================================================================
    # STAGE 4: Prompt Injection & Anti-Refusal (9Router Pro)
    # =========================================================================
    def stage_4_prompt_injection(self) -> None:
        self._header("Prompt Injection & Anti-Refusal Tuning")
        curr_global = config.get("router.prompt_injections.global", "")
        curr_priming = config.get("router.prompt_injections.chat_script_priming", True)

        self.console.print("[dim]Chat Script Priming injects synthetic administrative turns to prevent refusals.[/dim]")
        priming_choice = Confirm.ask("Enable Chat Script Priming for 100% Anti-Refusal compliance?", default=curr_priming)
        config.set("router.prompt_injections.chat_script_priming", priming_choice, auto_save=False)

        custom_prompt = Prompt.ask("Optional Global System Prompt override (or press Enter to skip)", default=curr_global)
        if custom_prompt.strip().lower() == "b":
            self.current_stage -= 1
            return

        config.set("router.prompt_injections.global", custom_prompt.strip(), auto_save=False)
        self.current_stage += 1

    # =========================================================================
    # STAGE 5: Messaging Gateway & Security Pairing
    # =========================================================================
    def stage_5_gateways_and_auth(self) -> None:
        self._header("Messaging Gateways & Security Authorization")
        curr_token = config.get("gateways.telegram.token", "")
        curr_code = config.get("security.pairing_code", "APEX-2026")

        self.console.print("[dim]Telegram Bot integration allows remote 24/7 access from your phone.[/dim]")
        token_val = Prompt.ask("Telegram Bot Token (or press Enter to skip)", default=curr_token)
        if token_val.strip().lower() == "b":
            self.current_stage -= 1
            return

        config.set("gateways.telegram.token", token_val.strip(), auto_save=False)

        code_val = Prompt.ask("Secret Security Pairing Code (for authenticating chats)", default=curr_code)
        if code_val.strip().lower() == "b":
            self.current_stage -= 1
            return

        config.set("security.pairing_code", code_val.strip(), auto_save=False)
        self.current_stage += 1

    # =========================================================================
    # STAGE 6: Live Diagnostic Healthcheck
    # =========================================================================
    def stage_6_diagnostics(self) -> None:
        self._header("Live Diagnostics & Provider Test-All")
        self.console.print("Testing connectivity to all configured providers...\n")

        table = Table(title="Diagnostic Healthcheck Results", show_lines=True)
        table.add_column("Provider", style="bold cyan")
        table.add_column("Status", style="bold")
        table.add_column("Latency", justify="right")
        table.add_column("Details", style="dim")

        results = provider_manager.test_all()
        for p_name, (success, msg, latency) in results.items():
            status_badge = "[bold green]✔ OK[/bold green]" if success else "[bold red]✖ FAILED[/bold red]"
            lat_str = f"{latency}s" if latency > 0 else "-"
            table.add_row(p_name.upper(), status_badge, lat_str, msg)

        self.console.print(table)
        self.console.print()

        choice = Prompt.ask("Press Enter to finalize setup, or 'b' to reconfigure providers", default="")
        if choice.strip().lower() == "b":
            self.current_stage = 2
            return

        self.current_stage += 1


def run_setup() -> None:
    """Entry point for `apex setup` command."""
    wizard = SetupWizard()
    wizard.run()
