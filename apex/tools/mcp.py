"""Model Context Protocol (MCP) Client: stdio & HTTP/SSE transports (Zeline & Hermes Style)."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import requests
from apex.config import config

MCP_TOOL_PREFIX = "mcp__"
_RPC_TIMEOUT = 12
_DISCOVERY_DEADLINE = 6.0


class MCPClientManager:
    """Manages connections to external MCP servers and registers their tools."""

    def __init__(self) -> None:
        self._servers: Dict[str, Any] = {}
        self._tools_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def discover_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """List and cache tools from all registered MCP servers in config."""
        servers_cfg = config.get("mcpServers", {})
        discovered: Dict[str, Dict[str, Any]] = {}

        for server_name, s_data in servers_cfg.items():
            command = s_data.get("command")
            args = s_data.get("args", [])
            env = s_data.get("env", {})
            url = s_data.get("url")

            if command:
                # stdio transport
                tools = self._discover_stdio_tools(server_name, command, args, env)
                discovered.update(tools)
            elif url:
                # http/sse transport
                tools = self._discover_http_tools(server_name, url)
                discovered.update(tools)

        with self._lock:
            self._tools_cache = discovered
        return discovered

    def _discover_stdio_tools(
        self,
        server_name: str,
        command: str,
        args: list[str],
        env: dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        full_cmd = [command] + args
        proc_env = os.environ.copy()
        proc_env.update(env)

        tools: Dict[str, Dict[str, Any]] = {}
        try:
            proc = subprocess.Popen(
                full_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                env=proc_env
            )

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
        except Exception:
            pass

        return tools

    def _discover_http_tools(self, server_name: str, url: str) -> Dict[str, Dict[str, Any]]:
        tools: Dict[str, Dict[str, Any]] = {}
        try:
            req_body = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            resp = requests.post(url, json=req_body, timeout=_DISCOVERY_DEADLINE)
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
                        "url": url
                    }
        except Exception:
            pass
        return tools

    def call_tool(self, scoped_tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute a tool on an external MCP server."""
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
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    env=env
                )
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
            try:
                call_req = {
                    "jsonrpc": "2.0",
                    "id": 100,
                    "method": "tools/call",
                    "params": {"name": orig_name, "arguments": arguments}
                }
                resp = requests.post(url, json=call_req, timeout=_RPC_TIMEOUT)
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
