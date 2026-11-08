"""System inspection, resource monitoring, and listening ports detection."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from typing import Dict, List, Tuple


def get_system_info() -> Tuple[bool, str]:
    """Retrieve host hardware, OS platform, memory, and environment summary."""
    info: list[str] = [
        f"🖥️ OS: {platform.system()} {platform.release()} ({platform.machine()})",
        f"👤 User: {os.environ.get('USER', 'unknown')}",
        f"🐍 Python: {platform.python_version()}",
        f"📁 Current Working Directory: {os.getcwd()}"
    ]

    # Disk usage
    try:
        usage = shutil.disk_usage(".")
        free_gb = round(usage.free / (1024**3), 2)
        total_gb = round(usage.total / (1024**3), 2)
        info.append(f"💾 Disk Free: {free_gb} GB / {total_gb} GB")
    except Exception:
        pass

    # Memory info on Linux via /proc/meminfo
    meminfo_path = "/proc/meminfo"
    if os.path.exists(meminfo_path):
        try:
            mem: Dict[str, int] = {}
            with open(meminfo_path, "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        k = parts[0].strip()
                        v = parts[1].strip().split()[0]
                        if v.isdigit():
                            mem[k] = int(v)
            if "MemTotal" in mem and "MemAvailable" in mem:
                total_mb = mem["MemTotal"] // 1024
                avail_mb = mem["MemAvailable"] // 1024
                info.append(f"🧠 RAM Available: {avail_mb} MB / {total_mb} MB")
        except Exception:
            pass

    return True, "\n".join(info)


def get_listening_ports() -> Tuple[bool, str]:
    """Detect active listening TCP/UDP ports on the host system."""
    commands_to_try = [
        ["ss", "-tuln"],
        ["netstat", "-tuln"],
        ["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"]
    ]

    for cmd in commands_to_try:
        if shutil.which(cmd[0]):
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                if proc.returncode == 0 and proc.stdout:
                    lines = proc.stdout.splitlines()[:50]
                    return True, f"=== Listening Ports ({cmd[0]}) ===\n" + "\n".join(lines)
            except Exception:
                continue

    return False, "Neither 'ss', 'netstat', nor 'lsof' is available to inspect network ports."


def list_system_processes(filter_name: str = "") -> Tuple[bool, str]:
    """List running processes filtered by name or sorted by resource usage."""
    if shutil.which("ps"):
        cmd = ["ps", "aux"]
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            lines = proc.stdout.splitlines()
            header = lines[0] if lines else ""
            matches: list[str] = []
            for line in lines[1:]:
                if not filter_name or filter_name.lower() in line.lower():
                    matches.append(line)
                    if len(matches) >= 40:
                        break
            return True, f"{header}\n" + "\n".join(matches)
        except Exception as e:
            return False, f"Failed to list processes: {e}"

    return False, "'ps' command is not available."
