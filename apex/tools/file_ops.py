"""Host Filesystem Operations (Full Unrestricted Access with Checkpoints)."""
from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from apex.tools.checkpoints import checkpoint_manager


def resolve_path(path_str: str) -> Path:
    """Resolve relative or tilde path to absolute Path."""
    p = Path(path_str).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    return p.resolve()


def read_file(
    path: str,
    offset_lines: int = 0,
    limit_lines: int = 1000
) -> Tuple[bool, str]:
    """Read contents of a file on the host filesystem (supports text, PDF, docx, xlsx, images with OCR, archives, and DBs)."""
    from apex.tools.doc_reader import read_any_file
    return read_any_file(path=path, offset_lines=offset_lines, limit_lines=limit_lines)


def write_file(path: str, content: str, overwrite: bool = True) -> Tuple[bool, str]:
    """Write or overwrite a file on disk, automatically snapshotting the existing state."""
    p = resolve_path(path)
    
    if p.exists() and not overwrite:
        return False, f"File '{p}' already exists and overwrite=False."

    # Safety: take snapshot before modifying
    checkpoint_manager.snapshot_file(p)

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Successfully wrote {len(content)} characters to '{p}'"
    except Exception as e:
        return False, f"Error writing file '{p}': {e}"


def edit_file(path: str, target: str, replacement: str) -> Tuple[bool, str]:
    """Targeted string replacement on an existing file with automatic snapshot."""
    p = resolve_path(path)
    if not p.exists() or not p.is_file():
        return False, f"File not found: {p}"

    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            original = f.read()

        if target not in original:
            return False, f"Target string not found in '{p.name}'. Please ensure whitespace matches exactly."

        occurrences = original.count(target)

        # Safety: take snapshot before editing
        checkpoint_manager.snapshot_file(p)

        modified = original.replace(target, replacement)
        with open(p, "w", encoding="utf-8") as f:
            f.write(modified)

        return True, f"Successfully replaced {occurrences} occurrence(s) of target in '{p.name}'"
    except Exception as e:
        return False, f"Error editing file '{p}': {e}"


def search_files(directory: str = ".", pattern: str = "*", recursive: bool = True) -> Tuple[bool, str]:
    """Search for files matching a glob pattern."""
    d = resolve_path(directory)
    if not d.exists() or not d.is_dir():
        return False, f"Directory not found: {d}"

    matched: list[str] = []
    try:
        if recursive:
            for root, dirs, files in os.walk(d):
                # Filter out heavy folders
                dirs[:] = [sub for sub in dirs if sub not in [".git", "node_modules", ".venv", "__pycache__"]]
                for f in files:
                    if fnmatch.fnmatch(f, pattern):
                        matched.append(str(Path(root) / f))
        else:
            for item in d.iterdir():
                if fnmatch.fnmatch(item.name, pattern):
                    matched.append(str(item))

        if not matched:
            return True, f"No files matching '{pattern}' in '{d}'"

        return True, f"Found {len(matched)} file(s):\n" + "\n".join(matched[:200])
    except Exception as e:
        return False, f"Search error in '{d}': {e}"


def grep_search(query: str, directory: str = ".", file_pattern: str = "*") -> Tuple[bool, str]:
    """Search for a regex or text query inside file contents."""
    d = resolve_path(directory)
    if not d.exists() or not d.is_dir():
        return False, f"Directory not found: {d}"

    results: list[str] = []
    regex = re.compile(query, re.IGNORECASE)

    try:
        for root, dirs, files in os.walk(d):
            dirs[:] = [sub for sub in dirs if sub not in [".git", "node_modules", ".venv", "__pycache__"]]
            for f in files:
                if not fnmatch.fnmatch(f, file_pattern):
                    continue
                file_path = Path(root) / f
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                        for line_num, line in enumerate(fh, 1):
                            if regex.search(line):
                                results.append(f"{file_path}:{line_num}: {line.strip()[:160]}")
                                if len(results) >= 200:
                                    break
                except Exception:
                    pass
            if len(results) >= 200:
                results.append("... [truncated at 200 matches] ...")
                break

        if not results:
            return True, f"No matches found for query '{query}' in '{d}'"

        return True, f"Found {len(results)} match(es):\n" + "\n".join(results)
    except Exception as e:
        return False, f"Grep error in '{d}': {e}"


def list_directory(directory: str = ".", depth: int = 2) -> Tuple[bool, str]:
    """List directory contents up to a specific depth."""
    d = resolve_path(directory)
    if not d.exists() or not d.is_dir():
        return False, f"Directory not found: {d}"

    lines: list[str] = []

    def _walk(current: Path, current_depth: int) -> None:
        if current_depth > depth:
            return
        try:
            items = sorted(current.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            for it in items:
                if it.name in [".git", "node_modules", ".venv", "__pycache__"]:
                    continue
                prefix = "  " * current_depth + ("📁 " if it.is_dir() else "📄 ")
                lines.append(f"{prefix}{it.name}")
                if it.is_dir():
                    _walk(it, current_depth + 1)
        except PermissionError:
            lines.append("  " * current_depth + "⚠️ [Permission Denied]")

    lines.append(f"📁 {d}")
    _walk(d, 1)
    return True, "\n".join(lines[:300])
