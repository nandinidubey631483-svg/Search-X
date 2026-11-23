"""
Canonical Document Model and Token Definitions for SearchX.
Complies with ADR 0001 and PROJECT_CONTEXT.md Module B.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class DocumentStatus(str, Enum):
    INGESTED = "ingested"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class Token:
    """Represents a normalized token with positional and character offset metadata."""
    term: str
    position: int
    char_start: int
    char_end: int

    def __post_init__(self) -> None:
        if not self.term:
            raise ValueError("Token term cannot be empty")
        if self.position < 0:
            raise ValueError(f"Token position must be non-negative, got {self.position}")
        if self.char_start < 0 or self.char_end < self.char_start:
            raise ValueError(
                f"Invalid char offsets: start={self.char_start}, end={self.char_end}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Token:
        return cls(
            term=str(data["term"]),
            position=int(data["position"]),
            char_start=int(data["char_start"]),
            char_end=int(data["char_end"]),
        )


@dataclass
class Document:
    """Canonical document representation across SearchX."""
    document_id: str
    title: str
    content: str
    fetched_at: str
    content_hash: str
    source_url: str = ""
    description: str = ""
    language: str = "en"
    status: str = DocumentStatus.INGESTED.value

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute deterministic SHA-256 hash of cleaned text."""
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

    @classmethod
    def create(
        cls,
        document_id: str,
        title: str,
        content: str,
        source_url: str = "",
        description: str = "",
        language: str = "en",
        fetched_at: Optional[str] = None,
        status: DocumentStatus = DocumentStatus.INGESTED,
    ) -> Document:
        """Factory helper creating a valid Document with auto-calculated hash and timestamp."""
        if not fetched_at:
            fetched_at = datetime.now(timezone.utc).isoformat()
        content_hash = cls.compute_content_hash(content)
        doc = cls(
            document_id=document_id.strip(),
            source_url=source_url.strip(),
            title=title.strip(),
            content=content,
            description=description.strip(),
            language=language.strip() or "en",
            content_hash=content_hash,
            fetched_at=fetched_at,
            status=status.value if isinstance(status, DocumentStatus) else str(status),
        )
        doc.validate()
        return doc

    def validate(self) -> None:
        """Validate required fields and constraints according to ADR 0001."""
        if not self.document_id:
            raise ValueError("document_id is required and cannot be empty")
        if not self.title and not self.source_url:
            raise ValueError("Either title or source_url must be provided")
        if not self.content or not self.content.strip():
            raise ValueError("content is required and cannot be empty or whitespace only")
        if not self.content_hash:
            raise ValueError("content_hash is required")
        if not self.fetched_at:
            raise ValueError("fetched_at is required")
        valid_statuses = {s.value for s in DocumentStatus}
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{self.status}'. Must be one of: {sorted(valid_statuses)}"
            )

    def is_duplicate_of(self, other: Document) -> bool:
        """Check if this document has identical content to another document."""
        return bool(self.content_hash and self.content_hash == other.content_hash)

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to JSON-serializable dictionary."""
        return asdict(self)

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize document to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Document:
        """Create Document from dictionary with validation."""
        doc = cls(
            document_id=str(data.get("document_id", "")),
            source_url=str(data.get("source_url", "")),
            title=str(data.get("title", "")),
            content=str(data.get("content", "")),
            description=str(data.get("description", "")),
            language=str(data.get("language", "en")),
            content_hash=str(data.get("content_hash", "")),
            fetched_at=str(data.get("fetched_at", "")),
            status=str(data.get("status", DocumentStatus.INGESTED.value)),
        )
        doc.validate()
        return doc

    @classmethod
    def from_json(cls, json_str: str) -> Document:
        """Parse JSON string into Document with validation."""
        return cls.from_dict(json.loads(json_str))
