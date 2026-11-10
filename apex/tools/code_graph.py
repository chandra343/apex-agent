"""AST Semantic Code Graph & Intelligent Symbol Explorer for Project Apex.

Provides instant syntactic codebase understanding without blowing context window limits:
- Native AST parsing for Python
- Structural heuristic parsing for TypeScript, JavaScript, Go, PHP, Rust
- Outline generator (classes, methods, docstrings, signatures)
- Symbol reference & caller tracing
- Framework route discovery (FastAPI, Flask, Express, Next.js)
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class CodeGraphEngine:
    """In-memory AST and symbol graph indexer."""

    def __init__(self, root_dir: str = ".") -> None:
        self.root_dir = Path(root_dir).resolve()
        self._index: Dict[str, Dict[str, Any]] = {}

    def index_directory(self, max_files: int = 500) -> Dict[str, Any]:
        """Scan and index all source files in the project."""
        count = 0
        extensions = {".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".php"}
        ignore_dirs = {".git", ".venv", "node_modules", "__pycache__", "dist", "build", ".next", ".pytest_cache"}

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                p = Path(root) / file
                if p.suffix in extensions:
                    rel_path = str(p.relative_to(self.root_dir))
                    self._index[rel_path] = self.inspect_file(str(p))
                    count += 1
                    if count >= max_files:
                        break
            if count >= max_files:
                break

        return {
            "indexed_files": count,
            "root": str(self.root_dir),
            "total_symbols": sum(len(d.get("symbols", [])) for d in self._index.values()),
            "total_routes": sum(len(d.get("routes", [])) for d in self._index.values())
        }

    def inspect_file(self, file_path: str) -> Dict[str, Any]:
        """Generate high-density AST outline of a single file."""
        p = Path(file_path)
        if not p.is_absolute():
            p = self.root_dir / file_path

        if not p.exists():
            return {"error": f"File not found: {file_path}"}

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"error": f"Read error: {e}"}

        if p.suffix == ".py":
            return self._inspect_python(content, str(p.name))
        else:
            return self._inspect_generic(content, str(p.name), p.suffix)

    def _inspect_python(self, content: str, filename: str) -> Dict[str, Any]:
        """Extract classes, functions, decorators, and routes from Python AST."""
        symbols = []
        routes = []
        imports = []

        try:
            tree = ast.parse(content)
        except Exception:
            return self._inspect_generic(content, filename, ".py")

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        imports.append(n.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

            elif isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) for b in node.bases] if hasattr(ast, "unparse") else []
                doc = ast.get_docstring(node) or ""
                doc_preview = doc.split("\n")[0] if doc else ""
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        sig = self._format_py_func_sig(item)
                        methods.append({"name": item.name, "sig": sig, "line": item.lineno})

                symbols.append({
                    "type": "class",
                    "name": node.name,
                    "bases": bases,
                    "line": node.lineno,
                    "doc": doc_preview,
                    "methods": methods
                })

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sig = self._format_py_func_sig(node)
                doc = ast.get_docstring(node) or ""
                doc_preview = doc.split("\n")[0] if doc else ""

                # Check if route decorator is present
                for dec in node.decorator_list:
                    dec_str = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                    route_m = re.search(r"@\w+\.(get|post|put|delete|patch|websocket)\([\"']([^\"']+)[\"']", dec_str)
                    if route_m:
                        routes.append({
                            "method": route_m.group(1).upper(),
                            "path": route_m.group(2),
                            "handler": node.name,
                            "line": node.lineno
                        })

                symbols.append({
                    "type": "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                    "name": node.name,
                    "sig": sig,
                    "line": node.lineno,
                    "doc": doc_preview
                })

        return {
            "filename": filename,
            "symbols_count": len(symbols),
            "symbols": symbols,
            "routes": routes,
            "imports_preview": imports[:10]
        }

    def _format_py_func_sig(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Render a clean signature string from AST arguments."""
        if hasattr(ast, "unparse"):
            try:
                args_str = ast.unparse(node.args)
                ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
                return f"{node.name}({args_str}){ret}"
            except Exception:
                pass
        return f"{node.name}(...)"

    def _inspect_generic(self, content: str, filename: str, ext: str) -> Dict[str, Any]:
        """Regex-based semantic extraction for JS, TS, Go, PHP, Rust."""
        symbols = []
        routes = []

        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            s = line.strip()

            # Class declarations
            cm = re.match(r"^(?:export\s+)?(?:default\s+)?class\s+([A-Za-z0-9_]+)", s)
            if cm:
                symbols.append({"type": "class", "name": cm.group(1), "line": i})
                continue

            # Interfaces & Types (TS)
            tm = re.match(r"^(?:export\s+)?(?:interface|type)\s+([A-Za-z0-9_]+)", s)
            if tm:
                symbols.append({"type": "interface", "name": tm.group(1), "line": i})
                continue

            # Function declarations
            fm = re.match(r"^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\((.*?)\)", s)
            if fm:
                symbols.append({
                    "type": "function",
                    "name": fm.group(1),
                    "sig": f"{fm.group(1)}({fm.group(2)[:30]})",
                    "line": i
                })
                continue

            # Route detection (Express / Fastify)
            rm = re.search(r"(?:app|router)\.(get|post|put|delete|patch)\([\"']([^\"']+)[\"']", s)
            if rm:
                routes.append({
                    "method": rm.group(1).upper(),
                    "path": rm.group(2),
                    "line": i
                })

        return {
            "filename": filename,
            "symbols_count": len(symbols),
            "symbols": symbols,
            "routes": routes
        }

    def find_symbol(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Find definitions of a symbol across all indexed files."""
        if not self._index:
            self.index_directory()

        results = []
        target = symbol_name.lower()
        for fpath, data in self._index.items():
            for sym in data.get("symbols", []):
                if sym["name"].lower() == target or target in sym["name"].lower():
                    results.append({
                        "file": fpath,
                        "type": sym["type"],
                        "name": sym["name"],
                        "line": sym["line"],
                        "sig": sym.get("sig", ""),
                        "doc": sym.get("doc", "")
                    })
                # Check inner methods
                for m in sym.get("methods", []):
                    if m["name"].lower() == target or target in m["name"].lower():
                        results.append({
                            "file": fpath,
                            "type": "method",
                            "name": f"{sym['name']}.{m['name']}",
                            "line": m["line"],
                            "sig": m.get("sig", "")
                        })
        return results

    def find_references(self, symbol_name: str, max_refs: int = 30) -> List[Dict[str, Any]]:
        """Search codebase for occurrences and calls to symbol."""
        refs = []
        pattern = re.compile(r"\b" + re.escape(symbol_name) + r"\b")

        for fpath in self._index.keys():
            full = self.root_dir / fpath
            if not full.exists():
                continue
            try:
                for idx, line in enumerate(full.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if pattern.search(line):
                        refs.append({
                            "file": fpath,
                            "line": idx,
                            "snippet": line.strip()[:140]
                        })
                        if len(refs) >= max_refs:
                            return refs
            except Exception:
                continue
        return refs


code_graph = CodeGraphEngine()


def query_code_graph(action: str, target: str = "", path: str = ".") -> str:
    """Tool function: Query AST code graph for fast symbol exploration."""
    act = action.strip().lower()
    engine = CodeGraphEngine(path)

    if act in ["index", "scan"]:
        stats = engine.index_directory()
        return (
            f"✅ **Codebase Indexing Complete** ({stats['root']}):\n"
            f"• Indexed Files : {stats['indexed_files']}\n"
            f"• Symbols Found : {stats['total_symbols']} (Classes & Functions)\n"
            f"• API Routes    : {stats['total_routes']}"
        )

    if act in ["outline", "inspect"]:
        if not target:
            return "❌ Masukkan nama file target untuk melihat outline AST (contoh: target='apex/agent.py')."
        data = engine.inspect_file(target)
        if "error" in data:
            return f"❌ {data['error']}"

        lines = [f"📄 **AST Outline: {data.get('filename')}** ({data.get('symbols_count', 0)} symbols):"]
        for s in data.get("symbols", []):
            if s["type"] == "class":
                lines.append(f"\n🏛️ **class {s['name']}** (L{s['line']}): {s.get('doc', '')}")
                for m in s.get("methods", []):
                    lines.append(f"   ↳ def {m['sig']} (L{m['line']})")
            else:
                lines.append(f"⚡ **{s['type']} {s.get('sig', s['name'])}** (L{s['line']}) {('— ' + s['doc']) if s.get('doc') else ''}")

        if data.get("routes"):
            lines.append("\n🌐 **API Endpoints:**")
            for r in data["routes"]:
                lines.append(f"   [{r['method']}] {r['path']} ➔ {r.get('handler', '')} (L{r['line']})")

        return "\n".join(lines)

    if act in ["find", "symbol", "lookup"]:
        if not target:
            return "❌ Masukkan nama symbol/function/class untuk dicari (contoh: target='AntiRefusalEngine')."
        engine.index_directory()
        matches = engine.find_symbol(target)
        if not matches:
            return f"ℹ️ Simbol '{target}' tidak ditemukan di codebase."

        lines = [f"🔍 **Ditemukan {len(matches)} definisi untuk '{target}':**"]
        for m in matches:
            lines.append(f"• `[{m['type']}]` **{m['name']}** in `{m['file']}:{m['line']}`")
            if m.get("sig"):
                lines.append(f"  Sig: `{m['sig']}`")
        return "\n".join(lines)

    if act in ["refs", "references", "callers"]:
        if not target:
            return "❌ Masukkan nama symbol untuk mencari referensi (contoh: target='compress_text_rtk')."
        engine.index_directory()
        refs = engine.find_references(target)
        if not refs:
            return f"ℹ️ Tidak ditemukan referensi untuk '{target}'."

        lines = [f"🔗 **Ditemukan {len(refs)} referensi untuk '{target}':**"]
        for r in refs:
            lines.append(f"• `{r['file']}:{r['line']}` ➔ `{r['snippet']}`")
        return "\n".join(lines)

    return (
        "❓ Aksi tidak dikenali. Gunakan salah satu:\n"
        "- `action='index'`: Scan & indeks seluruh codebase\n"
        "- `action='outline', target='path/file.py'`: Lihat peta fungsi & class tanpa baca seluruh isi file\n"
        "- `action='find', target='MyClass'`: Cari letak deklarasi class atau fungsi\n"
        "- `action='refs', target='my_func'`: Cari pemanggil / referensi fungsi di seluruh proyek"
    )
