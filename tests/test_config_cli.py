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
