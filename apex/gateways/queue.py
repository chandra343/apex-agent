"""Per-Conversation FIFO Queue Engine (OpenClaw Style Anti-Race Condition)."""
from __future__ import annotations

import queue
import threading
import time
from typing import Any, Callable, Dict, Optional


class ConversationQueueManager:
    """Manages dedicated sequential FIFO queues per conversation / chat ID."""

    def __init__(self) -> None:
        self._queues: Dict[str, queue.Queue] = {}
        self._workers: Dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def enqueue(
        self,
        conversation_id: str,
        payload: Any,
        processor: Callable[[Any], None]
    ) -> int:
        """Enqueue a message into the conversation's FIFO queue and ensure worker is running.

        Returns:
            Current queue position (0 = running immediately).
        """
        cid = str(conversation_id)
        with self._lock:
            if cid not in self._queues:
                self._queues[cid] = queue.Queue()

            q = self._queues[cid]
            q.put((payload, processor))
            pos = q.qsize()

            # Ensure worker thread is active for this conversation
            if cid not in self._workers or not self._workers[cid].is_alive():
                worker = threading.Thread(
                    target=self._worker_loop,
                    args=(cid,),
                    name=f"apex-queue-worker-{cid}",
                    daemon=True
                )
                self._workers[cid] = worker
                worker.start()

            return pos

    def _worker_loop(self, cid: str) -> None:
        """Worker thread processing items sequentially for a single conversation."""
        while True:
            with self._lock:
                q = self._queues.get(cid)
                if not q or q.empty():
                    # Clean up idle worker
                    if cid in self._workers:
                        del self._workers[cid]
                    break

            try:
                payload, processor = q.get(timeout=2.0)
                try:
                    processor(payload)
                except Exception as e:
                    print(f"Error processing item in conversation {cid}: {e}")
                finally:
                    q.task_done()
            except queue.Empty:
                pass

    def get_queue_size(self, conversation_id: str) -> int:
        cid = str(conversation_id)
        with self._lock:
            if cid in self._queues:
                return self._queues[cid].qsize()
        return 0


# Global conversation queue manager
conversation_queue = ConversationQueueManager()
