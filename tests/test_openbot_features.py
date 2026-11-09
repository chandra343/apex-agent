"""Comprehensive Unit Tests for OpenBot-Inspired Superpowers in Project Apex:
1. Dynamic Tool Discovery (tool_search & tool_describe)
2. Shared SQLite Data Lake (manage_data_lake & SQL queries)
3. Quiet Routine Runs (routine_no_update & scheduler status)
4. Anti-Death-Spiral Context Compaction Protection
"""
import pytest
from apex.tools import tool_registry
from apex.tools.tool_discovery import tool_discovery
from apex.tools.data_lake import shared_data_lake
from apex.scheduler.scheduler import task_scheduler
from apex.memory.compaction import context_compactor


def test_tool_search_and_describe():
    # 1. Search for DNS / network tools
    res_search = tool_discovery.search(tool_registry._tools, "dns lookup", max_results=3)
    assert "lookup_dns_records" in res_search
    assert "Hasil Pencarian Tool" in res_search

    # 2. Search for database tools
    res_db = tool_discovery.search(tool_registry._tools, "data lake", max_results=3)
    assert "manage_data_lake" in res_db

    # 3. Describe a tool
    res_desc = tool_discovery.describe(tool_registry._tools, "lookup_dns_records")
    assert "Inspeksi Detail Tool: `lookup_dns_records`" in res_desc
    assert "domain" in res_desc
    assert "Skema JSON Kompatibel LLM" in res_desc

    # 4. Describe non-existent tool with fuzzy suggestion
    res_missing = tool_discovery.describe(tool_registry._tools, "dns_lookup_fake")
    assert "tidak terdaftar" in res_missing or "tidak ditemukan" in res_missing or "Mungkin maksud Anda" in res_missing


def test_shared_data_lake_lifecycle(tmp_path):
    lake = shared_data_lake
    test_table = "test_metrics_table"

    # 1. Create shared table
    create_sql = f"""
        CREATE TABLE IF NOT EXISTS {test_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            latency_ms REAL NOT NULL,
            status_code INTEGER NOT NULL
        )
    """
    res_create = lake.query(create_sql, agent_id="subagent_network")
    assert "berhasil dibuat" in res_create or "berhasil" in res_create.lower()

    # 2. Insert records
    insert_sql = f"""
        INSERT INTO {test_table} (endpoint, latency_ms, status_code)
        VALUES ('https://api.example.com', 42.5, 200),
               ('https://api.target.com', 18.2, 200)
    """
    res_insert = lake.query(insert_sql, agent_id="subagent_network")
    assert "2 baris terpengaruh" in res_insert or "berhasil" in res_insert.lower()

    # 3. Query records with SELECT
    select_sql = f"SELECT endpoint, latency_ms FROM {test_table} ORDER BY latency_ms ASC"
    res_select = lake.query(select_sql, agent_id="subagent_analyst")
    assert "18.2" in res_select
    assert "api.target.com" in res_select
    assert "Hasil Query SQL" in res_select

    # 4. List tables
    res_list = lake.list_tables()
    assert test_table in res_list

    # 5. Describe table
    res_desc = lake.describe_table(test_table)
    assert "latency_ms" in res_desc
    assert "PRIMARY KEY" in res_desc

    # 6. Verify security boundary: forbid ATTACH or PRAGMA escape
    res_unsafe = lake.query("ATTACH DATABASE '/etc/passwd' AS pwn")
    assert "dilarang" in res_unsafe

    # 7. Clean up
    res_drop = lake.query(f"DROP TABLE {test_table}", agent_id="subagent_network")
    assert "berhasil dihapus" in res_drop


def test_quiet_routine_and_scheduler():
    # 1. Execute quiet tool
    ok, out = tool_registry.execute_tool("routine_no_update", {"reason": "All 5 endpoints healthy."})
    assert ok is True
    assert "🔕 [Quiet Run]" in out
    assert "All 5 endpoints healthy" in out

    # 2. Scheduler quiet run tracking
    task_scheduler.add_job("test_probe", interval_seconds=120, prompt_instruction="check uptime")
    is_quiet = task_scheduler.record_job_result("test_probe", out)
    assert is_quiet is True

    # 3. Verify job listing shows quiet status
    jobs = {j["name"]: j for j in task_scheduler.list_jobs()}
    assert "test_probe" in jobs
    assert jobs["test_probe"].get("last_status") == "quiet"

    # Cleanup
    task_scheduler.remove_job("test_probe")


def test_anti_death_spiral_compaction():
    compactor = context_compactor
    session_id = "test_loop_session"
    compactor.reset_budget(session_id)

    # Fabricate a message list where messages are bulky
    messages = [
        {"role": "system", "content": "You are Apex."},
        {"role": "user", "content": "Run analysis turn 1"},
        {"role": "assistant", "content": "Executing...", "tool_calls": [{"function": {"name": "run_shell"}}]},
        {"role": "tool", "name": "run_shell", "content": "output" * 200},
    ] * 6  # 24 messages

    # Run 1: Normal compaction
    compacted1, saved1 = compactor.compact(messages, session_id=session_id)
    assert len(compacted1) < len(messages)

    # Force simulated repeated ineffective compaction
    compactor._ineffective_counts[session_id] = 2
    assert compactor.is_stopped(session_id) is True

    # Run 2: Anti-Death-Spiral kicks in with Emergency Prune
    compacted2, saved2 = compactor.compact(messages, session_id=session_id)
    assert any("[Emergency Context Pruning" in str(m.get("content", "")) for m in compacted2)
    # Counter must be reset after emergency prune
    assert compactor.is_stopped(session_id) is False
