"""Unit tests for Universal Omni-Modal Document Reader."""
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from docx import Document
import openpyxl
from PIL import Image, ImageDraw

from apex.tools.doc_reader import (
    read_any_file, parse_docx, parse_excel, parse_archive, parse_sqlite, parse_image
)
from apex.tools.file_ops import read_file
from apex.tools import tool_registry


def test_read_text_file():
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("Line 1: Hello Apex\nLine 2: Sovereign Agent\nLine 3: End of text")
        tmp_path = f.name

    try:
        ok, content = read_any_file(tmp_path)
        assert ok is True
        assert "Hello Apex" in content
        assert "Sovereign Agent" in content

        # Test through standard read_file
        ok2, content2 = read_file(tmp_path)
        assert ok2 is True
        assert "Hello Apex" in content2
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_read_docx():
    with tempfile.TemporaryDirectory() as td:
        docx_path = Path(td) / "sample.docx"
        doc = Document()
        doc.add_heading("Apex Architecture", level=1)
        doc.add_paragraph("This is an omni-modal sovereign hybrid system.")
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Col A"
        table.cell(0, 1).text = "Col B"
        table.cell(1, 0).text = "Val 1"
        table.cell(1, 1).text = "Val 2"
        doc.save(str(docx_path))

        ok, content = read_any_file(str(docx_path))
        assert ok is True
        assert "sample.docx (Word Document)" in content
        assert "Apex Architecture" in content
        assert "omni-modal sovereign hybrid system" in content
        assert "Col A" in content


def test_read_excel():
    with tempfile.TemporaryDirectory() as td:
        xlsx_path = Path(td) / "metrics.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Performance"
        ws.append(["Metric", "Target", "Status"])
        ws.append(["Latency", "< 2.0s", "Achieved"])
        ws.append(["Uptime", "99.9%", "Achieved"])
        wb.save(str(xlsx_path))

        ok, content = read_any_file(str(xlsx_path))
        assert ok is True
        assert "metrics.xlsx (Excel Spreadsheet" in content
        assert "Sheet: [Performance]" in content
        assert "Latency" in content
        assert "Achieved" in content


def test_read_sqlite():
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "test.db"
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, role TEXT)")
        cur.execute("INSERT INTO users VALUES (1, 'chandra', 'operator')")
        cur.execute("INSERT INTO users VALUES (2, 'apex', 'sovereign_agent')")
        conn.commit()
        conn.close()

        ok, content = read_any_file(str(db_path))
        assert ok is True
        assert "Basis Data SQLite: test.db" in content
        assert "Tabel: `users`" in content
        assert "chandra" in content
        assert "sovereign_agent" in content


def test_read_archive():
    with tempfile.TemporaryDirectory() as td:
        zip_path = Path(td) / "bundle.zip"
        with zipfile.ZipFile(str(zip_path), "w") as zf:
            zf.writestr("notes.txt", "Top secret mission directives.")
            zf.writestr("subfolder/config.json", '{"mode": "autonomous"}')

        # List archive table of contents
        ok, content = read_any_file(str(zip_path))
        assert ok is True
        assert "Arsip Zip: bundle.zip" in content
        assert "notes.txt" in content
        assert "subfolder/config.json" in content

        # Read inner file without extraction
        ok2, content2 = read_any_file(str(zip_path), internal_path="notes.txt")
        assert ok2 is True
        assert "Top secret mission directives" in content2


def test_read_image_metadata():
    with tempfile.TemporaryDirectory() as td:
        img_path = Path(td) / "test.png"
        img = Image.new("RGB", (200, 100), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((10, 10), "APEX OCR TEST", fill=(255, 255, 0))
        img.save(str(img_path))

        ok, content = parse_image(img_path, ocr=True)
        assert ok is True
        assert "Berkas Gambar: test.png" in content
        assert "Dimensi" in content
        assert "200 x 100" in content


def test_tool_registry_registration():
    all_defs = tool_registry.get_all_tool_definitions()
    tool_names = [t["function"]["name"] for t in all_defs]
    assert "read_document" in tool_names
    assert "read_file" in tool_names
