"""Unit tests for Universal Modular Plugin System."""
import pytest
from apex.plugins.manager import PluginManager, manage_plugins


def test_plugin_manager_lifecycle(tmp_path):
    mgr = PluginManager(plugins_dir=tmp_path)

    # 1. Create plugin
    res = mgr.create_plugin("test-analyzer", description="Test code analyzer")
    assert res["success"] is True
    assert (tmp_path / "test-analyzer" / "plugin.json").exists()
    assert (tmp_path / "test-analyzer" / "main.py").exists()

    # 2. List plugins
    plugins = mgr.list_plugins()
    assert len(plugins) == 1
    assert plugins[0]["name"] == "test-analyzer"
    assert plugins[0]["enabled"] is True

    # 3. Toggle disable
    tog_res = mgr.toggle_plugin("test-analyzer", False)
    assert tog_res["success"] is True
    assert tog_res["enabled"] is False

    # 4. Remove plugin
    del_res = mgr.remove_plugin("test-analyzer")
    assert del_res["success"] is True
    assert not (tmp_path / "test-analyzer").exists()


def test_manage_plugins_tool(tmp_path, monkeypatch):
    from apex.plugins import manager
    monkeypatch.setattr(manager, "PLUGINS_DIR", tmp_path)
    monkeypatch.setattr(manager.plugin_manager, "plugins_dir", tmp_path)

    # Tool wrapper list empty
    out_empty = manage_plugins("list")
    assert "Belum ada plugin" in out_empty

    # Tool wrapper create
    out_create = manage_plugins("create", name="dummy-tool", description="A dummy tool")
    assert "Plugin Berhasil Dibuat" in out_create

    # Tool wrapper list
    out_list = manage_plugins("list")
    assert "dummy-tool" in out_list
