"""Unit tests for DocumentImporter (Module F)."""
import json
import pytest
from pathlib import Path
from crawler.app.importer import DocumentImporter


def test_import_from_json_array(tmp_path: Path):
    json_file = tmp_path / "docs.json"
    data = [
        {"document_id": "doc_1", "title": "Doc 1", "content": "Content of document 1"},
        {"document_id": "doc_2", "title": "Doc 2", "content": "Content of document 2"},
    ]
    json_file.write_text(json.dumps(data), encoding="utf-8")

    importer = DocumentImporter()
    docs, stats = importer.import_from_json(json_file)

    assert stats.imported == 2
    assert stats.errors_count == 0
    assert len(docs) == 2
    assert docs[0].document_id == "doc_1"
    assert docs[1].document_id == "doc_2"


def test_import_from_json_single_object(tmp_path: Path):
    json_file = tmp_path / "single.json"
    data = {"title": "Single Doc", "content": "Standalone single document content."}
    json_file.write_text(json.dumps(data), encoding="utf-8")

    importer = DocumentImporter()
    docs, stats = importer.import_from_json(json_file)

    assert stats.imported == 1
    assert len(docs) == 1
    assert docs[0].title == "Single Doc"
    assert docs[0].document_id != ""


def test_import_from_jsonl(tmp_path: Path):
    jsonl_file = tmp_path / "docs.jsonl"
    lines = [
        json.dumps({"document_id": "j1", "title": "Line 1", "content": "First line content"}),
        json.dumps({"document_id": "j2", "title": "Line 2", "content": "Second line content"}),
        "",  # Empty line should be skipped
        json.dumps({"document_id": "j3", "title": "Line 3", "content": "Third line content"}),
    ]
    jsonl_file.write_text("\n".join(lines), encoding="utf-8")

    importer = DocumentImporter()
    docs, stats = importer.import_from_jsonl(jsonl_file)

    assert stats.imported == 3
    assert stats.total_records == 3
    assert len(docs) == 3


def test_import_from_directory(tmp_path: Path):
    # Text file
    txt_file = tmp_path / "intro_to_search.txt"
    txt_file.write_text("Inverted indexes map terms to documents.", encoding="utf-8")

    # Markdown file
    md_file = tmp_path / "ranking.md"
    md_file.write_text("BM25 and TF-IDF are popular ranking algorithms.", encoding="utf-8")

    # HTML file with <title>
    html_file = tmp_path / "page.html"
    html_file.write_text(
        "<html><head><title>SearchX Overview</title></head><body><h1>Header</h1><p>Clean text.</p></body></html>",
        encoding="utf-8",
    )

    importer = DocumentImporter()
    docs, stats = importer.import_from_directory(tmp_path)

    assert stats.imported == 3
    titles = {d.title for d in docs}
    assert "SearchX Overview" in titles
    assert any("Intro To Search" in t for t in titles)
    assert any("Ranking" in t for t in titles)


def test_importer_skips_duplicates(tmp_path: Path):
    json_file = tmp_path / "duplicates.json"
    data = [
        {"document_id": "d1", "title": "Doc 1", "content": "Identical body content"},
        {"document_id": "d2", "title": "Doc 2", "content": "Identical body content"},
    ]
    json_file.write_text(json.dumps(data), encoding="utf-8")

    importer = DocumentImporter()
    docs, stats = importer.import_from_json(json_file)

    assert stats.total_records == 2
    assert stats.imported == 1
    assert stats.duplicates_skipped == 1
    assert len(docs) == 1


def test_importer_handles_missing_and_corrupt_files(tmp_path: Path):
    importer = DocumentImporter()

    # Non-existent file
    docs, stats = importer.import_from_json(tmp_path / "does_not_exist.json")
    assert stats.errors_count == 1
    assert len(docs) == 0

    # Malformed JSON
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("NOT_VALID_JSON{{{", encoding="utf-8")
    docs, stats = importer.import_from_json(corrupt_file)
    assert stats.errors_count == 1
    assert len(docs) == 0
