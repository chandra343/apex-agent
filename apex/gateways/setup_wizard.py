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
        """Interactive Provider Shelf UI/UX ala 9Router Pro & Zeline."""
        standard_catalog = [
            {"id": "anthropic", "name": "Anthropic", "icon": "🟣", "url": "https://api.anthropic.com/v1", "models": ["claude-3-7-sonnet-latest", "claude-3-5-haiku-latest"]},
            {"id": "openai", "name": "OpenAI", "icon": "🟢", "url": "https://api.openai.com/v1", "models": ["gpt-4o", "gpt-4o-mini", "o3-mini"]},
            {"id": "deepseek", "name": "DeepSeek", "icon": "🔵", "url": "https://api.deepseek.com/v1", "models": ["deepseek-chat", "deepseek-reasoner"]},
            {"id": "groq", "name": "Groq", "icon": "⚡", "url": "https://api.groq.com/openai/v1", "models": ["llama-3.3-70b-versatile", "whisper-large-v3"]},
            {"id": "gemini", "name": "Google Gemini", "icon": "💎", "url": "https://generativelanguage.googleapis.com/v1beta/openai", "models": ["gemini-2.0-flash", "gemini-2.0-pro-exp"]},
            {"id": "openrouter", "name": "OpenRouter", "icon": "🌐", "url": "https://openrouter.ai/api/v1", "models": ["deepseek/deepseek-r1:free", "meta-llama/llama-3.3-70b-instruct:free"]},
            {"id": "together", "name": "Together AI", "icon": "🤝", "url": "https://api.together.xyz/v1", "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "Qwen/Qwen2.5-Coder-32B-Instruct"]},
            {"id": "mistral", "name": "Mistral AI", "icon": "🌪️", "url": "https://api.mistral.ai/v1", "models": ["mistral-large-latest", "codestral-latest"]},
            {"id": "ollama", "name": "Ollama (Lokal)", "icon": "🦙", "url": "http://localhost:11434/v1", "models": ["qwen2.5-coder:7b", "llama3.2:3b"]},
        ]

        test_results: Dict[str, Tuple[bool, str, float]] = {}

        while True:
            if not standalone:
                self._header("AI Provider Shelf (Gaya 9Router Pro & Zeline)")
            else:
                self.console.clear()
                self.console.print(Panel.fit(
                    "[bold cyan]AI PROVIDER SHELF & MANAGER[/bold cyan]\n"
                    "[dim]Kelola seluruh endpoint dan API key provider AI Anda dengan mudah.[/dim]",
                    border_style="cyan"
                ))

            configured_providers = config.get("providers", {})

            # Merge standard catalog with any custom providers from config
            all_shelf_items: list[dict[str, Any]] = []
            known_ids = set()

            for item in standard_catalog:
                all_shelf_items.append(dict(item))
                known_ids.add(item["id"])

            for c_id, c_data in configured_providers.items():
                if c_id not in known_ids:
                    all_shelf_items.append({
                        "id": c_id,
                        "name": c_id.upper(),
                        "icon": "🔌",
                        "url": c_data.get("base_url", "-"),
                        "models": c_data.get("models", [f"{c_id}-model"])
                    })

            # Render Table
            table = Table(
                title="[bold yellow]Daftar Semua Provider AI yang Tersedia (9Router Pro & Zeline Style)[/bold yellow]",
                show_lines=True,
                header_style="bold cyan",
                expand=True
            )
            table.add_column("No", justify="center", style="bold yellow", no_wrap=True, width=4)
            table.add_column("Provider", style="bold", no_wrap=True, width=20)
            table.add_column("Endpoint (Base URL)", style="dim")
            table.add_column("Model Bawaan", style="cyan")
            table.add_column("Status API Key", style="bold", no_wrap=True, width=24)

            for idx, item in enumerate(all_shelf_items, 1):
                p_id = item["id"]
                cfg_data = configured_providers.get(p_id, {})
                api_key = cfg_data.get("api_key", "").strip()
                base_url = cfg_data.get("base_url") or item["url"]
                models_list = cfg_data.get("models") or item["models"]
                models_preview = ", ".join(models_list[:2])
                if len(models_list) > 2:
                    models_preview += f" (+{len(models_list) - 2})"

                # Check status
                if p_id in test_results:
                    ok, msg, lat = test_results[p_id]
                    if ok:
                        status_str = f"[bold green]🟢 OK ({lat}s)[/bold green]"
                    else:
                        status_str = f"[bold red]✖ Error: {msg[:18]}[/bold red]"
                elif api_key and "YOUR_" not in api_key:
                    if p_id == "ollama" and api_key == "none":
                        status_str = "[bold green]🟢 Aktif (Lokal / No Key)[/bold green]"
                    else:
                        masked = api_key[:5] + "..." + api_key[-4:] if len(api_key) > 9 else "••••••"
                        status_str = f"[bold green]🟢 Terpasang ({masked})[/bold green]"
                else:
                    status_str = "[dim]⚪ Belum Diatur[/dim]"

                table.add_row(
                    str(idx),
                    f"{item['icon']} {item['name']}",
                    base_url,
                    models_preview,
                    status_str
                )

            self.console.print(table)
            self.console.print(
                "\n[bold cyan]Menu Aksi:[/bold cyan]\n"
                f" • Masukkan angka [bold yellow]1 - {len(all_shelf_items)}[/bold yellow] : Pilih provider untuk memasukkan / mengedit API Key & URL\n"
                " • Masukkan [bold yellow]+[/bold yellow]       : Tambah Custom Provider Baru (vLLM, LM Studio, 9Router, dll.)\n"
                " • Masukkan [bold yellow]t[/bold yellow]       : Test All (Uji koneksi & latensi semua provider serentak)\n"
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
                    # Check if at least 1 provider is configured
                    has_any = any(
                        p.get("api_key") and "YOUR_" not in p.get("api_key")
                        for p in configured_providers.values()
                    )
                    if not has_any:
                        proceed = Confirm.ask("[yellow]Peringatan: Belum ada provider yang dikonfigurasi API key-nya. Yakin ingin lanjut?[/yellow]", default=False)
                        if not proceed:
                            continue
                    self.current_stage += 1
                break

            if choice == "t":
                self.console.print("\n[cyan]Menguji seluruh koneksi provider...[/cyan]")
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

        self.console.print(Panel(
            f"[bold cyan]Konfigurasi: {icon} {p_name.upper()}[/bold cyan]\n"
            f"Endpoint Default: [dim]{item['url']}[/dim]\n"
            f"Model Bawaan: [yellow]{', '.join(curr_models)}[/yellow]",
            border_style="cyan"
        ))

        key_prompt = f"API Key untuk {p_name} [Enter untuk simpan yang lama]"
        new_key = Prompt.ask(key_prompt, default=curr_key if "YOUR_" not in curr_key else "").strip()

        url_prompt = f"Base URL Endpoint [Enter untuk tetap: {curr_url}]"
        new_url = Prompt.ask(url_prompt, default=curr_url).strip()

        models_prompt = f"Daftar Model (pisahkan koma) [Enter untuk tetap]"
        new_models_str = Prompt.ask(models_prompt, default=", ".join(curr_models)).strip()
        new_models = [m.strip() for m in new_models_str.split(",") if m.strip()]

        if p_id == "ollama" and not new_key:
            new_key = "none"

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
