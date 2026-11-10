"""Unit tests for AST Semantic Code Graph and Symbol Explorer."""
import pytest
from apex.tools.code_graph import CodeGraphEngine, query_code_graph


def test_code_graph_index_and_symbols(tmp_path):
    # Create sample python files
    py_file = tmp_path / "sample_service.py"
    py_file.write_text('''
"""Sample service module for testing AST graph."""

class OrderProcessor:
    """Manages order transactions."""
    def process_order(self, order_id: str) -> bool:
        return True

async def calculate_tax(amount: float) -> float:
    """Calculate tax for transaction."""
    return amount * 0.11
''')

    engine = CodeGraphEngine(str(tmp_path))
    stats = engine.index_directory()
    assert stats["indexed_files"] == 1
    assert stats["total_symbols"] >= 2

    # Outline
    outline = engine.inspect_file("sample_service.py")
    assert outline["symbols_count"] >= 2
    sym_names = [s["name"] for s in outline["symbols"]]
    assert "OrderProcessor" in sym_names
    assert "calculate_tax" in sym_names

    # Find symbol
    matches = engine.find_symbol("OrderProcessor")
    assert len(matches) == 1
    assert matches[0]["type"] == "class"

    # Find inner method
    m_matches = engine.find_symbol("process_order")
    assert len(m_matches) == 1
    assert m_matches[0]["type"] == "method"


def test_query_code_graph_tool_wrapper(tmp_path):
    py_file = tmp_path / "api.py"
    py_file.write_text('''
def health_check():
    return {"status": "ok"}
''')

    # Test index action
    res_index = query_code_graph("index", path=str(tmp_path))
    assert "Codebase Indexing Complete" in res_index

    # Test outline action
    res_outline = query_code_graph("outline", target="api.py", path=str(tmp_path))
    assert "health_check" in res_outline

    # Test find action
    res_find = query_code_graph("find", target="health_check", path=str(tmp_path))
    assert "health_check" in res_find
