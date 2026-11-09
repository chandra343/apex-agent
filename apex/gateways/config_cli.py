"""Master Configuration Management CLI for Project Apex."""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from apex.config import config, CONFIG_FILE, DATA_DIR
from apex.router.provider_manager import provider_manager


console = Console()


def mask_key(key: str) -> str:
    """Mask sensitive API keys for safe terminal display."""
    if not key or key == "none":
        return "[dim]none[/dim]"
    if len(key) <= 8:
        return "[yellow]••••••••[/yellow]"
    return f"[cyan]{key[:4]}[/cyan][yellow]••••••••[/yellow][cyan]{key[-4:]}[/cyan]"


def show_config_dashboard() -> None:
    """Render a comprehensive visual dashboard of all active Apex configurations."""
    cfg = config.raw

    # 1. Main System Overview Panel
    active_m = config.default_model
    active_p = config.active_provider
    active_b = config.active_backend
    ws = str(config.workspace)
    rtk = "Aktif (Kompresi Otomatis)" if config.get("router.rtk_compression", True) else "Nonaktif"

    sys_text = (
        f"• [bold cyan]Model Default[/bold cyan]  : [bold green]{active_m}[/bold green] ([white]{active_p.upper()}[/white])\n"
        f"• [bold cyan]Backend Host[/bold cyan]   : [bold white]{active_b}[/bold white] (Kedaulatan Host Penuh)\n"
        f"• [bold cyan]Workspace Path[/bold cyan] : [dim]{ws}[/dim]\n"
        f"• [bold cyan]Token Saver[/bold cyan]    : [green]{rtk}[/green] · Threshold: [yellow]{config.get('router.rtk_threshold_bytes', 1024)} bytes[/yellow]\n"
        f"• [bold cyan]File Config[/bold cyan]    : [dim]{CONFIG_FILE}[/dim]"
    )
    console.print(Panel(sys_text, title="[bold cyan]⚙️ Konfigurasi Utama Sistem Project Apex[/bold cyan]", border_style="cyan"))

    # 2. Configured Providers Table
    providers = config.get("providers", {})
    p_table = Table(title="🤖 Status Provider AI & Kredensial", show_lines=True, border_style="cyan")
    p_table.add_column("Provider ID", style="bold cyan")
    p_table.add_column("Status Autentikasi", justify="center")
    p_table.add_column("API Key Masked", justify="center")
    p_table.add_column("Base URL", style="dim")
    p_table.add_column("Jumlah Model", justify="right")

    for p_id, p_data in providers.items():
        is_conf = provider_manager.is_provider_configured(p_id)
        if not is_conf and not p_data.get("api_key"):
            continue  # Only display configured or relevant providers
        status_badge = "[bold green]TERHUBUNG[/bold green]" if is_conf else "[yellow]DUMMY/BELUM AKTIF[/yellow]"
        m_count = len(p_data.get("models", []))
        key_disp = mask_key(p_data.get("api_key", ""))
        p_table.add_row(
            p_id.upper() + (" ★" if p_id == active_p else ""),
            status_badge,
            key_disp,
            p_data.get("base_url", "")[:35] or "[dim](default cloud)[/dim]",
            f"{m_count} model"
        )
    console.print(p_table)

    # 3. Fallback Tiers Table
    tiers = config.get("fallback_tiers", {})
    t_table = Table(title="🔄 Rantai Fallback Otomatis (Anti-Down / Anti-Timeout)", show_lines=False, border_style="magenta")
    t_table.add_column("Tingkat Fallback", style="bold magenta", width=25)
    t_table.add_column("Daftar Model AI Cadangan", style="white")

    t_table.add_row("Tier 1 (Langganan Utama)", ", ".join(f"`{m}`" for m in tiers.get("tier_1_subscription", [])))
    t_table.add_row("Tier 2 (Ekonomis Cepat)", ", ".join(f"`{m}`" for m in tiers.get("tier_2_cheap", [])))
    t_table.add_row("Tier 3 (Gratis / Lokal)", ", ".join(f"`{m}`" for m in tiers.get("tier_3_free", [])))
    console.print(t_table)

    # 4. Gateways & Security
    gw_enabled = config.get("gateways.enabled", [])
    console.print(f"\n[bold white]Gateway Aktif:[/bold white] [green]{', '.join(g.upper() for g in gw_enabled)}[/green] | [bold white]Pairing Code:[/bold white] [bold yellow]{config.get('security.pairing_code', 'APEX-2026')}[/bold yellow]")
    console.print("[dim]Gunakan: 'apex config set <key> <val>' untuk mengubah atau 'apex config --help'[/dim]\n")


def get_config_value(key_path: str) -> None:
    """Print value of a single config key path."""
    val = config.get(key_path)
    if val is None:
        console.print(f"[red]✖ Key '{key_path}' tidak ditemukan dalam konfigurasi.[/red]")
        return
    if isinstance(val, (dict, list)):
        console.print(json.dumps(val, indent=2))
    else:
        console.print(f"[bold cyan]{key_path}[/bold cyan] = [bold green]{val}[/bold green]")


def set_config_value(key_path: str, raw_value: str) -> None:
    """Parse and set a configuration key path."""
    # Attempt JSON parsing for boolean, number, list, dict
    val: Any = raw_value
    try:
        val = json.loads(raw_value)
    except Exception:
        if raw_value.lower() == "true":
            val = True
        elif raw_value.lower() == "false":
            val = False

    config.set(key_path, val)
    console.print(f"[bold green]✔ Konfigurasi berhasil diperbarui dan disimpan:[/bold green]")
    console.print(f"  [cyan]{key_path}[/cyan] = [green]{val}[/green]\n")


def reset_config() -> None:
    """Reset apex.json to default with backup."""
    if CONFIG_FILE.exists():
        backup_file = CONFIG_FILE.with_suffix(f".bak.{int(time.time())}")
        shutil.copy2(CONFIG_FILE, backup_file)
        console.print(f"[dim]Backup dibuat di: {backup_file}[/dim]")
    from apex.config import DEFAULT_CONFIG
    config._config = json.loads(json.dumps(DEFAULT_CONFIG))
    config.save()
    console.print("[bold green]✔ Konfigurasi Apex berhasil di-reset ke nilai default bawaan pabrik![/bold green]\n")


def export_config(out_path: Optional[str] = None) -> None:
    """Export configuration to a specified JSON file."""
    dest = Path(out_path) if out_path else DATA_DIR / f"apex_config_export_{int(time.time())}.json"
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(config.raw, f, indent=2)
    console.print(f"[bold green]✔ Konfigurasi berhasil diekspor ke:[/bold green] [cyan]{dest.resolve()}[/cyan]\n")


def import_config(src_path: str) -> None:
    """Import and validate configuration from an external JSON file."""
    src = Path(src_path)
    if not src.exists():
        console.print(f"[red]✖ File sumber tidak ditemukan: {src_path}[/red]")
        return
    try:
        with open(src, "r", encoding="utf-8") as f:
            imported = json.load(f)
        if not isinstance(imported, dict):
            console.print("[red]✖ Format file konfigurasi tidak valid (harus objek JSON).[/red]")
            return
        config._config = imported
        config.save()
        console.print(f"[bold green]✔ Konfigurasi berhasil diimpor dari:[/bold green] [cyan]{src.resolve()}[/cyan]\n")
    except Exception as e:
        console.print(f"[red]✖ Gagal mengimpor konfigurasi: {e}[/red]")
