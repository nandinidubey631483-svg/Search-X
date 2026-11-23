"""
Search Engine Service for SearchX Backend.
Interfaces with C++ searchx_engine binary using the defined CLI/JSON protocol.
"""
from __future__ import annotations

import collections
import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from crawler.app.models import Document
from crawler.app.text_processor import TextProcessor

from ..config import settings
from ..db.repository import DatabaseRepository
from ..models.schemas import (
    AnalyticsResponse,
    DocumentResponse,
    IndexStats,
    SearchResponse,
    SearchResultItem,
)

logger = logging.getLogger("searchx.backend.search")


class SearchEngineService:
    """Coordinates search operations, indexing, and analytics via C++ core engine binary."""

    def __init__(
        self,
        index_path: Optional[Path] = None,
        engine_bin: Optional[Path] = None,
        text_processor: Optional[TextProcessor] = None,
        repository: Optional[DatabaseRepository] = None,
    ) -> None:
        self.index_path = Path(index_path or settings.INDEX_PATH).resolve()
        self.engine_bin = Path(engine_bin or settings.ENGINE_BIN).resolve()
        self.text_processor = text_processor or TextProcessor()
        self.repository = repository or DatabaseRepository()
        self.total_searches = 0
        self.query_frequency: Dict[str, int] = collections.defaultdict(int)

    def _call_engine(self, args: List[str]) -> str:
        """Execute C++ engine binary with given arguments and return stdout."""
        import os
        cmd = [str(self.engine_bin)] + args
        env = os.environ.copy()
        # Ensure compiler bin directory is in PATH for MinGW runtime DLLs
        bin_dir = "C:\\Users\\Dell\\AppData\\Local\\Microsoft\\WinGet\\Packages\\BrechtSanders.WinLibs.MCF.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\\mingw64\\bin"
        if os.path.isdir(bin_dir) and bin_dir not in env.get("PATH", ""):
            env["PATH"] = f"{bin_dir};" + env.get("PATH", "")

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
            return res.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"C++ engine error: {e.stderr}")
            raise RuntimeError(f"Search engine binary failed: {e.stderr}")
        except FileNotFoundError:
            logger.error(f"C++ engine binary not found at: {self.engine_bin}")
            raise RuntimeError(f"Engine binary not found at {self.engine_bin}")

    def generate_snippet(self, content: str, query_terms: List[str], window: int = 160) -> str:
        """Generate a contextual snippet highlighting text around matched query terms."""
        if not content:
            return ""
        if not query_terms:
            return content[:window] + ("..." if len(content) > window else "")

        # Find earliest match of any query term in content
        lower_content = content.lower()
        earliest_pos = -1
        for term in query_terms:
            pos = lower_content.find(term.lower())
            if pos != -1 and (earliest_pos == -1 or pos < earliest_pos):
                earliest_pos = pos

        if earliest_pos == -1:
            return content[:window] + ("..." if len(content) > window else "")

        start = max(0, earliest_pos - window // 3)
        end = min(len(content), start + window)

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(content) else ""
        return f"{prefix}{content[start:end].strip()}{suffix}"

    def search(
        self,
        query: str,
        algo: str = "bm25",
        mode: str = "any",
        limit: int = 10,
        offset: int = 0,
    ) -> SearchResponse:
        """Execute search query via C++ core engine and return paginated results with snippets."""
        normalized_terms = self.text_processor.tokenize_query(query)
        self.total_searches += 1
        clean_query = " ".join(normalized_terms)
        if clean_query:
            self.query_frequency[clean_query] += 1
            if self.repository:
                try:
                    self.repository.record_query(clean_query)
                except Exception as e:
                    logger.warning(f"Failed to record query in DB: {e}")

        if not normalized_terms or not self.index_path.exists():
            return SearchResponse(
                query=query,
                total_hits=0,
                page=(offset // limit) + 1 if limit > 0 else 1,
                limit=limit,
                algorithm=algo,
                results=[],
            )

        top_k = offset + limit
        args = ["search", str(self.index_path), algo, mode, str(top_k)] + normalized_terms
        raw_json = self._call_engine(args)

        try:
            items_data = json.loads(raw_json)
        except json.JSONDecodeError:
            items_data = []

        total_hits = len(items_data)
        paginated = items_data[offset : offset + limit]

        results = [
            SearchResultItem(
                document_id=item.get("document_id", ""),
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=self.generate_snippet(item.get("content", ""), normalized_terms),
                score=round(float(item.get("score", 0.0)), 4),
            )
            for item in paginated
        ]

        return SearchResponse(
            query=query,
            total_hits=total_hits,
            page=(offset // limit) + 1 if limit > 0 else 1,
            limit=limit,
            algorithm=algo,
            results=results,
        )

    def get_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """Fetch term suggestions starting with prefix from index vocabulary."""
        prefix_clean = prefix.strip().lower()
        if not prefix_clean or not self.index_path.exists():
            return []

        args = ["suggestions", str(self.index_path), prefix_clean, str(limit)]
        try:
            raw = self._call_engine(args)
            return json.loads(raw)
        except Exception:
            return []

    def get_document(self, doc_id: str) -> Optional[DocumentResponse]:
        """Retrieve document metadata by string document ID."""
        if self.index_path.exists():
            args = ["document", str(self.index_path), doc_id]
            try:
                raw = self._call_engine(args)
                data = json.loads(raw)
                if "error" not in data:
                    return DocumentResponse(
                        document_id=data.get("document_id", ""),
                        title=data.get("title", ""),
                        source_url=data.get("source_url", ""),
                        content=data.get("content", ""),
                        description=data.get("description", ""),
                        language=data.get("language", "en"),
                        fetched_at=data.get("fetched_at", ""),
                        status=data.get("status", "ingested"),
                    )
            except Exception:
                pass

        # Fallback to persistent database
        if self.repository:
            doc_db = self.repository.get_document(doc_id)
            if doc_db:
                return DocumentResponse(
                    document_id=doc_db.document_id,
                    title=doc_db.title,
                    source_url=doc_db.source_url,
                    content=doc_db.content,
                    description=doc_db.description or "",
                    language=doc_db.language or "en",
                    fetched_at=doc_db.fetched_at or "",
                    status=doc_db.status or "ingested",
                )

        return None

    def get_stats(self) -> IndexStats:
        """Fetch index statistics from C++ core engine."""
        if not self.index_path.exists():
            return IndexStats(total_documents=0, vocabulary_size=0, average_document_length=0.0)

        args = ["stats", str(self.index_path)]
        try:
            raw = self._call_engine(args)
            data = json.loads(raw)
            return IndexStats(
                total_documents=data.get("total_documents", 0),
                vocabulary_size=data.get("vocabulary_size", 0),
                average_document_length=round(data.get("average_document_length", 0.0), 2),
            )
        except Exception:
            return IndexStats(total_documents=0, vocabulary_size=0, average_document_length=0.0)

    def index_documents(self, documents: List[Document]) -> int:
        """
        Tokenize documents and index them in the C++ core engine.
        Serializes to tab-delimited payload for fast C++ ingestion.
        """
        if not documents:
            return 0

        # Create temporary TSV payload
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tf:
            payload_path = tf.name
            for doc in documents:
                tokens = self.text_processor.tokenize(doc.content)
                # Escape newlines and tabs in fields
                def esc(s: str) -> str:
                    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")

                doc_line = (
                    f"DOC\t{esc(doc.document_id)}\t{esc(doc.source_url)}\t{esc(doc.title)}\t"
                    f"{esc(doc.content_hash)}\t{esc(doc.fetched_at)}\t{esc(doc.status)}\t{esc(doc.content)}\n"
                )
                tf.write(doc_line)

                tok_parts = [f"{esc(t.term)}:{t.position}:{t.char_start}:{t.char_end}" for t in tokens]
                tf.write(f"TOKENS\t{'\t'.join(tok_parts)}\n")

        try:
            args = ["index", str(self.index_path), payload_path]
            raw = self._call_engine(args)
            data = json.loads(raw)
            indexed_count = data.get("indexed_count", 0)

            # Persist documents into database
            if self.repository:
                try:
                    self.repository.save_documents(documents)
                except Exception as e:
                    logger.warning(f"Failed to persist indexed documents in DB: {e}")

            return indexed_count
        finally:
            try:
                Path(payload_path).unlink(missing_ok=True)
            except Exception:
                pass

    def get_analytics(self) -> AnalyticsResponse:
        """Return search engine usage and index analytics."""
        stats = self.get_stats()
        
        # Use repository query analytics if available
        top_queries = {}
        total_searches = self.total_searches
        if self.repository:
            try:
                db_top = self.repository.get_top_queries(10)
                db_total = self.repository.total_queries_count()
                if db_top or db_total > 0:
                    top_queries = db_top
                    total_searches = max(self.total_searches, db_total)
            except Exception as e:
                logger.warning(f"Failed to retrieve analytics from DB: {e}")

        if not top_queries:
            top_queries = dict(sorted(self.query_frequency.items(), key=lambda x: x[1], reverse=True)[:10])

        return AnalyticsResponse(
            total_searches=total_searches,
            top_queries=top_queries,
            index_stats=stats,
        )
