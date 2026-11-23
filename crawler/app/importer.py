"""
Manual Document Importer for SearchX.
Enables offline document ingestion from JSON, JSONL, and local directories.
Complies with PROJECT_CONTEXT.md Module F.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import Document, DocumentStatus
from .text_processor import TextProcessor


@dataclass
class ImportStats:
    """Summary statistics for an import operation."""
    total_records: int = 0
    imported: int = 0
    duplicates_skipped: int = 0
    errors_count: int = 0
    errors: List[str] = field(default_factory=list)


class DocumentImporter:
    """Imports documents from local files and directories into canonical Document objects."""

    def __init__(self, text_processor: Optional[TextProcessor] = None) -> None:
        self.text_processor = text_processor or TextProcessor()

    def import_from_json(self, file_path: str | Path) -> Tuple[List[Document], ImportStats]:
        """Import document(s) from a JSON file (single object or list of objects)."""
        stats = ImportStats()
        documents: List[Document] = []
        path = Path(file_path)

        if not path.exists():
            stats.errors.append(f"File not found: {path}")
            stats.errors_count += 1
            return documents, stats

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            stats.errors.append(f"JSON decode error in {path}: {e}")
            stats.errors_count += 1
            return documents, stats

        records = data if isinstance(data, list) else [data]
        stats.total_records = len(records)
        seen_hashes: Set[str] = set()

        for idx, item in enumerate(records):
            if not isinstance(item, dict):
                stats.errors.append(f"Record at index {idx} is not a JSON object")
                stats.errors_count += 1
                continue
            try:
                # If document_id is missing, generate deterministic hash
                doc_id = str(item.get("document_id", "")).strip()
                title = str(item.get("title", "")).strip()
                content = str(item.get("content", ""))

                if not doc_id:
                    doc_id = f"import_json_{path.stem}_{idx}"
                if not title:
                    title = f"Document {doc_id}"

                doc = Document.create(
                    document_id=doc_id,
                    title=title,
                    content=content,
                    source_url=str(item.get("source_url", f"file:///{path.as_posix()}")),
                    description=str(item.get("description", "")),
                    language=str(item.get("language", "en")),
                    fetched_at=item.get("fetched_at"),
                    status=DocumentStatus(item.get("status", DocumentStatus.INGESTED.value)),
                )

                if doc.content_hash in seen_hashes:
                    stats.duplicates_skipped += 1
                    continue

                seen_hashes.add(doc.content_hash)
                documents.append(doc)
                stats.imported += 1

            except Exception as e:
                stats.errors.append(f"Error importing record {idx}: {e}")
                stats.errors_count += 1

        return documents, stats

    def import_from_jsonl(self, file_path: str | Path) -> Tuple[List[Document], ImportStats]:
        """Import documents from newline-delimited JSON (JSONL)."""
        stats = ImportStats()
        documents: List[Document] = []
        path = Path(file_path)

        if not path.exists():
            stats.errors.append(f"File not found: {path}")
            stats.errors_count += 1
            return documents, stats

        seen_hashes: Set[str] = set()

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    line_str = line.strip()
                    if not line_str:
                        continue
                    stats.total_records += 1
                    try:
                        record = json.loads(line_str)
                        if not isinstance(record, dict):
                            stats.errors.append(f"Line {line_no} is not a valid JSON object")
                            stats.errors_count += 1
                            continue

                        doc_id = str(record.get("document_id", f"jsonl_{path.stem}_{line_no}")).strip()
                        title = str(record.get("title", f"Document {doc_id}")).strip()
                        content = str(record.get("content", ""))

                        doc = Document.create(
                            document_id=doc_id,
                            title=title,
                            content=content,
                            source_url=str(record.get("source_url", f"file:///{path.as_posix()}#L{line_no}")),
                            description=str(record.get("description", "")),
                            language=str(record.get("language", "en")),
                            fetched_at=record.get("fetched_at"),
                            status=DocumentStatus(record.get("status", DocumentStatus.INGESTED.value)),
                        )

                        if doc.content_hash in seen_hashes:
                            stats.duplicates_skipped += 1
                            continue

                        seen_hashes.add(doc.content_hash)
                        documents.append(doc)
                        stats.imported += 1

                    except Exception as e:
                        stats.errors.append(f"Line {line_no} error: {e}")
                        stats.errors_count += 1

        except Exception as e:
            stats.errors.append(f"File reading error in {path}: {e}")
            stats.errors_count += 1

        return documents, stats

    def import_from_directory(
        self,
        directory: str | Path,
        extensions: Tuple[str, ...] = (".txt", ".html", ".htm", ".md"),
        recursive: bool = True,
    ) -> Tuple[List[Document], ImportStats]:
        """Import text, markdown, or HTML documents from a local directory."""
        stats = ImportStats()
        documents: List[Document] = []
        dir_path = Path(directory)

        if not dir_path.is_dir():
            stats.errors.append(f"Directory not found: {dir_path}")
            stats.errors_count += 1
            return documents, stats

        files = dir_path.rglob("*") if recursive else dir_path.glob("*")
        target_files = [f for f in files if f.is_file() and f.suffix.lower() in extensions]
        stats.total_records = len(target_files)
        seen_hashes: Set[str] = set()

        for path in target_files:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    raw_text = f.read()

                if not raw_text.strip():
                    stats.errors.append(f"Skipped empty file: {path.name}")
                    stats.errors_count += 1
                    continue

                title = path.stem.replace("_", " ").replace("-", " ").title()
                content = raw_text

                # HTML processing
                if path.suffix.lower() in (".html", ".htm"):
                    # Extract title tag if present
                    title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_text, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        extracted_title = title_match.group(1).strip()
                        if extracted_title:
                            title = extracted_title
                    content = self.text_processor.clean_html(raw_text)

                doc = Document.create(
                    document_id=f"file_{path.stem}_{hash(path.as_posix()) & 0xffffffff:08x}",
                    title=title,
                    content=content,
                    source_url=f"file:///{path.as_posix()}",
                    description=f"Imported from {path.name}",
                    language="en",
                )

                if doc.content_hash in seen_hashes:
                    stats.duplicates_skipped += 1
                    continue

                seen_hashes.add(doc.content_hash)
                documents.append(doc)
                stats.imported += 1

            except Exception as e:
                stats.errors.append(f"Error processing {path.name}: {e}")
                stats.errors_count += 1

        return documents, stats
