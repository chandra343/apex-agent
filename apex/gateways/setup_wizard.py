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
    # STAGE 2: AI Providers & API Keys
    # =========================================================================
    def stage_2_providers(self) -> None:
        self._header("AI Providers & Model API Keys")
        self.console.print("[dim]Configure at least one provider. Press Enter on empty to skip.[/dim]\n")

        providers = config.get("providers", {})
        target_keys = ["anthropic", "openai", "deepseek", "groq", "openrouter", "ollama"]

        for p_name in target_keys:
            existing = providers.get(p_name, {}).get("api_key", "")
            placeholder = " (configured)" if existing and "YOUR_" not in existing else " (empty)"
            
            prompt_text = f"API Key for [bold]{p_name.upper()}[/bold]{placeholder}"
            val = Prompt.ask(prompt_text, default=existing if "YOUR_" not in existing else "")
            
            if val.strip().lower() == "b":
                self.current_stage = max(1, self.current_stage - 1)
                return

            if val.strip():
                if p_name not in providers:
                    providers[p_name] = {"api_key": val.strip(), "base_url": "", "models": []}
                else:
                    providers[p_name]["api_key"] = val.strip()

        config.set("providers", providers, auto_save=False)
        provider_manager.sync_with_config()
        self.current_stage += 1

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
