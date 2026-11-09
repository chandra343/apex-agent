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
from apex.tools.swarm_ops import dispatch_subagents
from apex.tools.db_ops import query_database
from apex.tools.speech import synthesize_speech
from apex.tools.web_scraper import scrape_structured_web
from apex.tools.memory_ops import (
    remember_fact, recall_memory, index_knowledge_base, search_knowledge_base
)
from apex.tools.scheduler_ops import manage_scheduled_tasks
from apex.tools.code_audit import audit_codebase
from apex.tools.doctor import run_system_doctor
from apex.tools.learning_ops import record_learned_lesson, consult_learned_lessons
from apex.tools.devops import run_project_tests, create_git_patch
from apex.tools.network_diag import benchmark_http_endpoint, check_ssl_certificate, lookup_dns_records
from apex.tools.config_ops import manage_system_config
from apex.tools.provider_ops import manage_ai_providers
from apex.tools.tool_discovery import tool_discovery
from apex.tools.data_lake import shared_data_lake

CORE_TOOL_NAMES = {
    "read_file", "write_file", "edit_file", "search_files", "grep_search",
    "list_directory", "run_shell", "python_repl", "web_search",
    "tool_search", "tool_describe", "manage_data_lake", "manage_scheduled_tasks",
    "routine_no_update"
}


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

        # Multi-Agent Swarm Orchestrator
        self.register("dispatch_subagents", "Dispatch a team of specialized sub-agents (researcher, coder, tester, auditor) concurrently in parallel to solve complex multi-step tasks", {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "description": "List of sub-agent task definitions with 'role' ('researcher', 'coder', 'tester', 'auditor') and 'task'",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["researcher", "coder", "tester", "auditor"]},
                            "task": {"type": "string", "description": "Specific instruction for the sub-agent"}
                        },
                        "required": ["role", "task"]
                    }
                }
            },
            "required": ["tasks"]
        }, lambda args: dispatch_subagents(args["tasks"]), is_safe=False)

        # Database Query & Explorer Tool
        self.register("query_database", "Inspect table schemas or execute SQL queries on a SQLite database file", {
            "type": "object",
            "properties": {
                "database": {"type": "string", "description": "Path to SQLite database file (e.g. 'users.db', '~/.apex/memory.db')"},
                "query": {"type": "string", "description": "Optional SQL query to execute. Omit to inspect table schemas"},
                "limit": {"type": "integer", "description": "Maximum number of rows to return", "default": 50}
            },
            "required": ["database"]
        }, lambda args: query_database(args["database"], args.get("query"), args.get("limit", 50)), is_safe=False)

        # Text-to-Speech (TTS) Voice Synthesis
        self.register("synthesize_speech", "Synthesize text into an audio MP3 speech file", {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to convert into speech audio"},
                "output_path": {"type": "string", "description": "Optional destination audio file path (.mp3)"},
                "language": {"type": "string", "description": "Language code (default: 'id' for Indonesian, 'en' for English)", "default": "id"}
            },
            "required": ["text"]
        }, lambda args: synthesize_speech(args["text"], args.get("output_path"), args.get("language", "id")), is_safe=True)

        # Structured Web Scraper
        self.register("scrape_structured_web", "Scrape a web page and extract clean Markdown content, title, metadata, tables, and links without boilerplate noise", {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Web URL to scrape (e.g. 'https://example.com')"},
                "extract_links": {"type": "boolean", "description": "Whether to extract outbound hyperlinks", "default": True},
                "max_length": {"type": "integer", "description": "Maximum characters of content to extract", "default": 5000}
            },
            "required": ["url"]
        }, lambda args: scrape_structured_web(args["url"], args.get("extract_links", True), args.get("max_length", 5000)), is_safe=True)

        # Long-Term Memory Tools
        self.register("remember_fact", "Store an important fact, user preference, architectural decision, or lesson into long-term memory", {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The fact or lesson to remember"},
                "category": {"type": "string", "description": "Category name (e.g. preference, project, credential)", "default": "general"},
                "tags": {"type": "string", "description": "Comma-separated search tags", "default": ""}
            },
            "required": ["content"]
        }, lambda args: remember_fact(args["content"], args.get("category", "general"), args.get("tags", "")), is_safe=False)

        self.register("recall_memory", "Recall or search stored facts and long-term memories using semantic full-text search", {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword or phrase to search in memory"},
                "limit": {"type": "integer", "description": "Maximum number of memories to return", "default": 5}
            },
            "required": ["query"]
        }, lambda args: recall_memory(args["query"], args.get("limit", 5)), is_safe=True)

        # Local RAG Knowledge Base Tools
        self.register("index_knowledge_base", "Index an entire folder or document into Apex's local RAG semantic search knowledge base", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file or folder to index (e.g. 'docs/', 'src/', 'README.md')"},
                "max_files": {"type": "integer", "description": "Maximum files to index", "default": 100}
            },
            "required": ["path"]
        }, lambda args: index_knowledge_base(args["path"], args.get("max_files", 100)), is_safe=False)

        self.register("search_knowledge_base", "Search the local RAG knowledge base for specific information across indexed project files", {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Question or technical keyword to locate"},
                "limit": {"type": "integer", "description": "Maximum number of code/doc snippets to retrieve", "default": 5}
            },
            "required": ["query"]
        }, lambda args: search_knowledge_base(args["query"], args.get("limit", 5)), is_safe=True)

        # Cron & Background Scheduler
        self.register("manage_scheduled_tasks", "Manage autonomous recurring background tasks and cron jobs in Project Apex", {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "add", "remove"], "description": "Action to perform"},
                "name": {"type": "string", "description": "Unique name for the job"},
                "interval_minutes": {"type": "integer", "description": "Execution frequency interval in minutes", "default": 60},
                "prompt": {"type": "string", "description": "Task instruction prompt for Apex to execute autonomously on schedule"}
            },
            "required": ["action"]
        }, lambda args: manage_scheduled_tasks(args["action"], args.get("name"), args.get("interval_minutes", 60), args.get("prompt")), is_safe=False)

        # Automated Codebase Auditor & Security Posture Analyzer
        self.register("audit_codebase", "Run an automated security audit and code quality scan on a directory or file", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to directory or single file to audit", "default": "."},
                "scan_secrets": {"type": "boolean", "description": "Scan for exposed credentials/tokens", "default": True},
                "scan_vulnerabilities": {"type": "boolean", "description": "Check for dangerous coding patterns", "default": True},
                "max_files": {"type": "integer", "description": "Maximum files to scan", "default": 150}
            }
        }, lambda args: audit_codebase(args.get("path", "."), args.get("scan_secrets", True), args.get("scan_vulnerabilities", True), args.get("max_files", 150)), is_safe=True)

        # System Doctor & Self-Healing
        self.register("run_system_doctor", "Run an automated diagnostic check and self-healing repair across all Apex subsystems, databases, and dependencies", {
            "type": "object",
            "properties": {
                "auto_repair": {"type": "boolean", "description": "Automatically repair missing directories and initialize schemas", "default": True}
            }
        }, lambda args: run_system_doctor(args.get("auto_repair", True)), is_safe=False)

        # Autonomous Lessons & Meta-Learning
        self.register("record_learned_lesson", "Record an operational DO or DONT lesson into Apex's permanent memory to prevent repeating past errors", {
            "type": "object",
            "properties": {
                "trigger_pattern": {"type": "string", "description": "Trigger keyword, tool name, or context (e.g. 'git_commit', 'sql_query')"},
                "rule_type": {"type": "string", "enum": ["DO", "DONT"], "description": "'DO' for best practice or 'DONT' for error pattern to avoid"},
                "explanation": {"type": "string", "description": "Detailed operational rule and actionable guidance"}
            },
            "required": ["trigger_pattern", "rule_type", "explanation"]
        }, lambda args: record_learned_lesson(args["trigger_pattern"], args["rule_type"], args["explanation"]), is_safe=False)

        self.register("consult_learned_lessons", "Consult stored operational lessons and guidelines learned from previous tool executions", {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Optional keyword to filter rules", "default": ""}
            }
        }, lambda args: consult_learned_lessons(args.get("query", "")), is_safe=True)

        # DevOps CI/CD & Test Runner
        self.register("run_project_tests", "Auto-detect and execute the test suite for a project (pytest, npm test, cargo test, go test) with structured pass/fail diagnostics", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Root path of the project", "default": "."},
                "framework": {"type": "string", "description": "Optional framework override (pytest, npm, go, cargo)"},
                "timeout": {"type": "integer", "description": "Execution timeout in seconds", "default": 120}
            }
        }, lambda args: run_project_tests(args.get("path", "."), args.get("framework"), args.get("timeout", 120)), is_safe=False)

        self.register("create_git_patch", "Create an isolated Git branch, stage working changes, and synthesize a clean commit or patch", {
            "type": "object",
            "properties": {
                "branch_name": {"type": "string", "description": "Optional new branch to create and checkout"},
                "commit_message": {"type": "string", "description": "Optional commit message to commit changes"}
            }
        }, lambda args: create_git_patch(args.get("branch_name"), args.get("commit_message")), is_safe=False)

        # Network & SSL Diagnostic Suite
        self.register("benchmark_http_endpoint", "Benchmark an HTTP/HTTPS endpoint measuring latency percentiles, TTFB, and status codes", {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target web or API URL"},
                "request_count": {"type": "integer", "description": "Number of probe requests (default: 5)", "default": 5}
            },
            "required": ["url"]
        }, lambda args: benchmark_http_endpoint(args["url"], args.get("request_count", 5)), is_safe=True)

        self.register("check_ssl_certificate", "Inspect SSL/TLS certificate validity, expiry date, days remaining, and issuer", {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "Hostname or domain name (e.g. 'google.com')"},
                "port": {"type": "integer", "description": "Port (default: 443)", "default": 443}
            },
            "required": ["host"]
        }, lambda args: check_ssl_certificate(args["host"], args.get("port", 443)), is_safe=True)

        self.register("lookup_dns_records", "Resolve DNS address records for a domain using native socket resolution", {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Target domain name"},
                "record_type": {"type": "string", "enum": ["A", "AAAA"], "default": "A"}
            },
            "required": ["domain"]
        }, lambda args: lookup_dns_records(args["domain"], args.get("record_type", "A")), is_safe=True)

        # System Configuration Manager Tool
        self.register("manage_system_config", "Inspect or update Project Apex system settings dynamically (e.g. default_model, router.rtk_compression)", {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["get", "set", "list"], "description": "Action to perform"},
                "key_path": {"type": "string", "description": "Nested configuration key path (e.g. 'default_model', 'router.rtk_compression')"},
                "value": {"type": "string", "description": "New value to assign when action is 'set'"}
            },
            "required": ["action"]
        }, lambda args: manage_system_config(args["action"], args.get("key_path"), args.get("value")), is_safe=False)

        # AI Provider Management Tool
        self.register("manage_ai_providers", "Search, switch, test, add, or configure AI providers and models dynamically", {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "search", "use", "add", "test", "fetch_models", "scan_local", "remove"],
                    "description": "Operation to perform on providers"
                },
                "provider_name": {"type": "string", "description": "Provider ID (e.g. 'groq', 'deepseek', 'ollama', 'anthropic')"},
                "api_key": {"type": "string", "description": "API key or token when adding or configuring"},
                "base_url": {"type": "string", "description": "Custom base URL endpoint"},
                "model_name": {"type": "string", "description": "Model ID to activate or register"},
                "query": {"type": "string", "description": "Search keyword (e.g. 'free', 'coding', 'fast', 'groq', 'sonnet')"}
            },
            "required": ["action"]
        }, lambda args: manage_ai_providers(
            args["action"],
            args.get("provider_name"),
            args.get("api_key"),
            args.get("base_url"),
            args.get("model_name"),
            args.get("query")
        ), is_safe=False)

        # OpenBot-inspired Superpowers:
        # 1. Dynamic Tool Discovery & Deferred Loading
        self.register("tool_search", "Search registered tools by keyword matching against names, descriptions, and capabilities", {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword to search tools (e.g. 'dns', 'ssl', 'database', 'devops', 'reverse', 'doctor')"},
                "max_results": {"type": "integer", "description": "Maximum tool results to return (default: 5)", "default": 5}
            },
            "required": ["query"]
        }, lambda args: (True, tool_discovery.search(self._tools, args["query"], args.get("max_results", 5))), is_safe=True)

        self.register("tool_describe", "Inspect detailed parameters, types, and schema of any registered tool in Apex", {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "Exact name of the tool to inspect"}
            },
            "required": ["tool_name"]
        }, lambda args: (True, tool_discovery.describe(self._tools, args["tool_name"])), is_safe=True)

        # 2. Shared SQLite Data Lake
        self.register("manage_data_lake", "Query, create tables, insert, and inspect multi-agent relational data in the shared SQLite Data Lake (~/.apex/agent_data.db)", {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["query", "list_tables", "describe_table"], "description": "Operation to perform"},
                "query": {"type": "string", "description": "SQL statement (SELECT, INSERT, UPDATE, CREATE TABLE) to execute when action='query'"},
                "table_name": {"type": "string", "description": "Name of the table to describe when action='describe_table'"},
                "agent_id": {"type": "string", "description": "Identifier of the agent executing the operation", "default": "apex"}
            },
            "required": ["action"]
        }, lambda args: (
            (True, shared_data_lake.list_tables()) if args["action"] == "list_tables"
            else (True, shared_data_lake.describe_table(args.get("table_name", ""))) if args["action"] == "describe_table"
            else (True, shared_data_lake.query(args.get("query", ""), agent_id=args.get("agent_id", "apex")))
        ), is_safe=False)

        # 3. Quiet Routine Runs
        self.register("routine_no_update", "Mark a scheduled task or background monitoring turn as quiet (no anomalies or urgent updates to report, suppresses noisy notifications)", {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Reason why no update is needed (e.g. 'All services healthy, 0 errors detected')", "default": "Pemeriksaan selesai tanpa anomali."}
            }
        }, lambda args: (True, f"🔕 [Quiet Run]: {args.get('reason', 'Pemeriksaan selesai tanpa anomali. Notifikasi disembunyikan.')}"), is_safe=True)

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

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return combined dictionary of all active tools (native, custom, and mcp)."""
        combined = dict(self._tools)
        combined.update(self.get_mcp_tools())
        return combined

    def is_safe_tool(self, name: str) -> bool:
        """Check if a tool is read-only (safe for parallel dispatch)."""
        if name in self._tools:
            return self._tools[name]["is_safe"]
        return False

    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return tool schemas in OpenAI/Anthropic format, including dynamic MCP tools."""
        deferred = config.get("tools.deferred_discovery", False)
        defs: list[dict[str, Any]] = []
        for name, t in self._tools.items():
            if deferred and name not in CORE_TOOL_NAMES and not t.get("is_active_session"):
                continue
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
                res = self._tools[name]["handler"](arguments)
                if isinstance(res, tuple) and len(res) == 2:
                    success, output = res
                elif isinstance(res, bool):
                    success, output = res, ""
                else:
                    success, output = True, str(res)
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
