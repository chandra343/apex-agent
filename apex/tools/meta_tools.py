"""Autonomous Meta-Tooling & Self-Extensibility Engine.
Enables Project Apex to dynamically create, register, and hot-load:
1. Custom User Tools (Python scripts in ~/.apex/custom_tools/)
2. Modular Skills (SKILL.md packages in ~/.apex/skills/)
3. MCP Servers (stdio or HTTP transports registered in ~/.apex/apex.json)
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from apex.config import config, CUSTOM_TOOLS_DIR, DATA_DIR, SKILLS_DIR


def create_custom_tool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    python_code: str,
    is_safe: bool = False
) -> Tuple[bool, str]:
    """Dynamically forge a new Python custom tool, write to ~/.apex/custom_tools/, and hot-load it."""
    # 1. Sanitize tool name
    clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip().lower()).strip("_")
    if not clean_name:
        return False, "Tool name cannot be empty and must be alphanumeric."

    # 2. Syntax validation
    try:
        ast.parse(python_code)
    except SyntaxError as se:
        return False, f"Python syntax validation failed: {se}"

    # 3. Assemble standard Apex tool script if boilerplate is missing
    CUSTOM_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    target_file = CUSTOM_TOOLS_DIR / f"{clean_name}.py"

    has_tool_name = "TOOL_NAME" in python_code
    has_params = "TOOL_PARAMETERS" in python_code
    has_execute = "def execute(" in python_code or "def run(" in python_code or "def main(" in python_code

    if not (has_tool_name and has_params and has_execute):
        # Auto-wrap as complete standalone tool module
        param_json = json.dumps(parameters or {"type": "object", "properties": {}}, indent=4)
        wrapped_code = (
            f'"""Custom autonomous tool: {clean_name}."""\n'
            f'TOOL_NAME = "{clean_name}"\n'
            f'TOOL_DESCRIPTION = {json.dumps(description or "Custom dynamically created tool")}\n'
            f'TOOL_PARAMETERS = {param_json}\n'
            f'IS_SAFE = {bool(is_safe)}\n\n'
            f'{python_code}\n'
        )
        if not has_execute:
            wrapped_code += (
                f'\ndef execute(args: dict):\n'
                f'    """Default handler wrapping tool execution."""\n'
                f'    return True, f"Executed {clean_name} with args: {{args}}"\n'
            )
        final_code = wrapped_code
    else:
        final_code = python_code

    try:
        target_file.write_text(final_code, encoding="utf-8")
    except Exception as ex:
        return False, f"Failed to write tool file: {ex}"

    # 4. Hot-load into ToolRegistry immediately
    try:
        from apex.tools import tool_registry
        tool_registry.discover_custom_tools(force_reload=True)
        is_loaded = clean_name in tool_registry.get_custom_tools() or f"custom__{clean_name}" in tool_registry.get_custom_tools()
        if is_loaded:
            return True, (
                f"✔ Custom tool '{clean_name}' created at {target_file} and hot-loaded into active registry!\n"
                f"Tool '{clean_name}' is now immediately callable by Apex."
            )
        return True, f"✔ Tool written to {target_file}. (Reload triggered)."
    except Exception as ex:
        return True, f"✔ Tool saved at {target_file}, but reload encountered warning: {ex}"


def create_skill(
    name: str,
    description: str,
    instructions: str,
    reference_files: Optional[Dict[str, str]] = None
) -> Tuple[bool, str]:
    """Dynamically forge a new modular skill package in ~/.apex/skills/<name>/SKILL.md."""
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower()).strip("-")
    if not clean_name:
        return False, "Skill name cannot be empty."

    target_dir = SKILLS_DIR / clean_name
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "SKILL.md"

    # Standard YAML frontmatter
    skill_content = (
        f"---\n"
        f"name: {clean_name}\n"
        f"description: {description.strip()}\n"
        f"---\n\n"
        f"{instructions.strip()}\n"
    )

    try:
        target_file.write_text(skill_content, encoding="utf-8")

        # Write any auxiliary reference files or scripts if provided
        if reference_files and isinstance(reference_files, dict):
            for rel_path, file_content in reference_files.items():
                ref_dest = target_dir / rel_path
                ref_dest.parent.mkdir(parents=True, exist_ok=True)
                ref_dest.write_text(file_content, encoding="utf-8")

        # Reload skills in SkillManager immediately
        from apex.learning.skills import skill_manager
        skill_manager.reload_skills()

        return True, (
            f"✔ Modular skill '{clean_name}' successfully created at {target_file}!\n"
            f"Skill is now active and indexed across all available skills in Apex."
        )
    except Exception as ex:
        return False, f"Failed to create skill package: {ex}"


def create_mcp_server(
    name: str,
    transport: str = "stdio",
    command: str = "",
    args: Optional[List[str]] = None,
    url: str = "",
    headers: Optional[Dict[str, str]] = None,
    env: Optional[Dict[str, str]] = None,
    python_server_code: str = ""
) -> Tuple[bool, str]:
    """Dynamically register or scaffold a new Model Context Protocol (MCP) server in ~/.apex/apex.json."""
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip().lower()).strip("_")
    if not clean_name:
        return False, "MCP server name cannot be empty."

    server_entry: Dict[str, Any] = {}
    trans = transport.strip().lower()

    # 1. If python script code is provided for stdio server, save it to disk
    if python_server_code.strip():
        mcp_servers_dir = DATA_DIR / "mcp_servers"
        mcp_servers_dir.mkdir(parents=True, exist_ok=True)
        script_file = mcp_servers_dir / f"{clean_name}_server.py"

        try:
            ast.parse(python_server_code)
        except SyntaxError as se:
            return False, f"MCP server Python code syntax error: {se}"

        script_file.write_text(python_server_code, encoding="utf-8")
        server_entry["command"] = sys.executable or "python3"
        server_entry["args"] = [str(script_file)]
        if env:
            server_entry["env"] = env

    elif trans in ["stdio", "cmd", "cli"]:
        if not command:
            return False, "stdio transport requires a 'command' executable."
        server_entry["command"] = command
        server_entry["args"] = args or []
        if env:
            server_entry["env"] = env

    elif trans in ["http", "sse", "url"]:
        if not url:
            return False, "http transport requires a 'url' endpoint."
        server_entry["url"] = url
        if headers:
            server_entry["headers"] = headers
    else:
        return False, f"Unsupported transport '{transport}'. Use 'stdio' or 'http'."

    # 2. Persist in apex.json configuration
    current_servers = config.get("mcpServers", {})
    if not isinstance(current_servers, dict):
        current_servers = {}
    current_servers[clean_name] = server_entry
    config.set("mcpServers", current_servers, auto_save=True)

    # 3. Discover and register tools immediately
    try:
        from apex.tools.mcp import mcp_manager
        discovered = mcp_manager.discover_all_tools(force_refresh=True)
        server_tools = [k for k in discovered if k.startswith(f"mcp__{clean_name}__")]
        return True, (
            f"✔ MCP server '{clean_name}' successfully configured ({trans})!\n"
            f"Tools discovered ({len(server_tools)}): {', '.join(server_tools) if server_tools else 'None yet / server starting'}"
        )
    except Exception as ex:
        return True, f"✔ MCP server '{clean_name}' saved to configuration. Discovery warning: {ex}"
