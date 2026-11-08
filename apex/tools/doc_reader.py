"""Universal Omni-Modal Document & File Reader.
Capable of reading, extracting text, parsing data, and performing OCR on:
- Text & Code files (.py, .json, .md, .txt, .csv, .yaml, etc.)
- PDF Documents (.pdf) with multi-page extraction & OCR fallback
- Office Documents (.docx, .xlsx) with table and sheet rendering
- Images (.png, .jpg, .jpeg, .webp, .bmp, .gif) with EXIF & Tesseract OCR
- Compressed Archives (.zip, .tar, .tar.gz, .tgz, .bz2, .xz) with TOC and inner reading
- Databases (.db, .sqlite, .sqlite3) with schema extraction and sample previews
- Binary / Executable inspection fallback
"""
from __future__ import annotations

import io
import os
import sqlite3
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import openpyxl
import pypdf
import pytesseract
from docx import Document
from PIL import Image, ExifTags


def resolve_path(path_str: str) -> Path:
    """Resolve relative or tilde path to absolute Path."""
    p = Path(path_str).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    return p.resolve()


def is_binary_file(p: Path, sample_size: int = 8192) -> bool:
    """Check if a file appears to be binary by scanning for null bytes."""
    try:
        with open(p, "rb") as f:
            chunk = f.read(sample_size)
            if b"\x00" in chunk:
                return True
        return False
    except Exception:
        return True


def parse_pdf(p: Path, max_pages: int = 50) -> Tuple[bool, str]:
    """Extract text and metadata from a PDF file."""
    try:
        reader = pypdf.PdfReader(str(p))
        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)

        meta = reader.metadata or {}
        meta_info = []
        if meta.title:
            meta_info.append(f"Title: {meta.title}")
        if meta.author:
            meta_info.append(f"Author: {meta.author}")
        if meta.creator:
            meta_info.append(f"Creator: {meta.creator}")

        output = [
            f"# Document: {p.name} (PDF — {total_pages} total pages)",
            f"Path: {p}",
        ]
        if meta_info:
            output.append("Metadata: " + " | ".join(meta_info))
        output.append("---")

        total_extracted_text = 0
        for i in range(pages_to_read):
            page_text = reader.pages[i].extract_text() or ""
            total_extracted_text += len(page_text.strip())
            output.append(f"### [Halaman {i + 1} / {total_pages}]\n{page_text.strip() or '(Halaman tidak berisi teks teks langsung / gambar saja)'}\n")

        # Fallback to pdftotext CLI if pypdf extracted very little text
        if total_extracted_text < 50:
            try:
                proc = subprocess.run(["pdftotext", str(p), "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
                if proc.stdout and len(proc.stdout.strip()) > total_extracted_text:
                    output = [
                        f"# Document: {p.name} (PDF via Poppler pdftotext)",
                        f"Path: {p}\n---",
                        proc.stdout[:8000]
                    ]
            except Exception:
                pass

        if total_pages > max_pages:
            output.append(f"\n[Catatan: Ditampilkan {pages_to_read} halaman pertama dari total {total_pages} halaman]")

        return True, "\n".join(output)
    except Exception as e:
        return False, f"Gagal membaca PDF '{p.name}': {e}"


def parse_docx(p: Path) -> Tuple[bool, str]:
    """Extract paragraphs and tables from a Word (.docx) document."""
    try:
        doc = Document(str(p))
        output = [
            f"# Document: {p.name} (Word Document)",
            f"Path: {p}\n---"
        ]

        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            if para.style.name.startswith("Heading 1"):
                output.append(f"## {text}")
            elif para.style.name.startswith("Heading 2"):
                output.append(f"### {text}")
            elif para.style.name.startswith("Heading"):
                output.append(f"#### {text}")
            else:
                output.append(text)

        # Extract tables if present
        if doc.tables:
            output.append("\n### [Tabel Dokumen]")
            for t_idx, table in enumerate(doc.tables, 1):
                output.append(f"\nTabel #{t_idx}:")
                for r_idx, row in enumerate(table.rows):
                    row_cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                    output.append("| " + " | ".join(row_cells) + " |")
                    if r_idx == 0:
                        output.append("| " + " | ".join(["---"] * len(row_cells)) + " |")

        return True, "\n".join(output)
    except Exception as e:
        return False, f"Gagal membaca file Word '{p.name}': {e}"


def parse_excel(p: Path, max_rows: int = 40) -> Tuple[bool, str]:
    """Read sheets and rows from an Excel (.xlsx) spreadsheet."""
    try:
        wb = openpyxl.load_workbook(str(p), data_only=True, read_only=True)
        sheet_names = wb.sheetnames

        output = [
            f"# Document: {p.name} (Excel Spreadsheet — {len(sheet_names)} sheet: {', '.join(sheet_names)})",
            f"Path: {p}\n---"
        ]

        for s_name in sheet_names:
            ws = wb[s_name]
            output.append(f"### Sheet: [{s_name}]")
            rows_data = []
            row_count = 0

            for row in ws.iter_rows(values_only=True):
                if not any(v is not None for v in row):
                    continue
                row_count += 1
                if row_count > max_rows:
                    continue
                clean_row = [str(c if c is not None else "") for c in row]
                rows_data.append(clean_row)

            if rows_data:
                # Format as markdown table
                max_cols = max(len(r) for r in rows_data)
                for r_idx, r in enumerate(rows_data):
                    padded = r + [""] * (max_cols - len(r))
                    output.append("| " + " | ".join(padded) + " |")
                    if r_idx == 0:
                        output.append("| " + " | ".join(["---"] * max_cols) + " |")

            if row_count > max_rows:
                output.append(f"\n[... +{row_count - max_rows} baris lainnya pada sheet {s_name}]")
            output.append("")

        return True, "\n".join(output)
    except Exception as e:
        return False, f"Gagal membaca Excel '{p.name}': {e}"


def parse_image(p: Path, ocr: bool = True) -> Tuple[bool, str]:
    """Extract metadata, EXIF properties, and run Tesseract OCR on an image."""
    try:
        img = Image.open(str(p))
        width, height = img.size
        img_format = img.format or p.suffix.lstrip(".").upper()
        mode = img.mode
        file_size_kb = round(p.stat().st_size / 1024, 2)

        output = [
            f"# Berkas Gambar: {p.name}",
            f"Path: {p}",
            f"• Dimensi : {width} x {height} px",
            f"• Format  : {img_format} (Mode: {mode})",
            f"• Ukuran  : {file_size_kb} KB",
        ]

        # Extract EXIF if available
        try:
            exif_data = img._getexif()
            if exif_data:
                exif_summary = []
                for tag_id, value in exif_data.items():
                    tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                    if tag in ["Make", "Model", "DateTime", "Software", "ExposureTime", "FNumber"]:
                        exif_summary.append(f"{tag}: {value}")
                if exif_summary:
                    output.append("• EXIF    : " + " | ".join(exif_summary))
        except Exception:
            pass

        output.append("---")

        # Optical Character Recognition (OCR) via Tesseract
        if ocr:
            try:
                ocr_text = pytesseract.image_to_string(img)
                cleaned_ocr = ocr_text.strip()
                if cleaned_ocr:
                    output.append("### 📝 Teks Terdeteksi di Gambar (OCR Tesseract):\n")
                    output.append(cleaned_ocr)
                else:
                    output.append("### 📝 OCR Tesseract: Tidak ditemukan teks yang terbaca pada gambar ini.")
            except Exception as ocr_err:
                output.append(f"### 📝 OCR Tesseract: {ocr_err}")

        return True, "\n".join(output)
    except Exception as e:
        return False, f"Gagal membuka berkas gambar '{p.name}': {e}"


def parse_archive(p: Path, internal_path: Optional[str] = None) -> Tuple[bool, str]:
    """Inspect contents of zip/tar archives and optionally extract text of an internal file."""
    suf = p.name.lower()
    try:
        if suf.endswith(".zip"):
            with zipfile.ZipFile(str(p), "r") as zf:
                infolist = zf.infolist()
                if internal_path:
                    # Read specific internal file
                    try:
                        content_bytes = zf.read(internal_path)
                        text = content_bytes.decode("utf-8", errors="replace")
                        return True, f"# Internal File: {internal_path} (from {p.name})\n---\n{text[:10000]}"
                    except Exception as ie:
                        return False, f"Gagal membaca berkas '{internal_path}' dalam zip: {ie}"

                # List Table of Contents
                output = [
                    f"# Arsip Zip: {p.name} ({len(infolist)} total berkas)",
                    f"Path: {p}\n---",
                    "| Nama Berkas | Ukuran Asli | Terkompresi | Waktu Modifikasi |",
                    "| --- | --- | --- | --- |"
                ]
                for info in infolist[:60]:
                    size_kb = round(info.file_size / 1024, 1)
                    comp_kb = round(info.compress_size / 1024, 1)
                    dt = f"{info.date_time[0]}-{info.date_time[1]:02d}-{info.date_time[2]:02d}"
                    output.append(f"| `{info.filename}` | {size_kb} KB | {comp_kb} KB | {dt} |")

                if len(infolist) > 60:
                    output.append(f"\n[... +{len(infolist) - 60} berkas lainnya dalam arsip ini]")
                output.append("\n*Tip: Gunakan parameter internal_path='<nama_file>' untuk membaca isi berkas tertentu di dalam zip.*")
                return True, "\n".join(output)

        elif any(suf.endswith(ext) for ext in [".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz"]):
            with tarfile.open(str(p), "r:*") as tf:
                members = tf.getmembers()
                if internal_path:
                    try:
                        f = tf.extractfile(internal_path)
                        if f:
                            text = f.read().decode("utf-8", errors="replace")
                            return True, f"# Internal File: {internal_path} (from {p.name})\n---\n{text[:10000]}"
                        return False, f"Berkas '{internal_path}' bukan berkas reguler."
                    except Exception as ie:
                        return False, f"Gagal membaca '{internal_path}' dalam tar: {ie}"

                output = [
                    f"# Arsip Tar: {p.name} ({len(members)} total entri)",
                    f"Path: {p}\n---",
                    "| Nama Berkas | Ukuran | Tipe |",
                    "| --- | --- | --- |"
                ]
                for m in members[:60]:
                    size_kb = round(m.size / 1024, 1)
                    t_type = "Folder" if m.isdir() else "File"
                    output.append(f"| `{m.name}` | {size_kb} KB | {t_type} |")

                if len(members) > 60:
                    output.append(f"\n[... +{len(members) - 60} entri lainnya]")
                return True, "\n".join(output)

        return False, f"Format arsip tidak didukung: {p.name}"
    except Exception as e:
        return False, f"Gagal membaca arsip '{p.name}': {e}"


def parse_sqlite(p: Path) -> Tuple[bool, str]:
    """Inspect schema and sample records of an SQLite database."""
    try:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

        output = [
            f"# Basis Data SQLite: {p.name} ({len(tables)} tabel terdeteksi)",
            f"Path: {p}\n---"
        ]

        for t_name in tables:
            output.append(f"### Tabel: `{t_name}`")
            # Get table schema
            cursor.execute(f"PRAGMA table_info({t_name});")
            cols_info = cursor.fetchall()
            col_names = [c[1] for c in cols_info]
            col_types = [c[2] for c in cols_info]

            output.append("Kolom: " + ", ".join(f"`{n}` ({t or 'BLOB'})" for n, t in zip(col_names, col_types)))

            # Count rows
            cursor.execute(f"SELECT count(*) FROM {t_name};")
            row_count = cursor.fetchone()[0]
            output.append(f"Total Baris: {row_count}")

            # Sample 3 rows
            if row_count > 0:
                cursor.execute(f"SELECT * FROM {t_name} LIMIT 3;")
                sample_rows = cursor.fetchall()
                output.append("\nContoh Baris:")
                output.append("| " + " | ".join(col_names) + " |")
                output.append("| " + " | ".join(["---"] * len(col_names)) + " |")
                for r in sample_rows:
                    output.append("| " + " | ".join(str(val if val is not None else "")[:50] for val in r) + " |")
            output.append("")

        conn.close()
        return True, "\n".join(output)
    except Exception as e:
        return False, f"Gagal membaca SQLite '{p.name}': {e}"


def read_any_file(
    path: str,
    offset_lines: int = 0,
    limit_lines: int = 1000,
    internal_path: Optional[str] = None,
    ocr: bool = True
) -> Tuple[bool, str]:
    """Master universal file reader dispatcher."""
    p = resolve_path(path)
    if not p.exists():
        return False, f"Berkas tidak ditemukan: {p}"
    if not p.is_file():
        return False, f"Jalur bukan berkas reguler: {p}"

    ext = p.suffix.lower()

    # 1. PDF
    if ext == ".pdf":
        return parse_pdf(p)

    # 2. Word
    if ext in [".docx", ".doc"]:
        return parse_docx(p)

    # 3. Excel
    if ext in [".xlsx", ".xls"]:
        return parse_excel(p)

    # 4. Images
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".ico", ".svg"]:
        return parse_image(p, ocr=ocr)

    # 5. Archives
    if ext in [".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z"]:
        return parse_archive(p, internal_path=internal_path)

    # 6. SQLite Database
    if ext in [".db", ".sqlite", ".sqlite3"]:
        return parse_sqlite(p)

    # 7. Check if binary fallback
    if is_binary_file(p):
        try:
            # Use linux 'file' command to identify exact MIME and description
            proc = subprocess.run(["file", "-b", str(p)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            file_desc = proc.stdout.strip() or "Berkas Biner"
            size_kb = round(p.stat().st_size / 1024, 2)
            with open(p, "rb") as f:
                hex_sample = f.read(128).hex(" ")
            return True, (
                f"# Berkas Biner: {p.name}\n"
                f"Tipe Terdeteksi : {file_desc}\n"
                f"Ukuran          : {size_kb} KB\n"
                f"Cuplikan Hex    :\n`{hex_sample}`"
            )
        except Exception:
            pass

    # 8. Standard Text / Code File
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total = len(lines)
        selected = lines[offset_lines : offset_lines + limit_lines]
        content = "".join(selected)

        header = f"# Berkas Teks/Kode: {p.name} (Baris {offset_lines + 1} s/d {min(offset_lines + limit_lines, total)} dari total {total} baris)\nPath: {p}\n---\n"
        return True, header + content
    except Exception as e:
        return False, f"Gagal membaca teks '{p.name}': {e}"
