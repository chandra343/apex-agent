"""Crash-Resilient Durable Jobs Engine (Zeline Style)."""
from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from apex.config import DATA_DIR

DURABLE_DB = DATA_DIR / "durable_jobs.db"


class DurableJobQueue:
    """Provides persistent job records with lease claims surviving reboots."""

    def __init__(self, lease_duration: float = 300.0) -> None:
        self.lease_duration = lease_duration
        self._init_db()

    def _init_db(self) -> None:
        DURABLE_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DURABLE_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS durable_jobs (
                    job_id TEXT PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    created_at REAL NOT NULL,
                    claimed_until REAL,
                    claimed_by TEXT
                )
            """)

    def submit_job(self, task_name: str, payload_str: str) -> str:
        """Enqueue a durable background job."""
        job_id = str(uuid.uuid4())[:8]
        with sqlite3.connect(DURABLE_DB) as conn:
            conn.execute("""
                INSERT INTO durable_jobs (job_id, task_name, payload, status, created_at)
                VALUES (?, ?, ?, 'pending', ?)
            """, (job_id, task_name, payload_str, time.time()))
            conn.commit()
        return job_id

    def claim_next_job(self, worker_id: str) -> Optional[Tuple[str, str, str]]:
        """Atomically claim the next pending or expired-lease job."""
        now = time.time()
        lease_until = now + self.lease_duration

        with sqlite3.connect(DURABLE_DB) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # Find candidate job
            cur.execute("""
                SELECT job_id, task_name, payload
                FROM durable_jobs
                WHERE status = 'pending' OR (status = 'running' AND claimed_until < ?)
                ORDER BY created_at ASC
                LIMIT 1
            """, (now,))
            row = cur.fetchone()
            if not row:
                return None

            job_id = row["job_id"]
            # Claim lease
            cur.execute("""
                UPDATE durable_jobs
                SET status = 'running', claimed_until = ?, claimed_by = ?
                WHERE job_id = ?
            """, (lease_until, worker_id, job_id))
            conn.commit()

            return row["job_id"], row["task_name"], row["payload"]

    def complete_job(self, job_id: str, result_str: str) -> None:
        with sqlite3.connect(DURABLE_DB) as conn:
            conn.execute("""
                UPDATE durable_jobs
                SET status = 'completed', result = ?, claimed_until = NULL
                WHERE job_id = ?
            """, (result_str, job_id))
            conn.commit()

    def fail_job(self, job_id: str, error_str: str) -> None:
        with sqlite3.connect(DURABLE_DB) as conn:
            conn.execute("""
                UPDATE durable_jobs
                SET status = 'failed', result = ?, claimed_until = NULL
                WHERE job_id = ?
            """, (error_str, job_id))
            conn.commit()

    def list_jobs(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(DURABLE_DB) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM durable_jobs ORDER BY created_at DESC LIMIT 50")
            return [dict(r) for r in cur.fetchall()]


# Global durable queue
durable_queue = DurableJobQueue()
