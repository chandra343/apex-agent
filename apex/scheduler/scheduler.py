"""In-App Cron & Interval Task Scheduler with Anti-Stampede Protection (Zeline Style)."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from apex.config import SCHEDULER_JOBS_FILE


class TaskScheduler:
    """Manages autonomous scheduled jobs (morning briefings, backups, API polls)."""

    def __init__(self) -> None:
        self.jobs_file = SCHEDULER_JOBS_FILE
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if self.jobs_file.exists():
            try:
                with open(self.jobs_file, "r", encoding="utf-8") as f:
                    self._jobs = json.load(f)
            except Exception:
                self._jobs = {}

    def _save(self) -> None:
        self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.jobs_file, "w", encoding="utf-8") as f:
                json.dump(self._jobs, f, indent=2)
        except Exception:
            pass

    def add_job(
        self,
        name: str,
        interval_seconds: int,
        prompt_instruction: str
    ) -> None:
        """Register a new interval job."""
        with self._lock:
            self._jobs[name] = {
                "name": name,
                "interval_seconds": interval_seconds,
                "prompt": prompt_instruction,
                "last_run": time.time(),
                "run_count": 0
            }
            self._save()

    def remove_job(self, name: str) -> bool:
        with self._lock:
            if name in self._jobs:
                del self._jobs[name]
                self._save()
                return True
        return False

    def record_job_result(self, name: str, result_output: str) -> bool:
        """Process job execution result and detect quiet runs (OpenBot style).

        Returns:
            bool: True if run ended quietly without requiring operator notification.
        """
        is_quiet = (
            "[[no-update]]" in result_output or
            "routine_no_update" in result_output or
            "🔕 [Quiet Run]" in result_output
        )
        with self._lock:
            if name in self._jobs:
                j = self._jobs[name]
                j["last_completed"] = time.time()
                j["last_status"] = "quiet" if is_quiet else "completed"
                j["last_summary"] = "Quiet run (no update needed)" if is_quiet else result_output[:200]
                self._save()
        return is_quiet

    def list_jobs(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._jobs.values())

    def tick(self, executor: Optional[Callable[[str, str], None]] = None) -> List[str]:
        """Check for ready jobs and dispatch them.

        Enforces 'No Catch-Up Stampede': executes at most one run per job tick
        regardless of how long the daemon was offline.
        """
        now = time.time()
        executed_jobs: list[str] = []

        with self._lock:
            for name, j_data in self._jobs.items():
                interval = j_data.get("interval_seconds", 3600)
                last_run = j_data.get("last_run", 0)

                if now - last_run >= interval:
                    # Mark last run immediately to prevent stampedes
                    j_data["last_run"] = now
                    j_data["run_count"] = j_data.get("run_count", 0) + 1
                    executed_jobs.append(name)
                    prompt = j_data.get("prompt", "")

                    if executor:
                        threading.Thread(
                            target=executor,
                            args=(name, prompt),
                            daemon=True
                        ).start()

            if executed_jobs:
                self._save()

        return executed_jobs

    def start_loop(self, executor: Optional[Callable[[str, str], None]] = None) -> None:
        """Start background scheduler loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop_worker, args=(executor,), daemon=True)
        self._thread.start()

    def _loop_worker(self, executor: Optional[Callable[[str, str], None]]) -> None:
        while self._running:
            try:
                self.tick(executor)
            except Exception:
                pass
            time.sleep(10.0)

    def stop(self) -> None:
        self._running = False


# Global scheduler instance
task_scheduler = TaskScheduler()
