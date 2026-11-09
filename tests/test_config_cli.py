"""Unit tests for Configuration CLI Handlers."""
import json
import pytest
from apex.gateways.config_cli import (
    mask_key, show_config_dashboard, get_config_value, set_config_value,
    export_config, import_config
)
from apex.config import config


def test_mask_key():
    assert mask_key("") == "[dim]none[/dim]"
    assert mask_key("none") == "[dim]none[/dim]"
    assert "••••••••" in mask_key("sk-1234567890abcdef")


def test_show_config_dashboard(capsys):
    show_config_dashboard()
    # verify no exception raised


def test_get_and_set_config_value(capsys):
    orig = config.default_model
    set_config_value("default_model", "test-model-xyz")
    assert config.default_model == "test-model-xyz"

    get_config_value("default_model")
    out = capsys.readouterr().out
    assert "test-model-xyz" in out

    # Restore
    set_config_value("default_model", orig)
    assert config.default_model == orig


def test_export_and_import_config(tmp_path):
    export_file = tmp_path / "exported_apex.json"
    export_config(str(export_file))
    assert export_file.exists()

    with open(export_file, "r") as f:
        data = json.load(f)
    assert "default_model" in data

    import_config(str(export_file))
    assert config.default_model == data["default_model"]


def test_profile_cli(capsys):
    from apex.gateways.config_cli import profile_cli

    # Save
    profile_cli("save", "cli_test_prof")
    out = capsys.readouterr().out
    assert "cli_test_prof" in out

    # List
    profile_cli("list")
    out = capsys.readouterr().out
    assert "cli_test_prof" in out

    # Use
    profile_cli("use", "cli_test_prof")
    out = capsys.readouterr().out
    assert "Berhasil beralih" in out

    # Switch back and remove
    profile_cli("use", "default")
    profile_cli("rm", "cli_test_prof")
    out = capsys.readouterr().out
    assert "berhasil dihapus" in out


def test_sync_env_and_validate_cli(capsys):
    from apex.gateways.config_cli import sync_env_cli, validate_cli
    sync_env_cli()
    out = capsys.readouterr().out
    assert "Environment" in out

    validate_cli()
    out = capsys.readouterr().out
    assert "HEALTH CHECK" in out


def test_setup_health_and_quick(tmp_path):
    from apex.gateways.setup_wizard import check_setup_health, repair_setup, quick_setup

    assert check_setup_health() is True
    actions = repair_setup()
    assert len(actions) > 0

    ws = tmp_path / "quick_ws"
    ws.mkdir()
    ok = quick_setup(
        provider="tokenharbor",
        model="mimo-v2.6-flash:free",
        workspace=str(ws)
    )
    assert ok is True
    assert config.active_provider == "tokenharbor"

