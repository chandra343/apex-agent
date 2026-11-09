"""Unit tests for Multi-Agent Swarm Orchestrator Tool."""
import pytest
from unittest.mock import patch
from apex.tools.swarm_ops import dispatch_subagents


def test_dispatch_subagents_mocked():
    mock_results = [
        {"worker_id": "agent-1", "role": "researcher", "success": True, "output": "Hasil riset arsitektur.", "latency_seconds": 1.2},
        {"worker_id": "agent-2", "role": "coder", "success": True, "output": "Implementasi kode selesai.", "latency_seconds": 2.1}
    ]

    with patch("apex.subagents.swarm.swarm_dispatcher.dispatch", return_value=mock_results):
        res = dispatch_subagents([
            {"role": "researcher", "task": "Riset kebutuhan sistem"},
            {"role": "coder", "task": "Buat implementasi"}
        ])

        assert "Laporan Hasil Multi-Agent Swarm" in res
        assert "RESEARCHER" in res
        assert "Hasil riset arsitektur" in res
        assert "CODER" in res
        assert "Implementasi kode selesai" in res


def test_dispatch_subagents_invalid_input():
    res = dispatch_subagents([])
    assert "tidak valid" in res.lower()
