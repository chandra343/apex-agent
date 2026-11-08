"""Model Context Protocol (MCP) Client: stdio & HTTP/SSE transports (Zeline & Hermes Style)."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests
from apex.config import config

MCP_TOOL_PREFIX = "mcp__"
_RPC_TIMEOUT = 12
_DISCOVERY_DEADLINE = 5.0


class MCPClientManager:
    """Manages connections to external MCP servers and registers their tools with multi-path auto-discovery."""

    def __init__(self) -> None:
        self._servers: Dict[str, Any] = {}
        self._tools_cache: Dict[str, Dict[str, Any]] = {}
        self._detected_servers: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get_known_config_paths(self) -> List[Tuple[Path, str]]:
        """Return candidate file paths where MCP configs are commonly defined across ecosystems."""
        home = Path.home()
        candidates: List[Tuple[Path, str]] = [
            (home / ".apex" / "apex.json", "Apex Config (~/.apex/apex.json)"),
            (home / ".gemini" / "config" / "mcp_config.json", "Gemini Config (~/.gemini/config/mcp_config.json)"),
            (home / ".config" / "Claude" / "claude_desktop_config.json", "Claude Desktop (~/.config/Claude/claude_desktop_config.json)"),
            (home / ".cursor" / "mcp.json", "Cursor (~/.cursor/mcp.json)"),
            (home / ".vscode" / "mcp.json", "VSCode (~/.vscode/mcp.json)"),
            (home / ".config" / "instabox" / "mcp.json", "Instabox (~/.config/instabox/mcp.json)"),
            (Path.cwd() / ".mcp.json", "Workspace Root (.mcp.json)"),
            (Path.cwd() / "mcp.json", "Workspace Root (mcp.json)"),
        ]

        # Add configured workspace paths if different from cwd
        ws = getattr(config, "workspace", None)
        if ws and Path(ws) != Path.cwd():
            candidates.append((Path(ws) / ".mcp.json", f"Workspace ({ws}/.mcp.json)"))
            candidates.append((Path(ws) / "mcp.json", f"Workspace ({ws}/mcp.json)"))

        # Add custom path from config if set
        custom_p = config.get("paths.mcp_config")
        if custom_p:
            candidates.append((Path(custom_p), f"Custom Config ({custom_p})"))

        return candidates

    def collect_all_server_configs(self) -> Dict[str, Tuple[Dict[str, Any], str]]:
        """Collect server definitions across all ecosystem config paths."""
        discovered_servers: Dict[str, Tuple[Dict[str, Any], str]] = {}

        # 1. First check apex internal memory config
        direct_cfg = config.get("mcpServers", {})
        if isinstance(direct_cfg, dict):
            for s_name, s_val in direct_cfg.items():
                if isinstance(s_val, dict):
                    discovered_servers[s_name] = (s_val, "Apex Internal Config")

        # 2. Check candidate config files on disk
        for p, label in self.get_known_config_paths():
            if not p.is_file():
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Check for "mcpServers" or "servers" key
                s_map = data.get("mcpServers") or data.get("servers")
                if isinstance(s_map, dict):
                    for s_name, s_val in s_map.items():
                        if isinstance(s_val, dict) and s_name not in discovered_servers:
                            discovered_servers[s_name] = (s_val, label)
            except Exception:
                continue

        return discovered_servers

    def discover_all_tools(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """List and cache tools from all registered & discovered MCP servers."""
        with self._lock:
            if self._tools_cache and not force_refresh:
                return dict(self._tools_cache)

        all_servers = self.collect_all_server_configs()
        discovered: Dict[str, Dict[str, Any]] = {}
        detected_status: Dict[str, Dict[str, Any]] = {}

        for server_name, (s_data, origin_label) in all_servers.items():
            command = s_data.get("command")
            args = s_data.get("args", [])
            env = s_data.get("env", {})
            # Handle url, serverUrl, or endpoint
            url = s_data.get("url") or s_data.get("serverUrl") or s_data.get("endpoint")
            headers = s_data.get("headers") or {}

            server_tools: Dict[str, Dict[str, Any]] = {}
            transport = "unknown"

            if command:
                transport = "stdio"
                server_tools = self._discover_stdio_tools(server_name, command, args, env)
            elif url:
                transport = "http"
                server_tools = self._discover_http_tools(server_name, url, headers)

            discovered.update(server_tools)

            detected_status[server_name] = {
                "name": server_name,
                "transport": transport,
                "endpoint": command if command else (url or "-"),
                "source": origin_label,
                "tool_count": len(server_tools),
                "status": "online" if server_tools else "unreachable",
                "tools": list(server_tools.keys())
            }

        with self._lock:
            self._tools_cache = discovered
            self._detected_servers = detected_status

        return discovered

    def get_detected_servers(self) -> List[Dict[str, Any]]:
        """Return list of detected MCP servers and their active status."""
        if not self._detected_servers:
            self.discover_all_tools()
        return list(self._detected_servers.values())

    def _discover_stdio_tools(
        self,
        server_name: str,
        command: str | list[str],
        args: list[str],
        env: dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        if isinstance(command, str):
            full_cmd = shlex.split(command) + args
        else:
            full_cmd = list(command) + args

        proc_env = os.environ.copy()
        proc_env.update(env)

        tools: Dict[str, Dict[str, Any]] = {}
        try:
            # Safe process launch with isolated process group
            popen_kwargs: Dict[str, Any] = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.DEVNULL,
                "text": True,
                "env": proc_env
            }
            if os.name != "nt":
                popen_kwargs["start_new_session"] = True

            proc = subprocess.Popen(full_cmd, **popen_kwargs)

            # Initialize MCP session
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "apex-client", "version": "1.0.0"}
                }
            }
            proc.stdin.write(json.dumps(init_req) + "\n")
            proc.stdin.flush()
            init_resp = proc.stdout.readline()

            # List tools
            list_req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            proc.stdin.write(json.dumps(list_req) + "\n")
            proc.stdin.flush()
            list_resp = proc.stdout.readline()

            if list_resp:
                parsed = json.loads(list_resp)
                raw_tools = parsed.get("result", {}).get("tools", [])
                for t in raw_tools:
                    original_name = t.get("name")
                    scoped_name = f"{MCP_TOOL_PREFIX}{server_name}__{original_name}"
                    tools[scoped_name] = {
                        "server": server_name,
                        "original_name": original_name,
                        "description": t.get("description", ""),
                        "parameters": t.get("inputSchema", {}),
                        "transport": "stdio",
                        "command": full_cmd,
                        "env": proc_env
                    }

            proc.terminate()
            try:
                proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception:
            pass

        return tools

    def _discover_http_tools(
        self,
        server_name: str,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        tools: Dict[str, Dict[str, Any]] = {}
        post_headers = {"Content-Type": "application/json"}
        if headers:
            post_headers.update(headers)

        try:
            req_body = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            resp = requests.post(url, json=req_body, headers=post_headers, timeout=_DISCOVERY_DEADLINE)
            if resp.status_code == 200:
                raw_tools = resp.json().get("result", {}).get("tools", [])
                for t in raw_tools:
                    orig = t.get("name")
                    scoped = f"{MCP_TOOL_PREFIX}{server_name}__{orig}"
                    tools[scoped] = {
                        "server": server_name,
                        "original_name": orig,
                        "description": t.get("description", ""),
                        "parameters": t.get("inputSchema", {}),
                        "transport": "http",
                        "url": url,
                        "headers": post_headers
                    }
        except Exception:
            pass
        return tools

    def call_tool(self, scoped_tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute a tool on an external MCP server."""
        with self._lock:
            tool_meta = self._tools_cache.get(scoped_tool_name)

        if not tool_meta:
            # Re-discover on cache miss
            self.discover_all_tools(force_refresh=True)
            with self._lock:
                tool_meta = self._tools_cache.get(scoped_tool_name)

        if not tool_meta:
            return False, f"MCP tool '{scoped_tool_name}' not found in registered servers."

        server_name = tool_meta["server"]
        orig_name = tool_meta["original_name"]
        transport = tool_meta["transport"]

        if transport == "stdio":
            cmd = tool_meta["command"]
            env = tool_meta["env"]
            try:
                popen_kwargs: Dict[str, Any] = {
                    "stdin": subprocess.PIPE,
                    "stdout": subprocess.PIPE,
                    "stderr": subprocess.DEVNULL,
                    "text": True,
                    "env": env
                }
                if os.name != "nt":
                    popen_kwargs["start_new_session"] = True

                proc = subprocess.Popen(cmd, **popen_kwargs)
                call_req = {
                    "jsonrpc": "2.0",
                    "id": 100,
                    "method": "tools/call",
                    "params": {"name": orig_name, "arguments": arguments}
                }
                proc.stdin.write(json.dumps(call_req) + "\n")
                proc.stdin.flush()
                resp_line = proc.stdout.readline()
                proc.terminate()
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    proc.kill()

                if resp_line:
                    res = json.loads(resp_line)
                    content_blocks = res.get("result", {}).get("content", [])
                    texts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                    return True, "\n".join(texts) or str(res.get("result", ""))
                return False, "Empty response from stdio MCP server"
            except Exception as e:
                return False, f"MCP execution error: {e}"

        elif transport == "http":
            url = tool_meta["url"]
            headers = tool_meta.get("headers") or {"Content-Type": "application/json"}
            try:
                call_req = {
                    "jsonrpc": "2.0",
                    "id": 100,
                    "method": "tools/call",
                    "params": {"name": orig_name, "arguments": arguments}
                }
                resp = requests.post(url, json=call_req, headers=headers, timeout=_RPC_TIMEOUT)
                if resp.status_code == 200:
                    res = resp.json()
                    content_blocks = res.get("result", {}).get("content", [])
                    texts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                    return True, "\n".join(texts) or str(res.get("result", ""))
                return False, f"HTTP MCP error {resp.status_code}: {resp.text}"
            except Exception as e:
                return False, f"MCP HTTP request error: {e}"

        return False, "Unsupported transport"


# Global MCP manager
mcp_manager = MCPClientManager()
