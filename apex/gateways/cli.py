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
    subparsers.add_parser("setup", help="Run 6-stage interactive setup wizard")

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
    model_parser = subparsers.add_parser("model", help="View or switch active model")
    model_parser.add_argument("name", nargs="?", default=None, help="Model name to switch to")

    # Provider
    prov_parser = subparsers.add_parser("provider", help="Manage AI providers")
    prov_sub = prov_parser.add_subparsers(dest="action")
    prov_add = prov_sub.add_parser("add", help="Add or update a provider")
    prov_add.add_argument("name", help="Provider name (e.g. deepseek, groq)")
    prov_add.add_argument("key", help="API key")
    prov_add.add_argument("--url", default="", help="Custom base URL")
    prov_add.add_argument("--models", nargs="*", default=[], help="Model IDs list")
    prov_sub.add_parser("test-all", help="Ping and test all configured providers")

    # Stats
    subparsers.add_parser("stats", help="View token usage, RPM/TPM, and estimated costs")

    # ACP
    subparsers.add_parser("acp", help="Start Agent Client Protocol (ACP) server for IDEs")

    args = parser.parse_args()

    # 1. Handle One-Shot Print Mode (-p)
    if args.one_shot_prompt:
        res = default_agent.run(args.one_shot_prompt, session_id="cli_oneshot", channel="cli_print")
        print(res)
        return

    # 2. Handle Subcommands
    if args.command == "setup":
        run_setup()
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
        if args.name:
            new_m = model_switcher.switch_model(args.name)
            print(f"✔ Active model switched to: {new_m}")
        else:
            models = model_switcher.get_available_models()
            print("Available models:")
            for m in models:
                mark = " (active)" if m["id"] == config.default_model else ""
                print(f"  • {m['display']}{mark}")
        return

    if args.command == "provider":
        if args.action == "add":
            models = args.models or [args.name]
            base_url = args.url or f"https://api.{args.name}.com/v1"
            provider_manager.add_provider(args.name, args.key, base_url, models)
            print(f"✔ Provider '{args.name}' registered successfully.")
        elif args.action == "test-all":
            print("Testing all providers...")
            results = provider_manager.test_all()
            for p_name, (ok, msg, lat) in results.items():
                status = "✔ OK" if ok else "✖ FAILED"
                print(f"[{status}] {p_name.upper()} ({lat}s): {msg}")
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

    # 3. Default: Launch Interactive Pi-Style TUI
    start_tui(agent_runner=lambda prompt: default_agent.run(prompt, session_id="cli_interactive", channel="cli_tui"))


if __name__ == "__main__":
    main()
