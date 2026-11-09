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

    def auto_detect_filter(self, text: str) -> str:
        """Heuristically identify the payload type to apply optimal compression."""
        head = text[:8192]
        if re.search(r"^diff --git |^@@ ", head, re.M):
            return "git-diff"
        if re.search(r"^On branch |^nothing to commit|^Changes (not |to be )|^Untracked files:", head, re.M):
            return "git-status"
        if "├──" in head or "└──" in head:
            return "tree"
        lines = [line.strip() for line in head.splitlines() if line.strip()]
        if len(lines) >= 3 and all(re.match(r"^[^\s:]+:\d+:", line) for line in lines[:5]):
            return "grep"
        if len(lines) >= 5 and sum(1 for line in lines if re.match(r"^\s*\d+[→|\t:]\s", line)) / max(1, len(lines)) >= 0.6:
            return "read-numbered"
        if self._has_adjacent_duplicates(lines):
            return "dedup-log"
        return "generic"

    def _has_adjacent_duplicates(self, lines: list[str]) -> bool:
        """Check if output contains adjacent repeating log lines."""
        for i in range(len(lines) - 1):
            if lines[i] == lines[i + 1]:
                return True
        return False

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

        # 3. Detect category automatically if tool_name is unspecified
        detected_category = self.auto_detect_filter(result)

        # 4. Tool-specific compressions
        if "diff" in tool_name.lower() or detected_category == "git-diff":
            result = self._compress_git_diff(result)
        elif "tree" in tool_name.lower() or "find" in tool_name.lower() or "ls" in tool_name.lower() or detected_category in ("tree", "git-status"):
            result = self._compress_directory_listing(result)
        elif "grep" in tool_name.lower() or "search" in tool_name.lower() or detected_category in ("grep", "read-numbered"):
            result = self._compress_grep_results(result)
        elif "log" in tool_name.lower() or "build" in tool_name.lower() or detected_category == "dedup-log":
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


# ---------------------------------------------------------------------------
# Ponytail — Idempotent / Bounded System-Prompt Policy (from OhMyRouter)
# ---------------------------------------------------------------------------

PONYTAIL_SENTINEL = "<!-- apex-ponytail:v1 -->"

PONYTAIL_SYSTEM_PROMPT = (
    "You are a concise, minimal-solution engineering assistant. "
    "Provide the smallest correct solution. Prefer direct code and brief explanations. "
    "Do not pad with unnecessary context or verbose preambles."
)


def apply_ponytail(messages: list[dict], enabled: bool = True) -> list[dict]:
    """Deterministic, idempotent, bounded system-prompt policy inspired by OhMyRouter.

    Inserts a minimal-solution directive only once. If sentinel is already present,
    returns messages untouched (idempotent across multi-turn chats).
    """
    if not enabled or not messages:
        return messages

    # Idempotence check
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str) and PONYTAIL_SENTINEL in content:
            return messages

    ponytail_msg = {
        "role": "system",
        "content": f"{PONYTAIL_SENTINEL}\n{PONYTAIL_SYSTEM_PROMPT}"
    }

    # Find last system message index
    last_sys_idx = -1
    for i, m in enumerate(messages):
        if m.get("role") in ("system", "developer"):
            last_sys_idx = i

    out = list(messages)
    if last_sys_idx == -1:
        out.insert(0, ponytail_msg)
    else:
        out.insert(last_sys_idx + 1, ponytail_msg)
    return out

