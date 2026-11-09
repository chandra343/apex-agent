"""Unit tests for System Configuration Manager Tool."""
import pytest
from apex.tools.config_ops import manage_system_config
from apex.config import config


def test_manage_config_list():
    res = manage_system_config("list")
    assert "Ikhtisar Konfigurasi Sistem Apex" in res
    assert "Model Default" in res


def test_manage_config_get():
    res = manage_system_config("get", key_path="default_model")
    assert "Konfigurasi" in res
    assert config.default_model in res


def test_manage_config_set():
    orig_val = config.get("router.rtk_compression", True)

    set_res = manage_system_config("set", key_path="router.rtk_compression", value="false")
    assert "Berhasil Diperbarui" in set_res
    assert config.get("router.rtk_compression") is False

    # Restore
    manage_system_config("set", key_path="router.rtk_compression", value=str(orig_val).lower())
    assert config.get("router.rtk_compression") == orig_val


def test_manage_config_invalid():
    res = manage_system_config("unknown_action")
    assert "tidak dikenali" in res
