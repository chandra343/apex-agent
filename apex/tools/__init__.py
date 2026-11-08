"""Unified Tool Registry, JSON Schema Generator & Execution Dispatcher."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from apex.config import config
from apex.router.rtk import rtk_compressor
from apex.tools.checkpoints import checkpoint_manager
from apex.tools.file_ops import (
    read_file, write_file, edit_file, search_files, grep_search, list_directory
)
from apex.tools.shell import run_shell, bg_tracker
from apex.tools.git_ops import git_status, git_diff, git_commit, git_log, git_branch
from apex.tools.transcribe import transcribe_audio
from apex.tools.network_routes import route_manager
from apex.tools.macros import macro_registry
from apex.tools.python_repl import python_repl
from apex.tools.reverse import inspect_binary, disassemble_binary
from apex.tools.system import get_system_info, get_listening_ports, list_system_processes
from apex.tools.lsp import lsp_client
from apex.tools.mcp import mcp_manager
from apex.tools.web import web_search, fetch_web_page
from apex.tools.custom_loader import custom_tool_loader
from apex.tools.meta_tools import create_custom_tool, create_skill, create_mcp_server
from apex.tools.doc_reader import read_any_file


class ToolRegistry:
    """Master tool registry and dispatcher."""

    def __init__(self) -> None:
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._custom_tool_keys: set[str] = set()
        self._register_native_tools()
        self.discover_custom_tools()

    def _register_native_tools(self) -> None:
        # File operations
        self.register("read_file", "Read contents of a file on the host filesystem (supports text, PDF, Word docx, Excel xlsx, image OCR, archives, SQLite, binary)", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative file path to read"},
                "offset_lines": {"type": "integer", "description": "Line offset to start reading", "default": 0},
                "limit_lines": {"type": "integer", "description": "Maximum lines to read", "default": 1000}
            },
            "required": ["path"]
        }, lambda args: read_file(args["path"], args.get("offset_lines", 0), args.get("limit_lines", 1000)), is_safe=True)

        self.register("read_document", "Universal omni-modal document & media parser. Reads PDF, Word (.docx), Excel (.xlsx), images with OCR, archives (.zip/.tar), SQLite databases (.db), and binary files", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to document, image, archive, database, or binary file"},
                "offset_lines": {"type": "integer", "description": "Line offset for pagination", "default": 0},
                "limit_lines": {"type": "integer", "description": "Maximum lines/rows to display", "default": 1000},
                "internal_path": {"type": "string", "description": "Optional inner file path when inspecting archives (.zip/.tar)"},
                "ocr": {"type": "boolean", "description": "Enable OCR text extraction on images (default: true)", "default": True}
            },
            "required": ["path"]
        }, lambda args: read_any_file(
            args["path"],
            args.get("offset_lines", 0),
            args.get("limit_lines", 1000),
            args.get("internal_path"),
            args.get("ocr", True)
        ), is_safe=True)

        self.register("write_file", "Write or overwrite a file on disk (auto-creates checkpoints)", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Full file content"},
                "overwrite": {"type": "boolean", "default": True}
            },
            "required": ["path", "content"]
        }, lambda args: write_file(args["path"], args["content"], args.get("overwrite", True)), is_safe=False)

        self.register("edit_file", "Targeted string replacement on an existing file (auto-creates checkpoints)", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit"},
                "target": {"type": "string", "description": "Exact text sequence to be replaced"},
                "replacement": {"type": "string", "description": "Replacement string"}
            },
            "required": ["path", "target", "replacement"]
        }, lambda args: edit_file(args["path"], args["target"], args["replacement"]), is_safe=False)

        self.register("undo_file", "Revert a file to its previous checkpoint snapshot", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path of the file to revert"}
            },
            "required": ["path"]
        }, lambda args: checkpoint_manager.undo_file(args["path"]), is_safe=False)

        self.register("search_files", "Search for files matching glob pattern", {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "default": "."},
                "pattern": {"type": "string", "default": "*"},
                "recursive": {"type": "boolean", "default": True}
            }
        }, lambda args: search_files(args.get("directory", "."), args.get("pattern", "*"), args.get("recursive", True)), is_safe=True)

        self.register("grep_search", "Search regex pattern across file contents", {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Regex or text string to search"},
                "directory": {"type": "string", "default": "."},
                "file_pattern": {"type": "string", "default": "*"}
            },
            "required": ["query"]
        }, lambda args: grep_search(args["query"], args.get("directory", "."), args.get("file_pattern", "*")), is_safe=True)

        self.register("list_directory", "List directory contents hierarchically", {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "default": "."},
                "depth": {"type": "integer", "default": 2}
            }
        }, lambda args: list_directory(args.get("directory", "."), args.get("depth", 2)), is_safe=True)

        # Shell execution
        self.register("run_shell", "Execute a terminal bash/cmd command on the host OS", {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Exact command line to execute"},
                "cwd": {"type": "string", "description": "Working directory"},
                "timeout": {"type": "integer", "default": 120},
                "background": {"type": "boolean", "default": False}
            },
            "required": ["command"]
        }, lambda args: self._run_shell_wrapper(args), is_safe=False)

        # Git operations
        self.register("git_status", "Check git working tree status", {
            "type": "object",
            "properties": {"cwd": {"type": "string", "default": "."}}
        }, lambda args: git_status(args.get("cwd")), is_safe=True)

        self.register("git_diff", "Show git changes", {
            "type": "object",
            "properties": {
                "staged": {"type": "boolean", "default": False},
                "cwd": {"type": "string", "default": "."}
            }
        }, lambda args: git_diff(args.get("staged", False), args.get("cwd")), is_safe=True)

        self.register("git_commit", "Stage and commit changes", {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "all_files": {"type": "boolean", "default": True},
                "cwd": {"type": "string", "default": "."}
            },
            "required": ["message"]
        }, lambda args: git_commit(args["message"], args.get("all_files", True), args.get("cwd")), is_safe=False)

        # Audio transcription
        self.register("transcribe_audio", "Transcribe audio file/voice note to text", {
            "type": "object",
            "properties": {
                "audio_path": {"type": "string"},
                "language": {"type": "string"}
            },
            "required": ["audio_path"]
        }, lambda args: transcribe_audio(args["audio_path"], args.get("language")), is_safe=True)

        # Python REPL
        self.register("python_repl", "Execute Python statements or expressions", {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python source code"}
            },
            "required": ["code"]
        }, lambda args: python_repl.execute(args["code"]), is_safe=False)

        # Binary Inspection
        self.register("inspect_binary", "Inspect binary ELF/PE headers and architecture", {
            "type": "object",
            "properties": {"file_path": {"type": "string"}},
            "required": ["file_path"]
        }, lambda args: inspect_binary(args["file_path"]), is_safe=True)

        self.register("disassemble_binary", "Disassemble binary symbol to machine code assembly", {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "symbol": {"type": "string", "default": "main"}
            },
            "required": ["file_path"]
        }, lambda args: disassemble_binary(args["file_path"], args.get("symbol", "main")), is_safe=True)

        # System inspection
        self.register("get_system_info", "Get host system specs, RAM, CPU, OS", {
            "type": "object", "properties": {}
        }, lambda args: get_system_info(), is_safe=True)

        self.register("get_listening_ports", "Inspect active network ports listening on host", {
            "type": "object", "properties": {}
        }, lambda args: get_listening_ports(), is_safe=True)

        # Web & Search
        self.register("web_search", "Search the web for up-to-date information", {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }, lambda args: web_search(args["query"], args.get("max_results", 5)), is_safe=True)

        self.register("fetch_web_page", "Fetch content of a web page URL", {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"]
        }, lambda args: fetch_web_page(args["url"]), is_safe=True)

        # Meta-Tooling: Autonomous Tool & Capability Synthesis
        self.register("create_custom_tool", "Dynamically create and hot-load a new Python tool in ~/.apex/custom_tools/ that Apex can immediately use", {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Alphanumeric tool name (e.g. check_ssl_expiry, port_scanner)"},
                "description": {"type": "string", "description": "Description of what this tool does"},
                "parameters": {"type": "object", "description": "JSON Schema object defining tool input properties"},
                "python_code": {"type": "string", "description": "Python source code containing def execute(args: dict) -> tuple[bool, str]"},
                "is_safe": {"type": "boolean", "description": "Whether this tool is safe for read-only parallel execution", "default": False}
            },
            "required": ["name", "description", "python_code"]
        }, lambda args: create_custom_tool(args["name"], args["description"], args.get("parameters", {}), args["python_code"], args.get("is_safe", False)), is_safe=False)

        self.register("create_skill", "Dynamically create and register a new modular skill package in ~/.apex/skills/<name>/SKILL.md", {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Skill name (e.g. cloudflare-waf-bypass, api-reverse-engineer)"},
                "description": {"type": "string", "description": "Short description of the specialized capability"},
                "instructions": {"type": "string", "description": "Full workflow instructions and steps in Markdown format"},
                "reference_files": {"type": "object", "description": "Optional mapping of relative file paths to file contents"}
            },
            "required": ["name", "description", "instructions"]
        }, lambda args: create_skill(args["name"], args["description"], args["instructions"], args.get("reference_files")), is_safe=False)

        self.register("create_mcp_server", "Dynamically configure and connect an MCP server (stdio command or HTTP endpoint) in ~/.apex/apex.json", {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Identifier name for the MCP server"},
                "transport": {"type": "string", "description": "Transport protocol: 'stdio' or 'http'", "enum": ["stdio", "http"]},
                "command": {"type": "string", "description": "Command executable for stdio transport"},
                "args": {"type": "array", "items": {"type": "string"}, "description": "CLI arguments for stdio command"},
                "url": {"type": "string", "description": "HTTP endpoint URL for http transport"},
                "headers": {"type": "object", "description": "HTTP headers such as API keys"},
                "env": {"type": "object", "description": "Environment variables for stdio transport"},
                "python_server_code": {"type": "string", "description": "Optional complete Python script for a standalone local stdio MCP server"}
            },
            "required": ["name", "transport"]
        }, lambda args: create_mcp_server(
            name=args["name"],
            transport=args.get("transport", "stdio"),
            command=args.get("command", ""),
            args=args.get("args"),
            url=args.get("url", ""),
            headers=args.get("headers"),
            env=args.get("env"),
            python_server_code=args.get("python_server_code", "")
        ), is_safe=False)

    def _run_shell_wrapper(self, args: Dict[str, Any]) -> Tuple[bool, str]:
        cmd = args["command"]
        cwd = args.get("cwd")
        timeout = args.get("timeout", 120)
        bg = args.get("background", False)
        code, out = run_shell(cmd, cwd=cwd, timeout=timeout, background=bg)
        return code == 0, out

    def discover_custom_tools(self, force_reload: bool = False) -> Dict[str, Dict[str, Any]]:
        """Scan directories for user-authored Python tools and dynamically register them."""
        # Clean previously registered custom tools
        for k in list(self._custom_tool_keys):
            self._tools.pop(k, None)
        self._custom_tool_keys.clear()

        loaded_custom = custom_tool_loader.discover_tools()
        for t_name, t_meta in loaded_custom.items():
            reg_name = t_name
            # If conflicts with native tools, prefix with custom__
            if reg_name in self._tools:
                reg_name = f"custom__{reg_name}"
            
            self._tools[reg_name] = {
                "name": reg_name,
                "description": t_meta.get("description", "Custom user-installed tool"),
                "parameters": t_meta.get("parameters", {"type": "object", "properties": {}}),
                "handler": t_meta["handler"],
                "is_safe": t_meta.get("is_safe", False),
                "is_custom": True,
                "source_path": t_meta.get("source_path", ""),
                "origin": t_meta.get("origin", "User Custom Tool")
            }
            self._custom_tool_keys.add(reg_name)

        return loaded_custom

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Tuple[bool, str]],
        is_safe: bool = True,
        is_custom: bool = False,
        origin: str = "Native Sovereign"
    ) -> None:
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
            "is_safe": is_safe,
            "is_custom": is_custom,
            "origin": origin
        }

    def get_native_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return registered native sovereign tools."""
        return {k: v for k, v in self._tools.items() if not v.get("is_custom")}

    def get_custom_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return dynamically loaded user custom tools."""
        return {k: v for k, v in self._tools.items() if v.get("is_custom")}

    def get_mcp_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return discovered remote MCP tools."""
        return mcp_manager.discover_all_tools()

    def is_safe_tool(self, name: str) -> bool:
        """Check if a tool is read-only (safe for parallel dispatch)."""
        if name in self._tools:
            return self._tools[name]["is_safe"]
        return False

    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return tool schemas in OpenAI/Anthropic format, including dynamic MCP tools."""
        defs: list[dict[str, Any]] = []
        for name, t in self._tools.items():
            defs.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": t["description"],
                    "parameters": t["parameters"]
                }
            })

        # Append dynamic MCP tools
        mcp_tools = mcp_manager.discover_all_tools()
        for scoped_name, m_data in mcp_tools.items():
            defs.append({
                "type": "function",
                "function": {
                    "name": scoped_name,
                    "description": m_data.get("description", ""),
                    "parameters": m_data.get("parameters", {"type": "object"})
                }
            })

        return defs

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """Dispatch tool call, applying RTK Token Saver on output."""
        # Check MCP tools
        if name.startswith("mcp__"):
            success, output = mcp_manager.call_tool(name, arguments)
        elif name in self._tools:
            try:
                success, output = self._tools[name]["handler"](arguments)
            except Exception as e:
                success, output = False, f"Tool execution exception in '{name}': {e}"
        else:
            return False, f"Unknown tool: '{name}'"

        # Apply RTK Token Saver compression if enabled
        if config.get("router.rtk_compression", True):
            compressed_output, orig_len, comp_len = rtk_compressor.compress(output, tool_name=name)
            return success, compressed_output

        return success, output


# Global tool registry
tool_registry = ToolRegistry()
