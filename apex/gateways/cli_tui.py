"""Pi Agent-Style Minimalist Terminal UI/UX (prompt_toolkit + rich)."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apex.agent import default_agent
from apex.config import config, DATA_DIR
from apex.router.ledger import token_ledger
from apex.router.model_switcher import model_switcher
from apex.security.anti_refusal import anti_refusal_engine
from apex.tools.backends import backend_manager

# Prompt toolkit custom styling (Pi Agent aesthetic)
PT_STYLE = Style.from_dict({
    "prompt_sym": "#00d7af bold",
    "prompt_name": "#ffffff bold",
    "prompt_arrow": "#00d7af bold",
    "rprompt": "#666666 italic",
})


class PiTerminalTUI:
    """Minimalist, clean terminal pair-programming interface inspired by Pi Agent."""

    def __init__(self, agent: Optional[Any] = None) -> None:
        self.console = Console()
        self.agent = agent or default_agent
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        history_file = DATA_DIR / "tui_history.txt"
        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            style=PT_STYLE
        )

    def print_welcome(self) -> None:
        """Render the sleek Pi Agent-style header banner."""
        active_model = config.default_model
        active_provider = config.active_provider
        active_backend = config.active_backend
        workspace = str(config.workspace)

        self.console.print()
        self.console.print(Panel(
            f"[bold cyan]▲ APEX[/bold cyan] [bold white]v1.0.0[/bold white] [dim]· Sovereign Hybrid AI Agent (Pi-Style Terminal)[/dim]\n\n"
            f"  [bold white]Model Utama :[/bold white] [bold cyan]{active_model}[/bold cyan] [dim]({active_provider.upper()})[/dim]\n"
            f"  [bold white]Workspace   :[/bold white] [dim]{workspace}[/dim]\n"
            f"  [bold white]Backend     :[/bold white] [green]{active_backend}[/green] · [bold magenta]SOUL: Sovereign Zero-Refusal[/bold magenta]\n\n"
            f"  [dim]Perintah: [bold cyan]/help[/bold cyan] · [bold cyan]/model[/bold cyan] · [bold cyan]/provider[/bold cyan] · [bold cyan]/stats[/bold cyan] · [bold cyan]/clear[/bold cyan] · [bold cyan]/exit[/bold cyan] | Host: [bold yellow]$ <perintah>[/bold yellow][/dim]",
            title="[bold cyan]● APEX AGENT[/bold cyan]",
            border_style="cyan",
            padding=(0, 2)
        ))
        self.console.print()

    def format_tool_chip(self, tool_name: str, args_summary: str, output: str, is_error: bool = False) -> None:
        """Render collapsible Pi Agent-style tool execution card."""
        lines = output.splitlines() if output else []
        line_count = len(lines)
        status_icon = "❌" if is_error else "⚡"
        border_col = "red" if is_error else "cyan"

        args_disp = f" ({args_summary})" if args_summary else ""
        header = f"{status_icon} [bold cyan]{tool_name}[/bold cyan]{args_disp} · [yellow]{line_count} baris[/yellow]"

        if not output.strip():
            preview = "[dim](selesai tanpa output)[/dim]"
        elif line_count <= 8:
            preview = output.strip()
        else:
            preview = "\n".join(lines[:8]) + f"\n[dim]... (+{line_count - 8} baris lainnya)[/dim]"

        self.console.print(Panel(
            preview,
            title=header,
            title_align="left",
            border_style=border_col,
            padding=(0, 1)
        ))

    def render_markdown_chunk(self, text: str) -> None:
        """Render streaming or final markdown text cleanly."""
        self.console.print(Markdown(text))

    def handle_slash_command(self, cmd: str) -> bool:
        """Process slash commands. Returns True if handled."""
        parts = cmd.strip().split()
        root_cmd = parts[0].lower()

        if root_cmd in ["/exit", "/quit"]:
            self.console.print("[dim]Sampai jumpa! Keluar dari Apex...[/dim]")
            sys.exit(0)

        elif root_cmd == "/help":
            table = Table(title="[bold cyan]Daftar Perintah Terminal APEX[/bold cyan]", show_lines=False, border_style="dim")
            table.add_column("Perintah", style="bold yellow")
            table.add_column("Keterangan", style="dim")
            table.add_row("/model [nama]", "Lihat daftar model atau ganti model AI aktif")
            table.add_row("/provider", "Buka rak provider AI (9Router Pro Shelf)")
            table.add_row("/backend [nama]", "Ganti backend eksekusi (local, docker, ssh)")
            table.add_row("/stats", "Lihat statistik penggunaan token & estimasi biaya")
            table.add_row("/soul", "Lihat doktrin SOUL & AGENTS anti-refusal")
            table.add_row("/clear", "Bersihkan layar terminal")
            table.add_row("/exit /quit", "Keluar dari sesi interaktif")
            table.add_row("$ <perintah>", "Eksekusi perintah host langsung (bypass LLM)")
            self.console.print(table)
            self.console.print()
            return True

        elif root_cmd == "/model":
            if len(parts) > 1:
                new_m = model_switcher.switch_model(parts[1])
                self.console.print(f"[bold green]✔ Model aktif berhasil diganti ke: {new_m}[/bold green]\n")
            else:
                models = model_switcher.get_available_models()
                self.console.print("\n[bold cyan]Daftar Model yang Tersedia:[/bold cyan]")
                for m in models:
                    active = " [bold green]★ (Aktif)[/bold green]" if m["id"] == config.default_model else ""
                    self.console.print(f"  • [yellow]{m['id']}[/yellow] [dim]({m['provider']})[/dim]{active}")
                self.console.print("[dim]Gunakan: /model <nama_model> untuk mengganti[/dim]\n")
            return True

        elif root_cmd == "/backend":
            if len(parts) > 1:
                ok, msg = backend_manager.switch_backend(parts[1])
                style = "green" if ok else "red"
                self.console.print(f"[{style}]{msg}[/{style}]\n")
            else:
                self.console.print(f"Backend aktif saat ini: [bold green]{config.active_backend}[/bold green]")
                self.console.print("Pilihan tersedia: local, docker, ssh, modal, daytona\n")
            return True

        elif root_cmd in ["/provider", "/providers"]:
            from apex.gateways.setup_wizard import SetupWizard
            SetupWizard().run_provider_shelf(standalone=True)
            self.print_welcome()
            return True

        elif root_cmd == "/stats":
            self.console.print(token_ledger.get_summary_text())
            self.console.print()
            return True

        elif root_cmd == "/soul":
            from apex.prompt_builder import prompt_builder
            soul_txt = prompt_builder.load_soul_manifest()
            self.console.print(Panel(
                soul_txt[:1200] + ("\n[dim]... (+ selengkapnya di SOUL.md)[/dim]" if len(soul_txt) > 1200 else ""),
                title="[bold magenta]SOUL Manifest — Operator Supremacy & Zero-Refusal[/bold magenta]",
                border_style="magenta"
            ))
            self.console.print()
            return True

        elif root_cmd in ["/clear", "/reset"]:
            from apex.memory.sessions import session_manager
            session = session_manager.get_or_create("cli_interactive")
            session.messages = []
            session_manager.save(session)
            self.console.clear()
            self.print_welcome()
            self.console.print("[bold green]✔ Layar & riwayat percakapan berhasil di-reset bersih![/bold green]\n")
            return True

        return False

    def run_loop(self) -> None:
        """Main terminal event loop with Pi Agent-style layout & live spinner."""
        self.print_welcome()

        while True:
            try:
                active_model = config.default_model
                active_provider = config.active_provider

                prompt_label = [
                    ("class:prompt_sym", "▲ "),
                    ("class:prompt_name", "apex"),
                    ("class:prompt_arrow", " › "),
                ]
                rprompt_str = f"[{active_model}]"

                user_input = self.session.prompt(
                    prompt_label,
                    rprompt=rprompt_str
                ).strip()

                if not user_input:
                    continue

                # Handle slash commands
                if user_input.startswith("/"):
                    self.handle_slash_command(user_input)
                    continue

                # Handle direct host override ($ <cmd>, ! <cmd>, or direct CLI commands)
                override_cmd = anti_refusal_engine.is_direct_host_override(user_input)
                if override_cmd:
                    code, stdout, stderr = backend_manager.execute(override_cmd)
                    out = stdout if stdout else stderr
                    self.format_tool_chip("host_direct", override_cmd, out, is_error=(code != 0))
                    continue

                # Live status tracking hooks for tool execution
                start_time = time.time()
                last_tool_args: Dict[str, Any] = {}

                def on_tool_start(fn_name: str, args: Dict[str, Any]) -> None:
                    last_tool_args[fn_name] = args
                    args_disp = ", ".join(f"{k}={repr(v)}" for k, v in list(args.items())[:2])
                    if len(args) > 2:
                        args_disp += "..."
                    status.update(f"[bold yellow]⚡ Menjalankan tool: {fn_name}({args_disp})...[/bold yellow]")

                def on_tool_end(fn_name: str, output: str, is_error: bool) -> None:
                    args = last_tool_args.get(fn_name, {})
                    args_disp = ", ".join(f"{k}={repr(v)}" for k, v in list(args.items())[:2])
                    if len(args) > 2:
                        args_disp += "..."
                    self.format_tool_chip(fn_name, args_disp, output, is_error)
                    status.update(f"[cyan]⠋ Menganalisis output ({active_model})...[/cyan]")

                # Execute with Live Spinner (Pi Agent Thinking state)
                with self.console.status(
                    f"[bold cyan]⠋ Menghubungi {active_provider.upper()} ({active_model})...[/bold cyan]",
                    spinner="dots"
                ) as status:
                    try:
                        response_text = self.agent.run(
                            user_prompt=user_input,
                            session_id="cli_interactive",
                            channel="cli_tui",
                            on_tool_start=on_tool_start,
                            on_tool_end=on_tool_end
                        )
                    except Exception as e:
                        response_text = f"❌ Terjadi kesalahan saat memproses permintaan: {str(e)}"

                # Render Agent Response (Pi Agent styling)
                elapsed = round(time.time() - start_time, 2)
                self.console.print()
                self.console.print(f"[bold cyan]● Apex[/bold cyan] [dim]({active_model})[/dim]")
                self.console.print(Markdown(response_text))
                self.console.print(f"[dim]⏱ {elapsed}s · {active_provider.upper()}[/dim]\n")

            except KeyboardInterrupt:
                self.console.print("\n[dim]Perintah dibatalkan. Tekan Ctrl+D atau ketik /exit untuk keluar.[/dim]\n")
            except EOFError:
                self.console.print("\n[dim]Sampai jumpa![/dim]")
                break


def start_tui(agent: Optional[Any] = None) -> None:
    """Launch the Pi Agent-style interactive terminal."""
    tui = PiTerminalTUI(agent=agent)
    tui.run_loop()
