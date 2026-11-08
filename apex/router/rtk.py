"""RTK (Request Token Keeper) Token Saver.

Implements in-memory payload compression for bulky tool outputs (git diff,
grep search, directory listings, file contents). Reduces token consumption
by 20-40% before dispatching payloads to the LLM.
"""
from __future__ import annotations

import re
from typing import Tuple


class RTKTokenSaver:
    """Intelligent token compressor using regex and AST-friendly heuristics."""

    def __init__(self, threshold_bytes: int = 1024) -> None:
        self.threshold_bytes = threshold_bytes

    def compress(self, text: str, tool_name: str = "") -> Tuple[str, int, int]:
        """Compress tool output string if it exceeds the threshold.

        Returns:
            Tuple[compressed_text, original_chars, compressed_chars]
        """
        if not text or len(text) < self.threshold_bytes:
            return text, len(text), len(text)

        original_len = len(text)
        result = text

        # 1. Clean excessive blank lines (more than 2 consecutive newlines -> 2)
        result = re.sub(r"\n\s*\n\s*\n+", "\n\n", result)

        # 2. Trim trailing whitespace from each line
        result = "\n".join(line.rstrip() for line in result.splitlines())

        # 3. Tool-specific compressions
        if "diff" in tool_name.lower() or result.startswith("diff --git"):
            result = self._compress_git_diff(result)
        elif "tree" in tool_name.lower() or "find" in tool_name.lower() or "ls" in tool_name.lower():
            result = self._compress_directory_listing(result)
        elif "grep" in tool_name.lower() or "search" in tool_name.lower():
            result = self._compress_grep_results(result)
        elif "log" in tool_name.lower() or "build" in tool_name.lower():
            result = self._compress_build_logs(result)

        compressed_len = len(result)
        return result, original_len, compressed_len

    def _compress_git_diff(self, diff_text: str) -> str:
        """Compress git diff by condensing large blocks of unchanged lines."""
        lines = diff_text.splitlines()
        out_lines: list[str] = []
        unchanged_buffer: list[str] = []

        for line in lines:
            if line.startswith(" ") and not line.startswith("+++") and not line.startswith("---"):
                unchanged_buffer.append(line)
            else:
                if len(unchanged_buffer) > 6:
                    # Keep first 2 and last 2, condense middle
                    out_lines.extend(unchanged_buffer[:2])
                    out_lines.append(f"  ... [{len(unchanged_buffer) - 4} unchanged lines skipped by RTK] ...")
                    out_lines.extend(unchanged_buffer[-2:])
                else:
                    out_lines.extend(unchanged_buffer)
                unchanged_buffer.clear()
                out_lines.append(line)

        if len(unchanged_buffer) > 6:
            out_lines.extend(unchanged_buffer[:2])
            out_lines.append(f"  ... [{len(unchanged_buffer) - 4} unchanged lines skipped by RTK] ...")
            out_lines.extend(unchanged_buffer[-2:])
        else:
            out_lines.extend(unchanged_buffer)

        return "\n".join(out_lines)

    def _compress_directory_listing(self, text: str) -> str:
        """Filter out noisy build/dependency directories from directory trees."""
        lines = text.splitlines()
        filtered: list[str] = []
        skipped_count = 0

        noise_patterns = [
            "node_modules/", ".git/", "__pycache__/", ".venv/",
            "target/", "dist/", "build/", ".idea/", ".vscode/"
        ]

        for line in lines:
            if any(pattern in line for pattern in noise_patterns):
                skipped_count += 1
                continue
            filtered.append(line)

        if skipped_count > 0:
            filtered.append(f"... [RTK: skipped {skipped_count} ignored dependency/build entries] ...")

        return "\n".join(filtered)

    def _compress_grep_results(self, text: str) -> str:
        """Limit overly repetitive grep matches."""
        lines = text.splitlines()
        if len(lines) > 200:
            head = lines[:100]
            tail = lines[-50:]
            return "\n".join(head + [f"... [RTK: {len(lines) - 150} intermediate matches condensed] ..."] + tail)
        return text

    def _compress_build_logs(self, text: str) -> str:
        """Collapse repeated warning patterns in build/test logs."""
        lines = text.splitlines()
        filtered: list[str] = []
        last_warning = ""
        warning_repeat_count = 0

        for line in lines:
            if "warning:" in line.lower():
                norm = re.sub(r":\d+:\d+", ":*:*", line)
                if norm == last_warning:
                    warning_repeat_count += 1
                    continue
                else:
                    if warning_repeat_count > 1:
                        filtered.append(f"... [repeated {warning_repeat_count} more times] ...")
                    warning_repeat_count = 0
                    last_warning = norm
            else:
                if warning_repeat_count > 1:
                    filtered.append(f"... [repeated {warning_repeat_count} more times] ...")
                warning_repeat_count = 0
                last_warning = ""
            filtered.append(line)

        return "\n".join(filtered)


# Global RTK instance
rtk_compressor = RTKTokenSaver()
