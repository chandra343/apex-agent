"""Pi Agent-Style Minimalist Terminal UI/UX (prompt_toolkit + rich)."""
from __future__ import annotations

import sys
import time
from typing import Any, Callable, Dict, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from apex.config import config, DATA_DIR
from apex.router.ledger import token_ledger
from apex.router.model_switcher import model_switcher
from apex.tools.backends import backend_manager

# Prompt toolkit custom styling
PT_STYLE = Style.from_dict({
    "prompt": "#00d7af bold",
    "model_tag": "#888888",
})


class PiTerminalTUI:
    """Minimalist, clean terminal pair-programming interface."""

    def __init__(self, agent_runner: Optional[Callable[[str], Any]] = None) -> None:
        self.console = Console()
        self.agent_runner = agent_runner
        history_file = DATA_DIR / "tui_history.txt"
        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            style=PT_STYLE
        )

    def print_welcome(self) -> None:
        active_model = config.default_model
        active_backend = config.active_backend
        self.console.print(f"[bold cyan]▲ APEX[/bold cyan] [dim]v1.0.0 · {active_model} · backend:{active_backend}[/dim]")
        self.console.print("[dim]Type your message, or /help for commands. Press Ctrl+C or /exit to quit.[/dim]\n")

    def format_tool_chip(self, tool_name: str, args_summary: str, output: str, is_error: bool = False) -> None:
        """Render collapsible-style tool execution chip."""
        line_count = len(output.splitlines())
        status_icon = "❌" if is_error else "⚡"
        border_col = "red" if is_error else "cyan"

        header = f"{status_icon} [bold]{tool_name}[/bold] [dim]({args_summary})[/dim] — [yellow]{line_count} lines[/yellow]"
        preview = "\n".join(output.splitlines()[:6])
        if line_count > 6:
            preview += f"\n[dim]... (+{line_count - 6} more lines)[/dim]"

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
            self.console.print("[dim]Exiting Apex...[/dim]")
            sys.exit(0)

        elif root_cmd == "/help":
            self.console.print(
                "\n[bold cyan]Available Commands:[/bold cyan]\n"
                "• [bold]/model [name][/bold]  - Switch active AI model dynamically\n"
                "• [bold]/provider[/bold]      - Open 9Router Pro-style AI Provider Shelf\n"
                "• [bold]/backend [name][/bold]- Switch execution backend (local, docker, ssh)\n"
                "• [bold]/stats[/bold]          - View token consumption and estimated costs\n"
                "• [bold]/clear[/bold]          - Clear terminal screen\n"
                "• [bold]/exit[/bold]           - Exit interactive session\n"
                "• [bold]$ <cmd>[/bold]        - Direct host override (bypass LLM)\n"
            )
            return True

        elif root_cmd == "/model":
            if len(parts) > 1:
                new_m = model_switcher.switch_model(parts[1])
                self.console.print(f"[bold green]✔ Active model switched to: {new_m}[/bold green]")
            else:
                models = model_switcher.get_available_models()
                self.console.print("[bold cyan]Available Models:[/bold cyan]")
                for m in models:
                    active = " [green](active)[/green]" if m["id"] == config.default_model else ""
                    self.console.print(f"  • {m['display']}{active}")
                self.console.print("[dim]Use: /model <name> to switch[/dim]")
            return True

        elif root_cmd == "/backend":
            if len(parts) > 1:
                ok, msg = backend_manager.switch_backend(parts[1])
                style = "green" if ok else "red"
                self.console.print(f"[{style}]{msg}[/{style}]")
            else:
                self.console.print(f"Active backend: [bold green]{config.active_backend}[/bold green]")
                self.console.print("Available: local, docker, ssh, modal, daytona")
            return True

        elif root_cmd in ["/provider", "/providers"]:
            from apex.gateways.setup_wizard import SetupWizard
            SetupWizard().run_provider_shelf(standalone=True)
            self.print_welcome()
            return True

        elif root_cmd == "/stats":
            self.console.print(token_ledger.get_summary_text())
            return True

        elif root_cmd == "/clear":
            self.console.clear()
            self.print_welcome()
            return True

        return False

    def run_loop(self) -> None:
        """Main terminal event loop."""
        self.print_welcome()

        while True:
            try:
                active_model = config.default_model
                active_backend = config.active_backend
                prompt_label = [
                    ("class:prompt", "apex"),
                    ("class:model_tag", f" [{active_model.split('/')[-1]}] > ")
                ]

                user_input = self.session.prompt(prompt_label).strip()
                if not user_input:
                    continue

                # Handle slash commands
                if user_input.startswith("/"):
                    self.handle_slash_command(user_input)
                    continue

                # Handle direct host override ($ <cmd>)
                if user_input.startswith("$ "):
                    cmd = user_input[2:].strip()
                    code, out = backend_manager.execute(cmd)
                    self.console.print(out)
                    continue

                # Run through agent
                if self.agent_runner:
                    self.agent_runner(user_input)
                else:
                    self.console.print(f"[dim]Echo: {user_input}[/dim]")

            except KeyboardInterrupt:
                self.console.print("\n[dim]Interrupted. Press Ctrl+D or type /exit to quit.[/dim]")
            except EOFError:
                break


def start_tui(agent_runner: Optional[Callable[[str], Any]] = None) -> None:
    tui = PiTerminalTUI(agent_runner)
    tui.run_loop()
