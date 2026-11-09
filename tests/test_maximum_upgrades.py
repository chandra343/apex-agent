"""Comprehensive test suite for Apex Maximum Capabilities:
- AES-256-GCM Encrypted Secret Vault
- Autonomous Tool Self-Healing & Stderr Diagnostics
- Declarative Multi-Step DAG Workflow Orchestrator
- Tiered Cognitive Memory with Time-Decay & Pinned Preferences
- Webhook & Event Router Gateway
"""
import os
import json
import tempfile
import pytest
from pathlib import Path

from apex.security.vault import SecretVault
from apex.tools.vault_ops import manage_vault
from apex.diagnostics.engine import DiagnosticEngine
from apex.workflows.engine import WorkflowEngine
from apex.tools.workflow_ops import manage_workflows
from apex.memory.tiered import TieredMemoryStore
from apex.tools.memory_tiered_ops import manage_cognitive_memory
from apex.prompt_builder import prompt_builder


def test_encrypted_secret_vault():
    with tempfile.TemporaryDirectory() as tmpdir:
        v_path = Path(tmpdir) / "vault.enc"
        s_path = Path(tmpdir) / ".vault_salt"
        vault = SecretVault(vault_path=v_path, salt_path=s_path)

        # 1. Set secret
        ok = vault.set("DATABASE_PASSWORD", "SuperSecretP@ssw0rd!2026", description="Production DB")
        assert ok is True

        # 2. Get secret
        val = vault.get("DATABASE_PASSWORD")
        assert val == "SuperSecretP@ssw0rd!2026"

        # 3. List keys - verify masked and never plain
        keys = vault.list_keys()
        assert len(keys) == 1
        assert keys[0]["key"] == "DATABASE_PASSWORD"
        assert "SuperSecret" not in keys[0]["masked"]
        assert "..." in keys[0]["masked"]

        # 4. Resolve placeholders
        cmd = "psql -U root -p 5432 -d app -W {{vault:DATABASE_PASSWORD}} -c 'SELECT 1;'"
        resolved = vault.resolve_placeholders(cmd)
        assert "SuperSecretP@ssw0rd!2026" in resolved
        assert "{{vault:DATABASE_PASSWORD}}" not in resolved

        # 5. Delete secret
        assert vault.delete("DATABASE_PASSWORD") is True
        assert vault.get("DATABASE_PASSWORD") is None


def test_diagnostic_self_healing_engine():
    diag = DiagnosticEngine()

    # 1. Strip ANSI
    colored = "\x1B[31mERROR:\x1B[0m something went wrong \x1B[2m[trace]\x1B[0m"
    clean = diag.strip_ansi(colored)
    assert clean == "ERROR: something went wrong [trace]"

    # 2. Redact sensitive credentials
    leak_text = "API error using key sk-proj1234567890abcdef1234567890 and Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
    redacted = diag.redact_secrets(leak_text)
    assert "sk-[REDACTED_API_KEY]" in redacted
    assert "sk-proj1234" not in redacted
    assert "Bearer [REDACTED_AUTH_TOKEN]" in redacted

    # 3. Pattern diagnostics
    py_err = "ModuleNotFoundError: No module named 'matplotlib'"
    hint = diag.analyze_failure("run_shell", py_err, exit_code=1)
    assert hint is not None
    assert "pip install matplotlib" in hint

    # 4. Command not found
    sh_err = "bash: line 1: htop: command not found"
    hint2 = diag.analyze_failure("run_shell", sh_err, exit_code=127)
    assert hint2 is not None
    assert "htop" in hint2


def test_dag_workflow_engine():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_workflows.db"
        wf_engine = WorkflowEngine(db_path=db_path)

        # 1. Reject cyclic graph
        cyclic_graph = {
            "nodes": [{"id": "a"}, {"id": "b"}],
            "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}]
        }
        with pytest.raises(ValueError, match="Cycle detected"):
            wf_engine.create_workflow("bad_wf", "Cyclic", cyclic_graph)

        # 2. Create valid DAG workflow
        dag_graph = {
            "nodes": [
                {
                    "id": "fetch_info",
                    "kind": "tool",
                    "tool_name": "list_directory",
                    "params": {"path": "."}
                },
                {
                    "id": "summarize",
                    "kind": "output",
                    "params": {"text": "Directory listing obtained. Total length: ${fetch_info.output}"}
                }
            ],
            "edges": [
                {"from": "fetch_info", "to": "summarize"}
            ]
        }
        res = wf_engine.create_workflow("dir_checker", "Check directory listing", dag_graph)
        assert res["name"] == "dir_checker"
        assert res["nodes"] == 2

        # 3. Execute workflow
        run_res = wf_engine.run_workflow("dir_checker")
        assert run_res["status"] == "completed"
        assert len(run_res["steps"]) == 2
        assert run_res["steps"][0]["node_id"] == "fetch_info"
        assert run_res["steps"][0]["success"] is True

        # Check run status from DB
        status = wf_engine.get_run_status(run_res["run_id"])
        assert status is not None
        assert status["status"] == "completed"


def test_tiered_cognitive_memory():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        mem = TieredMemoryStore(db_path=db_path)

        # 1. Remember fact & rule & preference
        mem.remember("Pengguna lebih menyukai respons dalam Bahasa Indonesia yang ringkas", memory_type="preference", key="lang_pref", importance=9, pinned=True)
        mem.remember("Server database staging berjalan di port 5433", memory_type="fact", key="db_staging", importance=7)
        mem.remember("Jangan pernah melakukan hard delete pada tabel transaksi", memory_type="rule", importance=10, pinned=True)

        # 2. Recall with ranking
        results = mem.recall("staging database", limit=5)
        assert len(results) >= 1
        assert "5433" in results[0]["content"]

        # 3. Pinned memories
        pinned = mem.get_pinned()
        assert len(pinned) == 2
        pinned_keys = {p.get("key") for p in pinned}
        assert "lang_pref" in pinned_keys

        # 4. Forget
        mem.forget("db_staging")
        res_after = mem.recall("5433", limit=5)
        assert len(res_after) == 0


def test_workflow_and_memory_tools():
    # Test manage_vault tool
    v_set = manage_vault("set", key="TEST_KEY", value="secret123", description="Unit test")
    assert "Sukses menyimpan" in v_set
    v_list = manage_vault("list")
    assert "TEST_KEY" in v_list
    assert "secret123" not in v_list  # masked
    manage_vault("delete", key="TEST_KEY")

    # Test manage_cognitive_memory tool
    m_set = manage_cognitive_memory("remember", content="Port redis adalah 6379", memory_type="fact", importance=8)
    assert "tersimpan" in m_set
    m_rec = manage_cognitive_memory("recall", query="redis")
    assert "6379" in m_rec
