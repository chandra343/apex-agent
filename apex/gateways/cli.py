"""Master CLI Entry Point Dispatcher for Project Apex."""
from __future__ import annotations

import argparse
import sys
from apex.agent import default_agent
from apex.config import config
from apex.gateways.acp import run_acp_server
from apex.gateways.cli_tui import start_tui
from apex.gateways.daemon import gateway_daemon
from apex.gateways.setup_wizard import run_setup
from apex.router.ledger import token_ledger
from apex.router.model_switcher import model_switcher
from apex.router.provider_manager import provider_manager


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="apex",
        description="Project Apex: Sovereign Hybrid AI Agent"
    )

    parser.add_argument(
        "-p", "--print",
        dest="one_shot_prompt",
        type=str,
        help="One-shot print mode: execute prompt and print result to stdout without TUI"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Setup
    setup_parser = subparsers.add_parser("setup", help="Run 6-stage interactive setup wizard, healthcheck, or quick setup")
    setup_parser.add_argument("--check", action="store_true", help="Check setup health and directory permissions")
    setup_parser.add_argument("--repair", action="store_true", help="Auto-repair missing directories and configs")
    setup_parser.add_argument("--quick", action="store_true", help="Fast headless non-interactive setup")
    setup_parser.add_argument("--provider", "-p", default="", help="Provider ID for quick setup (e.g. tokenharbor, ollama)")
    setup_parser.add_argument("--model", "-m", default="", help="Model name for quick setup")
    setup_parser.add_argument("--key", "-k", default="", help="API key for quick setup")
    setup_parser.add_argument("--workspace", "-w", default="", help="Workspace directory for quick setup")
    setup_parser.add_argument("--gateway", "-g", default="", help="Comma-separated gateways (e.g. cli,telegram)")

    # Config
    cfg_parser = subparsers.add_parser("config", help="View, update, test, export, or reset system configurations")
    cfg_sub = cfg_parser.add_subparsers(dest="action")
    cfg_sub.add_parser("show", help="Display full visual configuration dashboard")
    cfg_get = cfg_sub.add_parser("get", help="Get a single config value")
    cfg_get.add_argument("key", nargs="?", default="", help="Key path using dot notation (e.g. default_model)")
    cfg_set = cfg_sub.add_parser("set", help="Set a config value")
    cfg_set.add_argument("key", help="Key path using dot notation")
    cfg_set.add_argument("value", help="Value to assign (supports raw strings or JSON)")
    cfg_sub.add_parser("reset", help="Reset config to default with automatic backup")
    cfg_export = cfg_sub.add_parser("export", help="Export configuration to JSON file")
    cfg_export.add_argument("output", nargs="?", default="", help="Optional destination file path")
    cfg_import = cfg_sub.add_parser("import", help="Import configuration from JSON file")
    cfg_import.add_argument("file", help="Path to JSON file to import")
    cfg_prof = cfg_sub.add_parser("profile", help="Manage configuration profiles (environments)")
    cfg_prof.add_argument("subaction", nargs="?", default="list", choices=["list", "use", "save", "rm", "delete"], help="Profile operation")
    cfg_prof.add_argument("name", nargs="?", default="", help="Profile name")
    cfg_sub.add_parser("validate", help="Validate configuration and system directories")
    cfg_sync = cfg_sub.add_parser("sync-env", help="Synchronize credentials from environment variables and .env file")
    cfg_sync.add_argument("--env-file", default="", help="Optional path to .env file")

    # TUI
    subparsers.add_parser("tui", help="Launch interactive Pi-style terminal TUI")

    # Gateway
    gw_parser = subparsers.add_parser("gateway", help="Manage 24/7 background messaging gateway daemon")
    gw_sub = gw_parser.add_subparsers(dest="action")
    gw_start = gw_sub.add_parser("start", help="Start gateway daemon")
    gw_start.add_argument("--foreground", action="store_true", help="Run in foreground")
    gw_sub.add_parser("stop", help="Stop running gateway daemon")
    gw_sub.add_parser("status", help="Check gateway daemon status")

    # Model
    model_parser = subparsers.add_parser("model", help="View, switch, or add custom AI models")
    model_parser.add_argument("name", nargs="?", default=None, help="Model name to switch to, or 'add' / 'rm'")
    model_parser.add_argument("target_model", nargs="?", default="", help="Model name if using add/rm")
    model_parser.add_argument("--provider", "-p", default="", help="Target provider ID (e.g. ollama, openai, vllm)")

    # Provider
    prov_parser = subparsers.add_parser("provider", help="Manage AI providers (browse shelf, search, add, test, switch)")
    prov_sub = prov_parser.add_subparsers(dest="action")
    prov_sub.add_parser("list", help="List all configured AI providers and active status")
    prov_search = prov_sub.add_parser("search", help="Search providers and models by keyword (e.g. free, fast, sonnet)")
    prov_search.add_argument("query", help="Keyword or category to search")
    prov_add = prov_sub.add_parser("add", help="Add or configure an AI provider")
    prov_add.add_argument("name", help="Provider name or ID (e.g. deepseek, groq, vllm)")
    prov_add.add_argument("key", nargs="?", default="", help="API key (optional if in catalog/env)")
    prov_add.add_argument("--url", default="", help="Custom base URL endpoint")
    prov_add.add_argument("--models", nargs="*", default=[], help="Model IDs list")
    prov_add.add_argument("--test", action="store_true", help="Test connection immediately after adding")
    prov_add.add_argument("--use", action="store_true", help="Set as active provider immediately")
    prov_use = prov_sub.add_parser("use", help="Select active provider and default model to use")
    prov_use.add_argument("name", help="Provider name or ID")
    prov_use.add_argument("model", nargs="?", default="", help="Optional model name to activate")
    prov_test = prov_sub.add_parser("test", help="Test connection and latency of a provider")
    prov_test.add_argument("name", nargs="?", default="", help="Provider name to test (or omit for all)")
    prov_sub.add_parser("test-all", help="Ping and test all configured providers")
    prov_rm = prov_sub.add_parser("rm", aliases=["delete", "remove"], help="Remove a provider")
    prov_rm.add_argument("name", help="Provider name or ID")
    prov_sub.add_parser("scan", help="Auto-scan localhost for local AI engines (Ollama, LM Studio, vLLM)")
    prov_fetch = prov_sub.add_parser("fetch-models", help="Fetch live models from provider API endpoint")
    prov_fetch.add_argument("name", help="Provider name or ID")

    # Stats
    subparsers.add_parser("stats", help="View token usage, RPM/TPM, and estimated costs")

    # ACP
    subparsers.add_parser("acp", help="Start Agent Client Protocol (ACP) server for IDEs")

    # Web Dashboard
    web_parser = subparsers.add_parser("web", aliases=["dashboard"], help="Launch modern interactive Web UI & Dashboard")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
    web_parser.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on (default: 8000)")

    args = parser.parse_args()

    # 1. Handle One-Shot Print Mode (-p)
    if args.one_shot_prompt:
        import sys
        def on_tool_start(name: str, fn_args: dict):
            args_str = ", ".join(f"{k}={repr(v)}" for k, v in list(fn_args.items())[:2])
            sys.stderr.write(f"⚡ [Apex Tool]: Menjalankan `{name}` ({args_str})...\n")
            sys.stderr.flush()

        def on_tool_end(name: str, output: str, is_error: bool):
            icon = "❌" if is_error else "✅"
            sys.stderr.write(f"{icon} [Apex Tool]: `{name}` selesai.\n")
            sys.stderr.flush()

        res = default_agent.run(
            args.one_shot_prompt,
            session_id="cli_oneshot",
            channel="cli_print",
            on_tool_start=on_tool_start,
            on_tool_end=on_tool_end
        )
        print(res)
        return

    # 2. Handle Subcommands
    if args.command == "setup":
        from apex.gateways.setup_wizard import check_setup_health, repair_setup, quick_setup, run_setup
        if args.check:
            check_setup_health()
        elif args.repair:
            repair_setup()
        elif args.quick:
            quick_setup(
                provider=args.provider,
                model=args.model,
                api_key=args.key,
                workspace=args.workspace,
                gateway=args.gateway
            )
        else:
            run_setup()
        return

    if args.command == "config":
        from apex.gateways.config_cli import (
            show_config_dashboard, get_config_value, set_config_value,
            reset_config, export_config, import_config,
            profile_cli, sync_env_cli, validate_cli
        )
        if args.action == "get":
            get_config_value(args.key)
        elif args.action == "set":
            set_config_value(args.key, args.value)
        elif args.action == "reset":
            reset_config()
        elif args.action == "export":
            export_config(args.output or None)
        elif args.action == "import":
            import_config(args.file)
        elif args.action == "profile":
            profile_cli(args.subaction, args.name)
        elif args.action == "validate":
            validate_cli()
        elif args.action == "sync-env":
            sync_env_cli(args.env_file or None)
        else:
            show_config_dashboard()
        return

    if args.command == "gateway":
        if args.action == "start":
            gateway_daemon.start(foreground=getattr(args, "foreground", False))
        elif args.action == "stop":
            gateway_daemon.stop()
        elif args.action == "status":
            gateway_daemon.status()
        else:
            gw_parser.print_help()
        return

    if args.command == "model":
        cmd_action = (args.name or "").lower()

        if cmd_action == "add":
            m_name = args.target_model.strip()
            p_name = args.provider.strip().lower()

            if not m_name:
                from rich.prompt import Prompt
                from rich.console import Console
                c = Console()
                c.print("[bold cyan]➕ Tambah Model AI Kustom ke Project Apex[/bold cyan]")
                m_name = Prompt.ask("Masukkan nama model (contoh: my-finetuned-llama, qwen-custom, mistral-large-3)").strip()
                if not m_name:
                    print("✖ Nama model tidak boleh kosong.")
                    return

            if not p_name:
                from rich.prompt import Prompt
                from rich.console import Console
                c = Console()
                configured = list(config.get("providers", {}).keys())
                c.print(f"[dim]Provider yang aktif saat ini: {', '.join(configured[:8])}...[/dim]")
                p_name = Prompt.ask("Masukkan ID provider tujuan", default="ollama").strip().lower()

            ok, msg = provider_manager.add_model_to_provider(p_name, m_name)
            if ok:
                print(f"✔ {msg}")
                from rich.prompt import Confirm
                set_def = Confirm.ask(f"Jadikan '{m_name}' sebagai model default aktif sekarang?", default=True)
                if set_def:
                    model_switcher.switch_model(m_name)
                    print(f"✔ Model default aktif sekarang: {m_name}")
            else:
                print(f"✖ {msg}")
            return

        if cmd_action in ["rm", "remove", "delete"]:
            m_name = args.target_model.strip()
            p_name = args.provider.strip().lower()

            if not m_name:
                from rich.prompt import Prompt
                m_name = Prompt.ask("Masukkan nama model yang ingin dihapus").strip()
                if not m_name:
                    print("✖ Nama model tidak boleh kosong.")
                    return

            if not p_name:
                providers = config.get("providers", {})
                matching_p = [p for p, data in providers.items() if any(m.lower() == m_name.lower() for m in data.get("models", []))]
                if len(matching_p) == 1:
                    p_name = matching_p[0]
                elif len(matching_p) > 1:
                    from rich.prompt import Prompt
                    p_name = Prompt.ask(f"Model ditemukan di beberapa provider ({', '.join(matching_p)}). Hapus dari", choices=matching_p)
                else:
                    print(f"✖ Model '{m_name}' tidak ditemukan di provider manapun.")
                    return

            ok, msg = provider_manager.remove_model_from_provider(p_name, m_name)
            if ok:
                print(f"✔ {msg}")
            else:
                print(f"✖ {msg}")
            return

        if args.name:
            new_m = model_switcher.switch_model(args.name)
            print(f"✔ Active model switched to: {new_m}")
        else:
            models = model_switcher.get_available_models()
            print("Available models:")
            for m in models:
                mark = " (active)" if m["id"] == config.default_model else ""
                print(f"  • {m['display']}{mark}")
            print("\nTips:")
            print("  • Tambah model kustom: apex model add <nama-model> --provider <provider>")
            print("  • Ganti model aktif  : apex model <nama-model>")
        return

    if args.command == "provider":
        from rich.console import Console
        from rich.table import Table
        c = Console()

        if args.action == "list":
            summary = provider_manager.get_provider_shelf_summary()
            table = Table(title="🤖 Daftar Provider AI Terdaftar di Apex", show_lines=True, border_style="cyan")
            table.add_column("Provider", style="bold cyan")
            table.add_column("Status", justify="center")
            table.add_column("Kredensial", justify="center")
            table.add_column("Base URL", style="dim")
            table.add_column("Jumlah Model", justify="right")

            for item in summary:
                if not item.get("is_configured") and not item.get("has_key"):
                    continue
                is_act = item.get("is_active")
                badge = "[bold green]★ AKTIF[/bold green]" if is_act else "[green]Siap Digunakan[/green]"
                key_str = item.get("masked_key") or "[dim]none[/dim]"
                table.add_row(
                    f"{item.get('icon', '')} {item['id'].upper()}",
                    badge,
                    key_str,
                    item.get("url", "")[:35],
                    f"{item.get('model_count', 0)} model"
                )
            c.print(table)
            c.print(f"[dim]Provider aktif saat ini: [bold green]{config.active_provider.upper()}[/bold green] (Model: [yellow]{config.default_model}[/yellow])[/dim]\n")

        elif args.action == "search":
            q = getattr(args, "query", "")
            matches = provider_manager.search_providers(q)
            if not matches:
                c.print(f"[yellow]Tidak ada provider atau model yang cocok dengan '{q}'.[/yellow]\n")
                return
            table = Table(title=f"🔍 Hasil Pencarian Provider AI untuk '{q}'", show_lines=True, border_style="cyan")
            table.add_column("Provider", style="bold cyan")
            table.add_column("Alasan Cocok", style="white")
            table.add_column("Model Terpilih", style="dim")
            table.add_column("Status", justify="center")
            for m in matches:
                is_act = m.get("is_active")
                badge = "[bold green]★ AKTIF[/bold green]" if is_act else ("[green]Siap[/green]" if m.get("is_configured") else "[dim]Tersedia[/dim]")
                table.add_row(
                    f"{m.get('icon', '')} {m['name']} ({m['id']})",
                    ", ".join(m.get("reasons", [])),
                    ", ".join(m.get("models", [])[:3]),
                    badge
                )
            c.print(table)
            c.print("[dim]Gunakan 'apex provider use <id>' untuk mengaktifkan provider yang dipilih.[/dim]\n")

        elif args.action == "add":
            ok, msg, detail = provider_manager.add_provider_smart(
                args.name,
                api_key=args.key,
                base_url=args.url,
                models=args.models or None,
                auto_fetch=True,
                verify_now=getattr(args, "test", False)
            )
            if ok:
                c.print(f"[bold green]✔ {msg}[/bold green]")
                if getattr(args, "use", False):
                    first_m = detail.get("models", [config.default_model])[0]
                    provider_manager.set_active_provider(args.name, first_m)
                    c.print(f"[bold green]✔ Provider aktif sekarang diatur ke: {args.name.upper()} ({first_m})[/bold green]")
            else:
                c.print(f"[bold red]✖ {msg}[/bold red]")

        elif args.action == "use":
            ok, msg = provider_manager.set_active_provider(args.name, args.model)
            if ok:
                c.print(f"[bold green]✔ {msg}[/bold green]")
                c.print(f"[dim]Menguji konektivitas live ke {args.name.upper()}...[/dim]")
                t_ok, t_msg, t_lat = provider_manager.test_provider(args.name)
                if t_ok:
                    c.print(f"[bold green]🟢 Uji koneksi berhasil! Latensi: {t_lat}s ({t_msg})[/bold green]\n")
                else:
                    c.print(f"[bold yellow]⚠️ Peringatan respon: {t_msg}[/bold yellow]\n")
            else:
                c.print(f"[bold red]✖ {msg}[/bold red]\n")

        elif args.action in ("test", "test-all"):
            target_p = getattr(args, "name", "").strip().lower()
            if target_p:
                c.print(f"[dim]Menguji konektivitas provider {target_p.upper()}...[/dim]")
                t_ok, t_msg, t_lat = provider_manager.test_provider(target_p)
                status = "[bold green]✔ OK[/bold green]" if t_ok else "[bold red]✖ GAGAL[/bold red]"
                c.print(f"{status} {target_p.upper()} ({t_lat}s): {t_msg}\n")
            else:
                c.print("[cyan]Menguji seluruh provider aktif & terkonfigurasi...[/cyan]")
                results = provider_manager.test_all()
                table = Table(title="📊 Hasil Uji Konektivitas Provider AI", show_lines=True, border_style="cyan")
                table.add_column("Provider", style="bold cyan")
                table.add_column("Status", justify="center")
                table.add_column("Latensi", justify="right")
                table.add_column("Pesan / Respon", style="dim")
                for p_name, (ok, msg, lat) in results.items():
                    status = "[bold green]✔ OK[/bold green]" if ok else "[bold red]✖ FAILED[/bold red]"
                    table.add_row(p_name.upper(), status, f"{lat}s", msg[:60])
                c.print(table)
                c.print()

        elif args.action in ("rm", "delete", "remove"):
            if provider_manager.remove_provider(args.name):
                c.print(f"[bold green]✔ Provider '{args.name}' berhasil dihapus dari konfigurasi.[/bold green]\n")
            else:
                c.print(f"[red]✖ Provider '{args.name}' tidak ditemukan.[/red]\n")

        elif args.action == "scan":
            c.print("[cyan]Memindai engine AI lokal di host (Ollama, LM Studio, vLLM, llama.cpp)...[/cyan]")
            scan_res = provider_manager.scan_and_register_local_engines()
            reg = scan_res.get("registered", [])
            if reg:
                c.print(f"[bold green]✔ Berhasil mendeteksi & mendaftarkan {len(reg)} engine AI lokal:[/bold green]")
                for item in reg:
                    c.print(f"  • [bold cyan]{item['name']}[/bold cyan] di [dim]{item['url']}[/dim] (Model: {', '.join(item['models'][:3])})")
            else:
                c.print("[yellow]Tidak ditemukan server AI lokal yang sedang aktif di port default.[/yellow]")
            c.print()

        elif args.action == "fetch-models":
            c.print(f"[cyan]Mengambil daftar model langsung dari API {args.name.upper()}...[/cyan]")
            f_ok, f_msg, models = provider_manager.fetch_live_models(args.name)
            if f_ok:
                c.print(f"[bold green]✔ {f_msg}[/bold green]")
                c.print(f"Model tersedia ({len(models)}): [yellow]{', '.join(models[:10])}[/yellow]\n")
            else:
                c.print(f"[bold red]✖ {f_msg}[/bold red]\n")

        else:
            # Launch interactive Provider Shelf UI (9Router Pro style)
            from apex.gateways.setup_wizard import SetupWizard
            SetupWizard().run_provider_shelf(standalone=True)
        return

    if args.command == "stats":
        print(token_ledger.get_summary_text())
        return

    if args.command == "acp":
        run_acp_server()
        return

    if args.command in ("web", "dashboard"):
        from apex.gateways.web_dashboard import start_web_server
        start_web_server(host=args.host, port=args.port)
        return

    # 3. Default: Launch Interactive Pi-Style TUI
    start_tui()


if __name__ == "__main__":
    main()
