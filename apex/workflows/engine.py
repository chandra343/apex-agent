"""Autonomous DAG Workflow Orchestrator & Execution Engine (OpenBot Style)."""
from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from apex.config import APEX_DIR


WORKFLOWS_DB = APEX_DIR / "workflows.db"


class WorkflowEngine:
    """Enterprise DAG Workflow & Automation Engine for Project Apex."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or WORKFLOWS_DB
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    graph_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    run_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed', 'stopped')),
                    trigger_source TEXT NOT NULL DEFAULT 'manual',
                    started_at REAL NOT NULL,
                    completed_at REAL,
                    error TEXT,
                    context_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_step_logs (
                    step_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
                    input_data TEXT,
                    output_data TEXT,
                    error TEXT,
                    elapsed_seconds REAL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES workflow_runs(run_id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def create_workflow(
        self,
        name: str,
        description: str,
        graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or update a declarative DAG workflow."""
        name = name.strip()
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Validate nodes and edges
        if not nodes:
            raise ValueError("Workflow must contain at least one node.")

        node_ids = {n["id"] for n in nodes if "id" in n}
        if len(node_ids) != len(nodes):
            raise ValueError("All node IDs in workflow must be unique.")

        for edge in edges:
            if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
                raise ValueError(f"Invalid edge: '{edge.get('from')}' -> '{edge.get('to')}'")

        # Cycle detection
        adj: Dict[str, List[str]] = {nid: [] for nid in node_ids}
        for edge in edges:
            adj[edge["from"]].append(edge["to"])

        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def is_cyclic(v: str) -> bool:
            visited.add(v)
            rec_stack.add(v)
            for neighbor in adj.get(v, []):
                if neighbor not in visited:
                    if is_cyclic(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(v)
            return False

        for nid in node_ids:
            if nid not in visited:
                if is_cyclic(nid):
                    raise ValueError("Cycle detected in workflow graph! Workflows must be Directed Acyclic Graphs (DAG).")

        now = time.time()
        workflow_id = f"wf_{uuid.uuid4().hex[:10]}"
        graph_json = json.dumps(graph, indent=2)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO workflows (workflow_id, name, description, graph_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    description = excluded.description,
                    graph_json = excluded.graph_json,
                    updated_at = excluded.updated_at
            """, (workflow_id, name, description, graph_json, now, now))
            conn.commit()

        return {"workflow_id": workflow_id, "name": name, "nodes": len(nodes), "edges": len(edges)}

    def list_workflows(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT workflow_id, name, description, created_at, updated_at FROM workflows ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]

    def get_workflow(self, identifier: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM workflows WHERE workflow_id = ? OR name = ?",
                (identifier, identifier)
            ).fetchone()
            if not row:
                return None
            res = dict(row)
            res["graph"] = json.loads(res["graph_json"])
            return res

    def delete_workflow(self, identifier: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM workflows WHERE workflow_id = ? OR name = ?", (identifier, identifier))
            conn.commit()
            return cur.rowcount > 0

    def run_workflow(
        self,
        identifier: str,
        input_params: Optional[Dict[str, Any]] = None,
        trigger_source: str = "manual"
    ) -> Dict[str, Any]:
        """Execute all nodes in the DAG topologically with parameter interpolation."""
        wf = self.get_workflow(identifier)
        if not wf:
            raise ValueError(f"Workflow '{identifier}' not found.")

        graph = wf["graph"]
        nodes: List[Dict[str, Any]] = graph.get("nodes", [])
        edges: List[Dict[str, Any]] = graph.get("edges", [])

        run_id = f"run_{uuid.uuid4().hex[:12]}"
        now = time.time()
        context: Dict[str, Any] = {"input": input_params or {}, "nodes": {}}

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO workflow_runs (run_id, workflow_id, status, trigger_source, started_at, context_json)
                VALUES (?, ?, 'running', ?, ?, ?)
            """, (run_id, wf["workflow_id"], trigger_source, now, json.dumps(context)))
            conn.commit()

        # Build in-degree map and adjacency
        node_map = {n["id"]: n for n in nodes}
        in_degree: Dict[str, int] = {n["id"]: 0 for n in nodes}
        outgoing: Dict[str, List[Dict[str, Any]]] = {n["id"]: [] for n in nodes}

        for e in edges:
            in_degree[e["to"]] += 1
            outgoing[e["from"]].append(e)

        # Queue for nodes with in_degree == 0
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        step_results: List[Dict[str, Any]] = []
        workflow_failed = False
        workflow_error = ""

        # Import tool registry inside execution
        from apex.tools import tool_registry

        while queue and not workflow_failed:
            curr_id = queue.pop(0)
            node = node_map[curr_id]
            kind = node.get("kind", "tool")

            # Check if this node was skipped due to conditional branch
            if context["nodes"].get(curr_id, {}).get("skipped"):
                continue

            step_id = f"step_{uuid.uuid4().hex[:8]}"
            step_start = time.time()

            # Interpolate parameters
            interpolated_params = self._interpolate_params(node.get("params", {}), context)

            step_output = ""
            step_success = True
            step_error = None
            branch_taken = None

            try:
                if kind == "tool":
                    t_name = node.get("tool_name", "")
                    step_success, step_output = tool_registry.execute_tool(t_name, interpolated_params)
                    if not step_success:
                        step_error = f"Tool '{t_name}' execution failed: {step_output}"
                elif kind == "agent":
                    from apex.agent import default_agent
                    prompt = interpolated_params.get("prompt", "")
                    step_output = default_agent.run(prompt, session_id=f"wf_{run_id}")
                    step_success = True
                elif kind == "condition":
                    # Evaluate condition expression
                    expr = interpolated_params.get("expression", "True")
                    eval_globals = {"context": context, "len": len, "str": str, "int": int, "bool": bool}
                    eval_locals = {k: v.get("output") for k, v in context["nodes"].items()}
                    cond_val = bool(eval(expr, eval_globals, eval_locals))
                    branch_taken = "yes" if cond_val else "no"
                    step_output = f"Condition evaluated to: {cond_val} (Branch: {branch_taken})"
                    step_success = True
                elif kind == "output":
                    step_output = interpolated_params.get("text", "")
                    step_success = True
                else:
                    step_error = f"Unsupported node kind: '{kind}'"
                    step_success = False

            except Exception as ex:
                step_success = False
                step_error = str(ex)

            step_elapsed = round(time.time() - step_start, 3)

            # Record step in context
            context["nodes"][curr_id] = {
                "output": step_output,
                "success": step_success,
                "error": step_error,
                "branch": branch_taken
            }

            # Record step log in DB
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO workflow_step_logs (
                        step_id, run_id, node_id, kind, status, input_data, output_data, error, elapsed_seconds, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    step_id, run_id, curr_id, kind,
                    "completed" if step_success else "failed",
                    json.dumps(interpolated_params),
                    str(step_output)[:2000],
                    step_error,
                    step_elapsed,
                    time.time()
                ))
                conn.commit()

            step_results.append({
                "node_id": curr_id,
                "kind": kind,
                "success": step_success,
                "output": step_output,
                "error": step_error,
                "elapsed": step_elapsed
            })

            if not step_success:
                workflow_failed = True
                workflow_error = step_error or f"Node '{curr_id}' failed."
                break

            # Enqueue downstream nodes based on branch condition
            for edge in outgoing.get(curr_id, []):
                target_id = edge["to"]
                edge_branch = edge.get("branch")

                # If this is a conditional edge and branch doesn't match, skip downstream node
                if branch_taken and edge_branch and edge_branch != branch_taken:
                    context["nodes"].setdefault(target_id, {})["skipped"] = True
                    continue

                in_degree[target_id] -= 1
                if in_degree[target_id] == 0:
                    queue.append(target_id)

        run_completed_at = time.time()
        final_status = "failed" if workflow_failed else "completed"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE workflow_runs
                SET status = ?, completed_at = ?, error = ?, context_json = ?
                WHERE run_id = ?
            """, (final_status, run_completed_at, workflow_error, json.dumps(context), run_id))
            conn.commit()

        return {
            "run_id": run_id,
            "workflow_name": wf["name"],
            "status": final_status,
            "error": workflow_error,
            "steps": step_results,
            "total_elapsed": round(run_completed_at - now, 3)
        }

    def get_run_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            run = conn.execute("SELECT * FROM workflow_runs WHERE run_id = ?", (run_id,)).fetchone()
            if not run:
                return None
            steps = conn.execute(
                "SELECT * FROM workflow_step_logs WHERE run_id = ? ORDER BY created_at ASC", (run_id,)
            ).fetchall()
            res = dict(run)
            res["steps"] = [dict(s) for s in steps]
            return res

    def _interpolate_params(self, params: Any, context: Dict[str, Any]) -> Any:
        """Recursively interpolate ${node_id.output} and ${input.key} in params."""
        if isinstance(params, str):
            def repl(m: re.Match) -> str:
                path = m.group(1).split(".")
                root = path[0]
                if root == "input":
                    val = context.get("input", {})
                    for p in path[1:]:
                        val = val.get(p, "") if isinstance(val, dict) else ""
                    return str(val)
                elif root in context.get("nodes", {}):
                    node_data = context["nodes"][root]
                    if len(path) == 1 or path[1] == "output":
                        return str(node_data.get("output", ""))
                    elif path[1] == "error":
                        return str(node_data.get("error", ""))
                return m.group(0)

            return re.sub(r"\$\{([a-zA-Z0-9_\.]+)\}", repl, params)

        elif isinstance(params, dict):
            return {k: self._interpolate_params(v, context) for k, v in params.items()}
        elif isinstance(params, list):
            return [self._interpolate_params(item, context) for item in params]
        return params


# Global Workflow Engine instance
workflow_engine = WorkflowEngine()
