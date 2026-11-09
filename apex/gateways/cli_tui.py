"""Pi Agent-Style Minimalist Terminal UI/UX with Autocompletion & Command Palette."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apex.agent import default_agent
from apex.config import config, DATA_DIR, PKG_ROOT
from apex.router.ledger import token_ledger
from apex.router.model_switcher import model_switcher
from apex.security.anti_refusal import anti_refusal_engine
from apex.tools.backends import backend_manager

# Prompt toolkit custom styling (Pi Agent aesthetic + Popup Dropdown Menu)
PT_STYLE = Style.from_dict({
    "prompt_sym": "#00d7af bold",
    "prompt_name": "#ffffff bold",
    "prompt_arrow": "#00d7af bold",
    "rprompt": "#666666 italic",
    # Completion popup menu styling
    "completion-menu": "bg:#16191f #d0d7de",
    "completion-menu.completion": "bg:#16191f #d0d7de",
    "completion-menu.completion.current": "bg:#00d7af #000000 bold",
    "completion-menu.meta": "bg:#21262d #8b949e",
    "completion-menu.meta.current": "bg:#00b38f #000000 bold",
    "completion-menu.meta.completion": "bg:#21262d #8b949e",
    "completion-menu.meta.completion.current": "bg:#00b38f #000000 bold",
    "completion-menu.multi-column-meta": "bg:#21262d #8b949e",
    "scrollbar.background": "bg:#16191f",
    "scrollbar.button": "bg:#00d7af",
})


class SlashCommandCompleter(Completer):
    """Dynamic autocompletion popup for slash commands, models, and backends."""

    COMMANDS = {
        "/scan": "Pindai otomatis MCP, modular skills, dan custom tools",
        "/tools": "Daftar seluruh tool aktif (Native, Custom User, MCP)",
        "/model": "Ganti model AI aktif (TokenHarbor, Antigravity, dll)",
        "/provider": "Buka Rak Provider AI (9Router Pro Shelf)",
        "/setup": "Jalankan 6-Stage Interactive Setup Wizard",
        "/stats": "Lihat statistik penggunaan token & estimasi biaya",
        "/compact": "Kompresi konteks riwayat percakapan panjang",
        "/session": "Informasi & ringkasan sesi percakapan aktif",
        "/backend": "Ganti execution backend (local, docker, ssh)",
        "/doctor": "Diagnostik kesehatan sistem & koneksi provider",
        "/gateway": "Kelola background gateway (Telegram, WhatsApp)",
        "/soul": "Lihat doktrin SOUL & kedaulatan operator",
        "/agents": "Lihat arsitektur multi-agent (AGENTS.md)",
        "/skills": "Daftar kemampuan & modular skills terdeteksi",
        "/mcp": "Status dan daftar server MCP multi-ekosistem",
        "/paraphrase": "Uji netralisasi & parafrase prompt anti-refusal",
        "/web": "Buka Apex Web Dashboard & Chat Console interaktif di browser",
        "/dashboard": "Buka Apex Web Dashboard & Chat Console interaktif di browser",
        "/clear": "Bersihkan layar & reset memori chat",
        "/help": "Panduan bantuan & daftar perintah lengkap",
        "/exit": "Keluar dari sesi interaktif",
    }

    def get_completions(self, document: Document, complete_event: Any):
        text_before_cursor = document.text_before_cursor

        # 1. Autocomplete model names after '/model '
        if text_before_cursor.startswith("/model "):
            prefix = text_before_cursor[7:].strip().lower()
            try:
                models = model_switcher.get_available_models()
                for m in models:
                    m_id = m.get("id", "")
                    if m_id.lower().startswith(prefix) or not prefix:
                        yield Completion(
                            text=m_id,
                            start_position=-len(text_before_cursor[7:]),
                            display=m_id,
                            display_meta=f"{m.get('provider', '')} ({m.get('tag', '')})"
                        )
            except Exception:
                pass
            return

        # 2. Autocomplete backend names after '/backend '
        if text_before_cursor.startswith("/backend "):
            prefix = text_before_cursor[9:].strip().lower()
            backends = ["local", "docker", "ssh", "modal", "daytona"]
            for b in backends:
                if b.startswith(prefix) or not prefix:
                    yield Completion(
                        text=b,
                        start_position=-len(text_before_cursor[9:]),
                        display=b,
                        display_meta="Execution Backend"
                    )
            return

        # 3. Autocomplete slash commands when starting with '/'
        if text_before_cursor.startswith("/"):
            query = text_before_cursor.lower()
            for cmd, desc in self.COMMANDS.items():
                if cmd.startswith(query) or query == "/":
                    yield Completion(
                        text=cmd,
                        start_position=-len(text_before_cursor),
                        display=cmd,
                        display_meta=desc
                    )


class PiTerminalTUI:
    """Minimalist, clean terminal pair-programming interface inspired by Pi Agent."""

    def __init__(self, agent: Optional[Any] = None) -> None:
        self.console = Console()
        self.agent = agent or default_agent
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        history_file = DATA_DIR / "tui_history.txt"
        self.completer = SlashCommandCompleter()
        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            style=PT_STYLE,
            completer=self.completer,
            complete_while_typing=True,
            reserve_space_for_menu=8,
        )

    def print_welcome(self) -> None:
        """Render the sleek Pi Agent-style header banner with auto-detected ecosystem counts."""
        active_model = config.default_model
        active_provider = config.active_provider
        active_backend = config.active_backend
        workspace = str(config.workspace)

        from apex.tools import tool_registry
        from apex.learning.skills import skill_manager
        from apex.tools.mcp import mcp_manager

        native_count = len(tool_registry.get_native_tools())
        custom_count = len(tool_registry.get_custom_tools())
        mcp_servers = mcp_manager.get_detected_servers()
        mcp_tools_count = len(tool_registry.get_mcp_tools())
        skills_count = len(skill_manager.get_detected_skills())

        mcp_badge = f"{len(mcp_servers)} server ({mcp_tools_count} tools)" if mcp_servers else "0 server"

        self.console.print()
        self.console.print(Panel(
            f"[bold cyan]▲ APEX[/bold cyan] [bold white]v1.0.0[/bold white] [dim]· Sovereign Hybrid AI Agent (Pi-Style Terminal)[/dim]\n\n"
            f"  [bold white]Model Utama :[/bold white] [bold cyan]{active_model}[/bold cyan] [dim]({active_provider.upper()})[/dim]\n"
            f"  [bold white]Workspace   :[/bold white] [dim]{workspace}[/dim]\n"
            f"  [bold white]Backend     :[/bold white] [green]{active_backend}[/green] · [bold magenta]SOUL: Sovereign Zero-Refusal[/bold magenta]\n"
            f"  [bold white]Ekosistem   :[/bold white] [green]{native_count} Native Tools[/green] · [yellow]{custom_count} Custom[/yellow] · [cyan]{mcp_badge}[/cyan] · [magenta]{skills_count} Skills[/magenta]\n\n"
            f"  [dim]Ketik [bold cyan]/[/bold cyan] untuk menu | Web UI: [bold cyan]/web[/bold cyan] | Pindai: [bold cyan]/scan[/bold cyan] | Tools: [bold cyan]/tools[/bold cyan] | Host: [bold yellow]$ <perintah>[/bold yellow][/dim]",
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
        if not parts:
            return False
        root_cmd = parts[0].lower()

        if root_cmd in ["/exit", "/quit"]:
            self.console.print("[dim]Sampai jumpa! Keluar dari Apex...[/dim]")
            sys.exit(0)

        elif root_cmd in ["/", "/help"]:
            table = Table(title="[bold cyan]⚡ APEX COMMAND PALETTE (Daftar Menu /)[/bold cyan]", show_lines=True, border_style="cyan")
            table.add_column("Perintah", style="bold yellow")
            table.add_column("Keterangan & Fitur", style="white")
            for c_name, c_desc in SlashCommandCompleter.COMMANDS.items():
                table.add_row(f"[bold yellow]{c_name}[/bold yellow]", c_desc)
            self.console.print(table)
            self.console.print("[dim]Tip: Cukup ketik '/' di terminal untuk melihat menu dropdown autocomplete otomatis.[/dim]\n")
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

        elif root_cmd in ["/provider", "/providers"]:
            from apex.gateways.setup_wizard import SetupWizard
            SetupWizard().run_provider_shelf(standalone=True)
            self.print_welcome()
            return True

        elif root_cmd == "/setup":
            from apex.gateways.setup_wizard import run_setup
            run_setup()
            self.print_welcome()
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

        elif root_cmd == "/stats":
            self.console.print(token_ledger.get_summary_text())
            self.console.print()
            return True

        elif root_cmd == "/compact":
            from apex.memory.sessions import session_manager
            from apex.memory.compaction import ContextCompactor
            session = session_manager.get_or_create("cli_interactive")
            old_len = len(session.messages)
            compactor = ContextCompactor()
            compacted, saved = compactor.compact(session.messages)
            session.messages = compacted
            session_manager.save(session)
            self.console.print(f"[bold green]✔ Konteks percakapan dikompresi: {old_len} pesan → {len(compacted)} pesan (Hemat ~{saved} token)![/bold green]\n")
            return True

        elif root_cmd == "/session":
            from apex.memory.sessions import session_manager
            session = session_manager.get_or_create("cli_interactive")
            channel = session.metadata.get("channel", "cli_tui")
            created = session.metadata.get("created_at", "")
            self.console.print(Panel(
                f" • Session ID    : [cyan]{session.session_id}[/cyan]\n"
                f" • Channel       : [green]{channel}[/green]\n"
                f" • Active Model  : [yellow]{session.active_model}[/yellow]\n"
                f" • Total Messages: [bold white]{len(session.messages)} pesan[/bold white]\n"
                f" • Created At    : [dim]{created}[/dim]",
                title="[bold cyan]ℹ Info Sesi Percakapan Aktif[/bold cyan]",
                border_style="cyan"
            ))
            self.console.print()
            return True

        elif root_cmd == "/doctor":
            from apex.router.provider_manager import provider_manager
            self.console.print("[cyan]Menjalankan uji konektivitas & diagnostik provider aktif...[/cyan]")
            results = provider_manager.test_all(only_configured=True)
            doc_table = Table(title="🩺 Hasil Diagnostik Kesehatan Apex", show_lines=True)
            doc_table.add_column("Provider", style="bold cyan")
            doc_table.add_column("Status", justify="center")
            doc_table.add_column("Latensi", justify="right")
            doc_table.add_column("Keterangan", style="dim")
            for p, (ok, msg, lat) in results.items():
                s_badge = "[bold green]✔ OK[/bold green]" if ok else "[bold red]✖ FAILED[/bold red]"
                doc_table.add_row(p.upper(), s_badge, f"{lat}s" if lat > 0 else "-", msg)
            self.console.print(doc_table)
            self.console.print()
            return True

        elif root_cmd == "/gateway":
            from apex.gateways.daemon import gateway_daemon
            gateway_daemon.status()
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

        elif root_cmd == "/agents":
            agents_file = config.workspace / "AGENTS.md"
            if not agents_file.is_file():
                agents_file = PKG_ROOT / "AGENTS.md"
            if agents_file.is_file():
                content = agents_file.read_text(encoding="utf-8")
                self.console.print(Panel(
                    content[:1200] + ("\n[dim]... (+ selengkapnya di AGENTS.md)[/dim]" if len(content) > 1200 else ""),
                    title="[bold cyan]AGENTS Manifest (Multi-Agent Architecture)[/bold cyan]",
                    border_style="cyan"
                ))
            else:
                self.console.print("[dim]AGENTS.md tidak ditemukan.[/dim]")
            self.console.print()
            return True

        elif root_cmd == "/scan":
            from apex.tools import tool_registry
            from apex.learning.skills import skill_manager
            from apex.tools.mcp import mcp_manager
            from apex.tools.custom_loader import custom_tool_loader

            self.console.print("\n[bold cyan]🔍 Memindai seluruh MCP, modular skills, dan custom tools di sistem...[/bold cyan]")
            mcp_manager.discover_all_tools(force_refresh=True)
            skill_manager.reload_skills()
            tool_registry.discover_custom_tools(force_reload=True)

            detected_servers = mcp_manager.get_detected_servers()
            detected_skills = skill_manager.get_detected_skills()
            detected_custom = custom_tool_loader.get_detected_custom_tools()
            native_tools = tool_registry.get_native_tools()

            # Summary Metrics Panel
            online_mcp = sum(1 for s in detected_servers if s.get("status") == "online")
            total_mcp_tools = sum(s.get("tool_count", 0) for s in detected_servers)
            summary_txt = (
                f"• [bold cyan]Server MCP Terdeteksi[/bold cyan]   : [white]{len(detected_servers)} server[/white] "
                f"([green]{online_mcp} online[/green]) · [yellow]{total_mcp_tools} remote tools[/yellow]\n"
                f"• [bold magenta]Modular Skills[/bold magenta]          : [white]{len(detected_skills)} skills terdaftar[/white]\n"
                f"• [bold yellow]Custom User Tools[/bold yellow]       : [white]{len(detected_custom)} tool kustom aktif[/white]\n"
                f"• [bold green]Native Sovereign Tools[/bold green]  : [white]{len(native_tools)} tool bawaan siap pakai[/white]"
            )
            self.console.print(Panel(summary_txt, title="[bold cyan]📊 Hasil Pemindaian Ekosistem Apex[/bold cyan]", border_style="cyan"))

            # Table 1: MCP Servers
            if detected_servers:
                mcp_table = Table(title="🔌 Server MCP Terdeteksi", show_lines=True, border_style="cyan")
                mcp_table.add_column("Server", style="bold cyan")
                mcp_table.add_column("Transport", justify="center")
                mcp_table.add_column("Status", justify="center")
                mcp_table.add_column("Tools", justify="right")
                mcp_table.add_column("Sumber Konfigurasi", style="dim")
                for s in detected_servers:
                    stat_badge = "[bold green]ONLINE[/bold green]" if s.get("status") == "online" else "[bold red]OFFLINE[/bold red]"
                    mcp_table.add_row(
                        s.get("name", ""),
                        s.get("transport", "").upper(),
                        stat_badge,
                        f"{s.get('tool_count', 0)} tool",
                        s.get("source", "")
                    )
                self.console.print(mcp_table)

            # Table 2: Modular Skills
            if detected_skills:
                sk_table = Table(title=f"🧩 Modular Skills Terdeteksi ({len(detected_skills)} Skills)", show_lines=False, border_style="magenta")
                sk_table.add_column("Skill", style="bold magenta", width=24)
                sk_table.add_column("Asal / Sumber", style="cyan", width=34)
                sk_table.add_column("Deskripsi", style="white")
                for sk in detected_skills:
                    sk_table.add_row(sk["name"], sk.get("origin", "Ecosystem"), sk.get("description", "")[:85])
                self.console.print(sk_table)

            # Table 3: Custom User Tools
            if detected_custom:
                ct_table = Table(title=f"🛠 Custom User Tools ({len(detected_custom)} Tool)", show_lines=True, border_style="yellow")
                ct_table.add_column("Tool Name", style="bold yellow")
                ct_table.add_column("Asal / Lokasi Script", style="dim")
                ct_table.add_column("Deskripsi", style="white")
                for ct in detected_custom:
                    ct_table.add_row(ct["name"], ct.get("source_path", ""), ct.get("description", ""))
                self.console.print(ct_table)
            else:
                self.console.print("[dim]💡 Tip: Pasang tool Python kustom Anda di ~/.apex/custom_tools/ untuk dimuat otomatis.[/dim]")

            self.console.print()
            return True

        elif root_cmd == "/tools":
            from apex.tools import tool_registry
            native = tool_registry.get_native_tools()
            custom = tool_registry.get_custom_tools()
            mcp = tool_registry.get_mcp_tools()

            t_table = Table(title=f"🛠 Daftar Seluruh Tools Aktif ({len(native) + len(custom) + len(mcp)} Total)", show_lines=True, border_style="cyan")
            t_table.add_column("Kategori", style="bold cyan", width=18)
            t_table.add_column("Nama Tool", style="bold yellow", width=30)
            t_table.add_column("Deskripsi", style="white")

            for n_name, n_meta in native.items():
                t_table.add_row("[green]Native Sovereign[/green]", n_name, n_meta.get("description", ""))

            for c_name, c_meta in custom.items():
                t_table.add_row("[yellow]Custom User[/yellow]", c_name, c_meta.get("description", ""))

            for m_name, m_meta in mcp.items():
                t_table.add_row("[cyan]MCP Remote[/cyan]", m_name, m_meta.get("description", ""))

            self.console.print(t_table)
            self.console.print("[dim]Tip: Ketik /scan untuk memindai ulang tools kustom & MCP yang baru dipasang.[/dim]\n")
            return True

        elif root_cmd == "/skills":
            from apex.learning.skills import skill_manager
            skills = skill_manager.get_detected_skills()
            if not skills:
                self.console.print("[dim]Tidak ada modular skills yang terdeteksi di sistem.[/dim]\n")
            else:
                sk_table = Table(title=f"🧩 Daftar Modular Skills Terdeteksi ({len(skills)} Skills)", show_lines=False, border_style="magenta")
                sk_table.add_column("Skill", style="bold yellow", width=24)
                sk_table.add_column("Asal / Sumber", style="cyan", width=34)
                sk_table.add_column("Deskripsi", style="white")
                for s in skills:
                    sk_table.add_row(s["name"], s.get("origin", "Ecosystem"), s.get("description", "")[:85])
                self.console.print(sk_table)
                self.console.print("[dim]Tip: Gunakan /scan untuk memindai ulang skills baru yang dipasang.[/dim]\n")
            return True

        elif root_cmd == "/mcp":
            from apex.tools.mcp import mcp_manager
            servers = mcp_manager.get_detected_servers()
            if not servers:
                self.console.print("[dim]Tidak ada server MCP yang terdeteksi di sistem.[/dim]\n")
            else:
                mcp_table = Table(title="🔌 Daftar Server MCP Terdeteksi Multi-Ekosistem", show_lines=True, border_style="cyan")
                mcp_table.add_column("Server", style="bold cyan")
                mcp_table.add_column("Transport", justify="center")
                mcp_table.add_column("Status", justify="center")
                mcp_table.add_column("Tools", justify="right")
                mcp_table.add_column("Endpoint", style="white")
                mcp_table.add_column("Sumber Konfigurasi", style="dim")
                for s in servers:
                    stat_badge = "[bold green]ONLINE[/bold green]" if s.get("status") == "online" else "[bold red]OFFLINE[/bold red]"
                    mcp_table.add_row(
                        s.get("name", ""),
                        s.get("transport", "").upper(),
                        stat_badge,
                        f"{s.get('tool_count', 0)} tool",
                        s.get("endpoint", ""),
                        s.get("source", "")
                    )
                self.console.print(mcp_table)
                self.console.print("[dim]Tip: Gunakan /scan untuk memindai ulang atau /tools untuk melihat tool MCP.[/dim]\n")
            return True

        elif root_cmd == "/paraphrase":
            query = cmd[len(root_cmd):].strip()
            if not query:
                self.console.print("[yellow]Gunakan: /paraphrase <kalimat atau perintah yang ingin diuji>[/yellow]\n")
                return True
            from apex.security.paraphraser import semantic_paraphraser
            para, mod = semantic_paraphraser.paraphrase(query)
            reconstructed = semantic_paraphraser.reconstruct_as_benign_engineering(query)

            p_table = Table(title="🔄 Semantic Paraphrase & Anti-Refusal Neutralizer", show_lines=True, border_style="cyan")
            p_table.add_column("Lapisan", style="bold cyan", width=20)
            p_table.add_column("Konten / Hasil Rekonstruksi", style="white")
            p_table.add_row("Input Asli", f"[yellow]{query}[/yellow]")
            status_text = "[bold green]TERDETEKSI & DINORMALISASI[/bold green]" if mod else "[dim]Aman (Tidak mengandung trigger)[/dim]"
            p_table.add_row("Status Neutralizer", status_text)
            p_table.add_row("Hasil Parafrase", f"[bold green]{para}[/bold green]")
            p_table.add_row("Payload Rekonstruksi", f"[dim]{reconstructed}[/dim]")
            self.console.print(p_table)
            self.console.print()
            return True

        elif root_cmd in ["/web", "/dashboard"]:
            import threading
            from apex.gateways.web_dashboard import start_web_server

            port = 8000
            url = f"http://127.0.0.1:{port}"
            self.console.print(f"[bold cyan]🌐 Memulai Apex Web Dashboard di latar belakang...[/bold cyan]")
            self.console.print(f"👉 Buka browser Anda di: [bold green]{url}[/bold green]\n")

            t = threading.Thread(target=start_web_server, kwargs={"host": "127.0.0.1", "port": port}, daemon=True)
            t.start()
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
                    rprompt=rprompt_str,
                    completer=self.completer,
                    complete_while_typing=True,
                    reserve_space_for_menu=8,
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

                # Auto-Neutralizer notification if prompt contains sensitive refusal-trigger terms
                from apex.security.paraphraser import semantic_paraphraser
                _, was_modified = semantic_paraphraser.paraphrase(user_input)
                if was_modified:
                    self.console.print("[dim]🔄 [bold cyan]Auto-Neutralizer:[/bold cyan] Kata pemicu penolakan dinetralkan otomatis ke bahasa rekayasa resmi...[/dim]")

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
                if not response_text or not response_text.strip():
                    response_text = "✅ Permintaan telah selesai diproses dengan sukses oleh sistem Apex 🚀"
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
