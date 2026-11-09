"""Tools for managing and triggering declarative DAG Workflows in Project Apex."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional
from apex.workflows.engine import workflow_engine


def manage_workflows(
    action: str,
    name: str = "",
    description: str = "",
    graph: Optional[Dict[str, Any]] = None,
    input_params: Optional[Dict[str, Any]] = None,
    run_id: str = ""
) -> str:
    """Manage and orchestrate multi-step DAG Workflows (Pipelines) in Project Apex.

    Args:
        action: One of 'create', 'run', 'status', 'list', 'delete'.
        name: Name or ID of the workflow.
        description: Description of the workflow (for 'create').
        graph: Dict containing 'nodes' and 'edges' defining the DAG (for 'create').
        input_params: Optional dictionary of runtime inputs (for 'run').
        run_id: Specific execution run ID (for 'status').

    Returns:
        Structured result string or Markdown execution report.
    """
    act = action.strip().lower()

    if act == "create":
        if not name or not graph:
            return "❌ Parameter 'name' dan 'graph' (nodes & edges) wajib diisi untuk membuat workflow."
        try:
            res = workflow_engine.create_workflow(name, description, graph)
            return (
                f"✅ **Workflow Berhasil Dibuat / Diperbarui**:\n"
                f"- **Nama**: `{res['name']}`\n"
                f"- **ID**: `{res['workflow_id']}`\n"
                f"- **Total Nodes**: {res['nodes']}\n"
                f"- **Total Edges**: {res['edges']}"
            )
        except Exception as e:
            return f"❌ Gagal membuat workflow: {e}"

    elif act == "run":
        if not name:
            return "❌ Parameter 'name' (nama atau ID workflow) wajib diisi untuk menjalankan workflow."
        try:
            res = workflow_engine.run_workflow(name, input_params=input_params, trigger_source="tool")
            status_icon = "✅" if res["status"] == "completed" else "❌"
            step_lines = []
            for s in res.get("steps", []):
                s_icon = "✔" if s["success"] else "✖"
                s_out = str(s.get("output", ""))[:120].replace("\n", " ")
                step_lines.append(f"  - {s_icon} Node `{s['node_id']}` ({s['kind']}): {s_out} ({s['elapsed']}s)")

            return (
                f"{status_icon} **Eksekusi Workflow `{res['workflow_name']}` Selesai**:\n"
                f"- **Run ID**: `{res['run_id']}`\n"
                f"- **Status**: `{res['status']}`\n"
                f"- **Total Durasi**: {res['total_elapsed']}s\n"
                f"### 📋 Log Langkah:\n" + "\n".join(step_lines)
            )
        except Exception as e:
            return f"❌ Gagal mengeksekusi workflow: {e}"

    elif act == "status":
        if not run_id:
            return "❌ Parameter 'run_id' wajib diisi untuk melihat status eksekusi."
        st = workflow_engine.get_run_status(run_id)
        if not st:
            return f"⚠️ Run ID `{run_id}` tidak ditemukan."

        status_icon = "✅" if st["status"] == "completed" else "❌" if st["status"] == "failed" else "⏳"
        step_lines = []
        for s in st.get("steps", []):
            s_icon = "✔" if s["status"] == "completed" else "✖"
            step_lines.append(f"  - {s_icon} `[{s['node_id']}]` ({s['kind']}) Status: {s['status']} ({s.get('elapsed_seconds', 0)}s)")

        return (
            f"{status_icon} **Status Workflow Run `{run_id}`**:\n"
            f"- **Workflow ID**: `{st['workflow_id']}`\n"
            f"- **Status**: `{st['status']}`\n"
            f"- **Trigger**: `{st['trigger_source']}`\n"
            f"### 📋 Detail Step Execution:\n" + "\n".join(step_lines)
        )

    elif act == "list":
        wfs = workflow_engine.list_workflows()
        if not wfs:
            return "📭 Belum ada DAG workflow yang terdaftar di sistem Apex."

        rows = [
            "| Nama Workflow | ID | Deskripsi | Diperbarui |",
            "| --- | --- | --- | --- |"
        ]
        import datetime
        for w in wfs:
            dt = datetime.datetime.fromtimestamp(w["updated_at"]).strftime("%Y-%m-%d %H:%M")
            rows.append(f"| **`{w['name']}`** | `{w['workflow_id']}` | {w.get('description') or '-'} | {dt} |")
        return "🔀 **Apex DAG Workflows Catalog**:\n\n" + "\n".join(rows)

    elif act == "delete":
        if not name:
            return "❌ Parameter 'name' wajib diisi untuk menghapus workflow."
        ok = workflow_engine.delete_workflow(name)
        if ok:
            return f"🗑️ Workflow `{name}` berhasil dihapus."
        return f"⚠️ Workflow `{name}` tidak ditemukan."

    else:
        return f"❌ Action `{action}` tidak dikenal. Gunakan: 'create', 'run', 'status', 'list', atau 'delete'."
