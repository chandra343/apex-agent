"""Binary Reverse Engineering Suite: Disassembly & ELF/PE Inspection."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple


def inspect_binary(file_path: str) -> Tuple[bool, str]:
    """Inspect binary file format (ELF, PE, Mach-O), architecture, and headers."""
    p = Path(file_path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return False, f"File not found: {p}"

    info_lines: list[str] = [f"🔍 Inspecting Binary: {p} ({p.stat().st_size} bytes)"]

    # 1. Read Magic Bytes
    try:
        with open(p, "rb") as f:
            magic = f.read(16)
        if magic.startswith(b"\x7fELF"):
            bitness = "64-bit" if magic[4] == 2 else "32-bit"
            endian = "Little-endian" if magic[5] == 1 else "Big-endian"
            info_lines.append(f"Format: ELF ({bitness}, {endian})")
        elif magic.startswith(b"MZ"):
            info_lines.append("Format: Windows PE (Portable Executable)")
        elif magic[:4] in [b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe"]:
            info_lines.append("Format: macOS Mach-O")
        else:
            info_lines.append(f"Format: Unknown / Raw (Magic: {magic[:8].hex()})")
    except Exception as e:
        return False, f"Error reading header: {e}"

    # 2. Use system tools if available (readelf, file, ldd, nm)
    if shutil.which("file"):
        try:
            out = subprocess.check_output(["file", "-b", str(p)], text=True, stderr=subprocess.DEVNULL)
            info_lines.append(f"System File Info: {out.strip()}")
        except Exception:
            pass

    if shutil.which("readelf") and magic.startswith(b"\x7fELF"):
        try:
            out = subprocess.check_output(["readelf", "-h", str(p)], text=True, stderr=subprocess.DEVNULL)
            info_lines.append("\n=== ELF Header ===\n" + out.strip())
        except Exception:
            pass

    return True, "\n".join(info_lines)


def disassemble_binary(
    file_path: str,
    symbol: str = "main",
    max_lines: int = 100
) -> Tuple[bool, str]:
    """Disassemble functions or symbols from an executable binary using objdump."""
    p = Path(file_path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return False, f"Binary not found: {p}"

    if not shutil.which("objdump"):
        return False, "Tool 'objdump' is not installed on this system. Install binutils to enable disassembly."

    cmd = ["objdump", "-d", f"--disassemble={symbol}", str(p)]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
        if proc.returncode != 0:
            # Fallback to general disassembly
            cmd = ["objdump", "-d", "-M", "intel", str(p)]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)

        lines = proc.stdout.splitlines()[:max_lines]
        if not lines:
            return False, f"No disassembly output produced for symbol '{symbol}': {proc.stderr[:200]}"

        return True, f"=== Disassembly: {p.name} ({symbol}) ===\n" + "\n".join(lines)
    except Exception as e:
        return False, f"Disassembly error: {e}"
