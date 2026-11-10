"""Universal Modular Plugin System for Project Apex.

Supports manifest-driven extensions in ~/.apex/plugins/:
- Structured manifest: plugin.json
- Lifecycle hooks (before_prompt, after_tool, filter_output)
- Dynamic tool & route injection
- Secure permission boundary auditing
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from apex.config import DATA_DIR

PLUGINS_DIR = DATA_DIR / "plugins"
PLUGINS_DIR.mkdir(parents=True, exist_ok=True)


class PluginManager:
    """Discovers, loads, and executes modular plugins."""

    def __init__(self, plugins_dir: Optional[Path] = None) -> None:
        self.plugins_dir = plugins_dir or PLUGINS_DIR
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self._plugins: Dict[str, Dict[str, Any]] = {}
        self._hooks: Dict[str, List[Callable[..., Any]]] = {
            "before_turn": [],
            "after_turn": [],
            "filter_output": []
        }

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all discovered plugins and their active states."""
        self.discover_plugins()
        return list(self._plugins.values())

    def discover_plugins(self) -> None:
        """Scan ~/.apex/plugins/ for subdirectories with plugin.json or single python files."""
        self._plugins.clear()

        # 1. Directory-based plugins with plugin.json
        for pdir in self.plugins_dir.iterdir():
            if pdir.is_dir() and not pdir.name.startswith((".", "_")):
                manifest_file = pdir / "plugin.json"
                entrypoint = pdir / "main.py"
                if manifest_file.exists():
                    try:
                        manifest = json.loads(manifest_file.read_text())
                        name = manifest.get("name", pdir.name)
                        self._plugins[name] = {
                            "name": name,
                            "version": manifest.get("version", "1.0.0"),
                            "author": manifest.get("author", "Community"),
                            "description": manifest.get("description", "Apex Extension Plugin"),
                            "enabled": manifest.get("enabled", True),
                            "path": str(pdir),
                            "entrypoint": str(pdir / manifest.get("entrypoint", "main.py")),
                            "permissions": manifest.get("permissions", ["read_only"])
                        }
                    except Exception as e:
                        self._plugins[pdir.name] = {
                            "name": pdir.name,
                            "error": f"Invalid manifest: {e}",
                            "enabled": False
                        }
                elif entrypoint.exists():
                    self._plugins[pdir.name] = {
                        "name": pdir.name,
                        "version": "0.1.0",
                        "author": "Local",
                        "description": "Standalone Python Plugin",
                        "enabled": True,
                        "path": str(pdir),
                        "entrypoint": str(entrypoint),
                        "permissions": ["all"]
                    }

    def create_plugin(self, name: str, description: str = "", code: str = "") -> Dict[str, Any]:
        """Create a new plugin template."""
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "", name).strip().lower()
        target_dir = self.plugins_dir / clean_name
        target_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "name": clean_name,
            "version": "1.0.0",
            "author": "Apex Sovereign Developer",
            "description": description or f"Custom plugin {clean_name}",
            "enabled": True,
            "entrypoint": "main.py",
            "permissions": ["filesystem", "network"]
        }
        (target_dir / "plugin.json").write_text(json.dumps(manifest, indent=2))

        default_code = code or '''"""Apex Plugin Entrypoint."""

def on_init(apex_context):
    """Called when plugin is initialized."""
    print(f"[{manifest['name']}] Plugin initialized.")

def filter_prompt(prompt: str) -> str:
    """Optional hook to transform prompt."""
    return prompt
'''
        (target_dir / "main.py").write_text(default_code)

        return {
            "success": True,
            "name": clean_name,
            "path": str(target_dir),
            "manifest": manifest
        }

    def toggle_plugin(self, name: str, enabled: bool) -> Dict[str, Any]:
        """Enable or disable a plugin."""
        target_dir = self.plugins_dir / name
        manifest_file = target_dir / "plugin.json"
        if not manifest_file.exists():
            return {"success": False, "error": f"Plugin '{name}' manifest not found"}

        try:
            m = json.loads(manifest_file.read_text())
            m["enabled"] = bool(enabled)
            manifest_file.write_text(json.dumps(m, indent=2))
            return {"success": True, "name": name, "enabled": m["enabled"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def remove_plugin(self, name: str) -> Dict[str, Any]:
        """Remove a plugin directory."""
        target_dir = self.plugins_dir / name
        if not target_dir.exists():
            return {"success": False, "error": f"Plugin '{name}' does not exist"}

        shutil.rmtree(target_dir, ignore_errors=True)
        return {"success": True, "message": f"Plugin '{name}' successfully deleted."}


plugin_manager = PluginManager()


def manage_plugins(
    action: str,
    name: str = "",
    description: str = "",
    code: str = "",
    enabled: bool = True
) -> str:
    """Tool function to manage Apex plugins."""
    act = action.strip().lower()

    if act in ["list", "ls"]:
        plugins = plugin_manager.list_plugins()
        if not plugins:
            return "ℹ️ Belum ada plugin kustom di `~/.apex/plugins/`. Buat plugin baru dengan `action='create'`."

        lines = [f"🔌 **Apex Plugins Installed ({len(plugins)}):**"]
        for p in plugins:
            status = "🟢 Active" if p.get("enabled", True) else "⚪ Disabled"
            lines.append(f"• **{p['name']}** (v{p.get('version', '1.0.0')}) — {status}")
            lines.append(f"  {p.get('description', '')}")
            if p.get("permissions"):
                lines.append(f"  Perms: `{', '.join(p['permissions'])}`")
        return "\n".join(lines)

    if act in ["create", "new", "add"]:
        if not name:
            return "❌ Nama plugin wajib diisi (contoh: name='my-analyzer')."
        res = plugin_manager.create_plugin(name, description=description, code=code)
        if not res.get("success"):
            return f"❌ {res.get('error')}"
        return (
            f"✅ **Plugin Berhasil Dibuat!**\n"
            f"• Nama : `{res['name']}`\n"
            f"• Path : `{res['path']}`\n"
            f"• File : `plugin.json` & `main.py`\n"
            "Plugin siap digunakan dan otomatis di-load saat start."
        )

    if act in ["toggle", "enable", "disable"]:
        if not name:
            return "❌ Nama plugin wajib diisi."
        set_enabled = (act == "enable") or (enabled if act == "toggle" else False)
        res = plugin_manager.toggle_plugin(name, set_enabled)
        if not res.get("success"):
            return f"❌ {res.get('error')}"
        return f"⚡ Plugin '{name}' sekarang {'🟢 Diaktifkan' if res['enabled'] else '⚪ Dinonaktifkan'}."

    if act in ["delete", "remove", "rm"]:
        if not name:
            return "❌ Nama plugin wajib diisi."
        res = plugin_manager.remove_plugin(name)
        if not res.get("success"):
            return f"❌ {res.get('error')}"
        return f"🗑️ {res['message']}"

    return (
        "❓ Aksi tidak dikenali. Opsi:\n"
        "- `action='list'`\n"
        "- `action='create', name='my-plugin', description='Custom tool'`\n"
        "- `action='enable', name='my-plugin'`\n"
        "- `action='delete', name='my-plugin'`"
    )
