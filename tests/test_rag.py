"""Unit tests for Local RAG Engine & Knowledge Base Tools."""
import pytest
from apex.memory.rag import LocalRAGEngine
from apex.tools.memory_ops import remember_fact, recall_memory, index_knowledge_base, search_knowledge_base


@pytest.fixture
def temp_rag(tmp_path):
    db_file = tmp_path / "test_kb.db"
    return LocalRAGEngine(db_path=db_file)


def test_chunking(temp_rag):
    sample_text = "# Header 1\nLine 1\nLine 2\n## Subheader\nLine 3\nLine 4\n" * 15
    chunks = temp_rag.chunk_text(sample_text, chunk_size_lines=20, overlap=5)
    assert len(chunks) > 1
    assert "heading" in chunks[0]
    assert "content" in chunks[0]


def test_index_and_search(temp_rag, tmp_path):
    doc_dir = tmp_path / "docs"
    doc_dir.mkdir()
    (doc_dir / "architecture.md").write_text("# Arsitektur Sistem\nApex menggunakan sistem Multi-Provider Router dan ReAct Loop.")
    (doc_dir / "guide.py").write_text("def start_pipeline():\n    # Memulai pipeline pemrosesan dokumen omni-modal\n    pass")

    res = temp_rag.index_path(str(doc_dir))
    assert res["success"] is True
    assert res["files_indexed"] == 2
    assert res["chunks_created"] >= 2

    # Search
    search_res = temp_rag.search("Multi-Provider")
    assert len(search_res) > 0
    assert "Arsitektur Sistem" in search_res[0]["content"]


def test_memory_store_and_recall():
    fact_res = remember_fact("Host gateway berjalan pada port 8000", category="network", tags="web,port")
    assert "Memori Tersimpan" in fact_res

    recall_res = recall_memory("port 8000")
    assert "Hasil Penelusuran Memori" in recall_res
    assert "8000" in recall_res
