"""Cross-Platform File Picker Helper for SOUL and Configuration Files."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def pick_file(prompt_title: str = "Select File", default_path: Optional[str] = None) -> Optional[str]:
    """Open a native file dialog if available, or fall back to terminal input."""
    # 1. Try Linux Zenity (GNOME / GTK)
    if shutil.which("zenity") and os.environ.get("DISPLAY"):
        try:
            cmd = ["zenity", "--file-selection", f"--title={prompt_title}"]
            if default_path and Path(default_path).exists():
                cmd.append(f"--filename={default_path}")
            res = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
            if res:
                return res
        except Exception:
            pass

    # 2. Try Linux Kdialog (KDE / Qt)
    if shutil.which("kdialog") and os.environ.get("DISPLAY"):
        try:
            cmd = ["kdialog", "--getopenfilename", default_path or str(Path.home()), f"All Files (*)\n|{prompt_title}"]
            res = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
            if res:
                return res
        except Exception:
            pass

    # 3. Try Windows PowerShell OpenFileDialog
    if sys.platform == "win32":
        try:
            ps_script = """
            Add-Type -AssemblyName System.Windows.Forms
            $dialog = New-Object System.Windows.Forms.OpenFileDialog
            $dialog.Title = '__TITLE__'
            $dialog.Filter = 'Markdown & Text Files (*.md;*.txt)|*.md;*.txt|All Files (*.*)|*.*'
            if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                Write-Output $dialog.FileName
            }
            """.replace("__TITLE__", prompt_title)
            res = subprocess.check_output(["powershell", "-Command", ps_script], text=True, stderr=subprocess.DEVNULL).strip()
            if res:
                return res
        except Exception:
            pass

    # 4. Fallback to clean CLI terminal input
    default_str = f" [{default_path}]" if default_path else ""
    try:
        val = input(f"📁 {prompt_title}{default_str}: ").strip()
        if not val and default_path:
            return default_path
        if val:
            p = Path(val).expanduser().resolve()
            if p.exists():
                return str(p)
            print(f"⚠️ File does not exist: {p}")
    except (EOFError, KeyboardInterrupt):
        return None

    return None
