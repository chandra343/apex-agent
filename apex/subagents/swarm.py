"""Unbounded Sub-Agent Swarm Engine (Massive Parallel Delegation)."""
from __future__ import annotations

import concurrent.futures
import time
from typing import Any, Callable, Dict, List, Optional
from apex.subagents.roles import SWARM_ROLES


class SubAgentWorker:
    """An isolated sub-agent worker with a specialized role."""

    def __init__(
        self,
        worker_id: str,
        role: str,
        agent_runner: Callable[[str, str], str]
    ) -> None:
        self.worker_id = worker_id
        self.role = role
        self.agent_runner = agent_runner
        self.system_prompt = SWARM_ROLES.get(role, SWARM_ROLES["coder"])

    def execute_task(self, task_instruction: str) -> Dict[str, Any]:
        start_t = time.time()
        try:
            full_prompt = f"Role: {self.role.upper()}\n{task_instruction}"
            result_text = self.agent_runner(self.system_prompt, full_prompt)
            latency = round(time.time() - start_t, 2)
            return {
                "worker_id": self.worker_id,
                "role": self.role,
                "success": True,
                "output": result_text,
                "latency_seconds": latency
            }
        except Exception as e:
            latency = round(time.time() - start_t, 2)
            return {
                "worker_id": self.worker_id,
                "role": self.role,
                "success": False,
                "output": f"Sub-agent execution error: {e}",
                "latency_seconds": latency
            }


class SwarmDispatcher:
    """Dispatches dozens of sub-agent tasks concurrently in a thread pool."""

    def __init__(self, default_workers: int = 10) -> None:
        self.default_workers = default_workers

    def dispatch(
        self,
        task_list: List[Dict[str, str]],
        agent_runner: Callable[[str, str], str],
        max_workers: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Run tasks in parallel across the sub-agent swarm.

        task_list format: [{"role": "researcher", "task": "Search X"}, ...]
        """
        workers_count = max_workers or min(len(task_list), self.default_workers)
        results: list[dict[str, Any]] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_count) as executor:
            future_to_task = {}
            for idx, item in enumerate(task_list, 1):
                role = item.get("role", "coder")
                task = item.get("task", "")
                worker = SubAgentWorker(f"agent-{idx}", role, agent_runner)
                fut = executor.submit(worker.execute_task, task)
                future_to_task[fut] = item

            for fut in concurrent.futures.as_completed(future_to_task):
                try:
                    res = fut.result()
                    results.append(res)
                except Exception as e:
                    results.append({"success": False, "output": str(e)})

        return results


# Global swarm dispatcher instance
swarm_dispatcher = SwarmDispatcher()
