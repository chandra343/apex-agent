"""Dynamic Custom User Tool Discovery & Loader (Python Script Plugin System)."""
from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from apex.config import config, CUSTOM_TOOLS_DIR, DATA_DIR


class CustomToolLoader:
    """Discovers and dynamically imports user-authored Python tools."""

    def __init__(self) -> None:
        self._custom_tools: Dict[str, Dict[str, Any]] = {}
        self._load_errors: Dict[str, str] = {}

    def get_search_directories(self) -> List[Tuple[Path, str]]:
        """Return candidate directories for user-authored custom tools."""
        candidates: List[Tuple[Path, str]] = [
            (CUSTOM_TOOLS_DIR, "Apex User Tools (~/.apex/custom_tools)"),
            (DATA_DIR / "tools", "Apex Global Tools (~/.apex/tools)"),
            (Path.cwd() / "custom_tools", "Workspace (./custom_tools)"),
            (Path.cwd() / "tools", "Workspace (./tools)"),
        ]

        ws = getattr(config, "workspace", None)
        if ws and Path(ws) != Path.cwd():
            candidates.append((Path(ws) / "custom_tools", f"Workspace ({ws}/custom_tools)"))
            candidates.append((Path(ws) / "tools", f"Workspace ({ws}/tools)"))

        # User custom tool directories from config
        custom_dirs = config.get("paths.tools_dirs", [])
        if isinstance(custom_dirs, list):
            for cd in custom_dirs:
                candidates.append((Path(cd), f"Custom Tools Dir ({cd})"))

        return candidates

    def discover_tools(self) -> Dict[str, Dict[str, Any]]:
        """Scan candidate directories, load valid python tool plugins, and return them."""
        discovered: Dict[str, Dict[str, Any]] = {}
        self._load_errors.clear()

        search_dirs = self.get_search_directories()
        seen_files: set[Path] = set()

        for t_dir, origin_label in search_dirs:
            if not t_dir.exists() or not t_dir.is_dir():
                continue

            for py_path in t_dir.glob("*.py"):
                if py_path.name.startswith(("_", ".")) or py_path.name.startswith("test_"):
                    continue
                if py_path.resolve() in seen_files:
                    continue
                seen_files.add(py_path.resolve())

                try:
                    loaded = self._load_tool_module(py_path, origin_label)
                    for t_name, t_meta in loaded.items():
                        discovered[t_name] = t_meta
                except Exception as e:
                    self._load_errors[str(py_path)] = str(e)

        self._custom_tools = discovered
        return discovered

    def _load_tool_module(self, py_path: Path, origin_label: str) -> Dict[str, Dict[str, Any]]:
        mod_name = f"apex_custom_tool_{py_path.stem}"
        spec = importlib.util.spec_from_file_location(mod_name, py_path)
        if not spec or not spec.loader:
            return {}

        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)

        tools_found: Dict[str, Dict[str, Any]] = {}

        # 1. Multi-tool list in module: TOOLS = [...]
        if hasattr(mod, "TOOLS") and isinstance(mod.TOOLS, list):
            for item in mod.TOOLS:
                if isinstance(item, dict) and "name" in item and "handler" in item:
                    tools_found[item["name"]] = self._normalize_meta(item, py_path, origin_label)

        # 2. Single TOOL_DEFINITION dict in module
        elif hasattr(mod, "TOOL_DEFINITION") and isinstance(mod.TOOL_DEFINITION, dict):
            td = mod.TOOL_DEFINITION
            if "name" in td and "handler" in td:
                tools_found[td["name"]] = self._normalize_meta(td, py_path, origin_label)

        # 3. Individual variables: TOOL_NAME, TOOL_DESCRIPTION, TOOL_PARAMETERS, execute/run
        else:
            handler = getattr(mod, "execute", None) or getattr(mod, "run", None) or getattr(mod, "main", None)
            if callable(handler):
                name = getattr(mod, "TOOL_NAME", py_path.stem)
                desc = getattr(mod, "TOOL_DESCRIPTION", "") or (mod.__doc__ or "Custom user tool").strip()
                params = getattr(mod, "TOOL_PARAMETERS", {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "Input parameter"}
                    }
                })
                is_safe = getattr(mod, "IS_SAFE", False)

                t_dict = {
                    "name": name,
                    "description": desc,
                    "parameters": params,
                    "handler": handler,
                    "is_safe": is_safe
                }
                tools_found[name] = self._normalize_meta(t_dict, py_path, origin_label)

        return tools_found

    def _normalize_meta(self, t_dict: Dict[str, Any], py_path: Path, origin_label: str) -> Dict[str, Any]:
        handler = t_dict["handler"]

        def wrapped_handler(args: Dict[str, Any]) -> Tuple[bool, str]:
            try:
                # Support handlers returning (bool, str) or str or dict
                res = handler(args)
                if isinstance(res, tuple) and len(res) == 2:
                    return bool(res[0]), str(res[1])
                elif isinstance(res, bool):
                    return res, ""
                else:
                    return True, str(res)
            except Exception as ex:
                return False, f"Custom tool execution error in {t_dict.get('name')}: {ex}"

        return {
            "name": t_dict["name"],
            "description": t_dict.get("description", "Custom user-installed tool"),
            "parameters": t_dict.get("parameters", {"type": "object", "properties": {}}),
            "handler": wrapped_handler,
            "is_safe": t_dict.get("is_safe", False),
            "is_custom": True,
            "source_path": str(py_path),
            "origin": origin_label
        }

    def get_detected_custom_tools(self) -> List[Dict[str, Any]]:
        """Return metadata list of loaded custom tools."""
        return list(self._custom_tools.values())

    def get_load_errors(self) -> Dict[str, str]:
        """Return mapping of script paths to syntax/import errors if any."""
        return dict(self._load_errors)


# Global custom tool loader
custom_tool_loader = CustomToolLoader()
