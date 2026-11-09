"""Multi-Agent Swarm Orchestrator Tool for Apex."""
from __future__ import annotations

import json
from typing import Any, Dict, List
from apex.subagents.swarm import swarm_dispatcher


def _default_runner(system_prompt: str, user_prompt: str) -> str:
    """Execute a task turn using the global Apex agent."""
    from apex.agent import default_agent
    from apex.router.fallback import fallback_router

    active_model = fallback_router.get_active_model()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    res = default_agent._call_llm_with_fallback(
        messages=messages,
        active_model=active_model,
        tools_defs=[]
    )
    if res.get("success"):
        return res.get("content", "").strip() or "(Sub-agent selesai tanpa output)"
    return f"Gagal mengeksekusi sub-agent: {res.get('error', 'Unknown error')}"


def dispatch_subagents(tasks: List[Dict[str, str]] | str) -> str:
    """Dispatch a batch of specialized sub-agent workers concurrently in parallel.

    Args:
        tasks: List of task definitions, each with 'role' ('researcher', 'coder', 'tester', 'auditor')
               and 'task' (description of the task). Can also be a JSON-encoded string.

    Returns:
        Structured Markdown summary of execution results across all sub-agents.
    """
    if isinstance(tasks, str):
        try:
            tasks = json.loads(tasks)
        except Exception:
            tasks = [{"role": "researcher", "task": tasks}]

    if not isinstance(tasks, list) or not tasks:
        return "❌ Format tugas tidak valid. Berikan list of dict dengan role dan task."

    results = swarm_dispatcher.dispatch(tasks, _default_runner)

    report_lines = [
        f"👥 **Laporan Hasil Multi-Agent Swarm ({len(results)} Sub-Agents)** 🚀\n"
    ]

    for idx, r in enumerate(results, 1):
        role = r.get("role", "worker").upper()
        worker_id = r.get("worker_id", f"agent-{idx}")
        success = r.get("success", False)
        icon = "✅" if success else "❌"
        latency = r.get("latency_seconds", 0)
        output = r.get("output", "")

        report_lines.append(
            f"### {icon} [{worker_id}] Role: `{role}` (⏱ {latency}s)\n"
            f"{output}\n"
        )

    return "\n---\n".join(report_lines)
