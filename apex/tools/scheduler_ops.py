"""Cron & Autonomous Background Scheduler Tool for Project Apex."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from apex.scheduler.scheduler import task_scheduler


def manage_scheduled_tasks(
    action: str,
    name: Optional[str] = None,
    interval_minutes: int = 60,
    prompt: Optional[str] = None
) -> str:
    """Manage autonomous recurring background tasks and cron jobs in Project Apex.

    Args:
        action: 'list' to view active jobs, 'add' to create a recurring task, or 'remove' to cancel one.
        name: Unique name for the job (e.g. 'health_check', 'daily_cleanup').
        interval_minutes: Execution frequency interval in minutes (default: 60).
        prompt: Task instruction or command prompt for Apex to execute autonomously on schedule.

    Returns:
        Structured confirmation or listing of scheduled jobs.
    """
    act = action.strip().lower()

    if act == "list":
        jobs = task_scheduler.list_jobs()
        if not jobs:
            return "⏰ **Scheduled Background Jobs**: Belum ada tugas terjadwal yang terdaftar."

        lines = [f"⏰ **Daftar Tugas Latar Belakang Terjadwal ({len(jobs)} Tugas)**:\n"]
        for idx, j in enumerate(jobs, 1):
            j_name = j.get("name", "unnamed")
            interval_m = round(j.get("interval_seconds", 3600) / 60, 1)
            p = j.get("prompt", "")[:70] + ("..." if len(j.get("prompt", "")) > 70 else "")
            r_count = j.get("run_count", 0)
            last_run = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(j.get("last_run", 0)))
            lines.append(
                f"{idx}. **`{j_name}`** (Setiap {interval_m} menit · Run count: {r_count})\n"
                f"   • Prompt: *\"{p}\"*\n"
                f"   • Terakhir Dijalankan: `{last_run}`"
            )
        return "\n".join(lines)

    elif act == "add":
        if not name or not prompt:
            return "❌ Parameter `name` dan `prompt` wajib diisi untuk membuat tugas terjadwal baru."

        interval_sec = max(60, int(interval_minutes * 60))
        task_scheduler.add_job(name, interval_seconds=interval_sec, prompt_instruction=prompt)
        return (
            f"✅ **Tugas Terjadwal Berhasil Dibuat** ⏰\n\n"
            f"• Nama: `{name}`\n"
            f"• Interval: Setiap **{interval_minutes} menit** ({interval_sec} detik)\n"
            f"• Prompt: *\"{prompt}\"*\n"
            f"Tugas ini akan dieksekusi secara mandiri oleh Apex."
        )

    elif act == "remove":
        if not name:
            return "❌ Parameter `name` wajib diisi untuk menghapus tugas terjadwal."

        ok = task_scheduler.remove_job(name)
        if ok:
            return f"🗑️ **Tugas Dihapus**: Tugas terjadwal `{name}` berhasil dibatalkan."
        return f"⚠️ Tugas terjadwal dengan nama `{name}` tidak ditemukan."

    return f"❌ Aksi '{action}' tidak dikenali. Gunakan 'list', 'add', atau 'remove'."
