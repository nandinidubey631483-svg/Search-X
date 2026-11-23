"""Unit tests for Document and Token models (Module B)."""
import pytest
from crawler.app.models import Document, DocumentStatus, Token


def test_valid_token():
    token = Token(term="search", position=0, char_start=0, char_end=6)
    assert token.term == "search"
    assert token.position == 0
    assert token.char_start == 0
    assert token.char_end == 6
    assert token.to_dict() == {
        "term": "search",
        "position": 0,
        "char_start": 0,
        "char_end": 6,
    }


def test_token_validation_errors():
    with pytest.raises(ValueError, match="cannot be empty"):
        Token(term="", position=0, char_start=0, char_end=0)

    with pytest.raises(ValueError, match="non-negative"):
        Token(term="test", position=-1, char_start=0, char_end=4)

    with pytest.raises(ValueError, match="Invalid char offsets"):
        Token(term="test", position=0, char_start=5, char_end=3)


def test_document_creation_valid():
    doc = Document.create(
        document_id="doc_1",
        title="Introduction to Information Retrieval",
        content="An inverted index is the fundamental data structure in search.",
        source_url="https://example.com/ir",
        description="IR overview",
    )
    assert doc.document_id == "doc_1"
    assert doc.title == "Introduction to Information Retrieval"
    assert doc.source_url == "https://example.com/ir"
    assert doc.status == DocumentStatus.INGESTED.value
    assert len(doc.content_hash) == 64
    assert doc.fetched_at != ""


def test_document_required_fields_validation():
    # Missing document_id
    with pytest.raises(ValueError, match="document_id is required"):
        Document.create(document_id="", title="Title", content="Some content")

    # Missing both title and source_url
    with pytest.raises(ValueError, match="Either title or source_url"):
        Document.create(document_id="doc_1", title="", source_url="", content="Some content")

    # Missing content
    with pytest.raises(ValueError, match="content is required"):
        Document.create(document_id="doc_1", title="Title", content="   ")


def test_document_invalid_status():
    with pytest.raises(ValueError, match="Invalid status"):
        Document(
            document_id="doc_1",
            title="Title",
            content="Hello world",
            fetched_at="2026-11-23T09:00:00Z",
            content_hash="abc",
            status="unknown_status",
        ).validate()


def test_document_content_hash_consistency():
    content = "Search engines crawl, index, and rank documents."
    hash1 = Document.compute_content_hash(content)
    hash2 = Document.compute_content_hash(content)
    assert hash1 == hash2
    assert len(hash1) == 64

    # Whitespace normalization at borders
    hash_trimmed = Document.compute_content_hash(f"  {content} \n")
    assert hash_trimmed == hash1


def test_document_deduplication():
    doc1 = Document.create(
        document_id="doc_1",
        title="Page 1",
        content="Identical body text",
        source_url="https://example.com/p1",
    )
    doc2 = Document.create(
        document_id="doc_2",
        title="Page 2",
        content="Identical body text",
        source_url="https://example.com/p2",
    )
    doc3 = Document.create(
        document_id="doc_3",
        title="Page 3",
        content="Different body text",
        source_url="https://example.com/p3",
    )
    assert doc1.is_duplicate_of(doc2)
    assert not doc1.is_duplicate_of(doc3)


def test_document_json_roundtrip():
    doc = Document.create(
        document_id="doc_test",
        title="Test Title with Special Characters: <>&\"'",
        content="Here is some content with Unicode: café, résumé.",
        source_url="https://example.com/test",
        description="Test desc",
        language="en",
    )
    json_str = doc.to_json()
    reconstructed = Document.from_json(json_str)

    assert reconstructed.document_id == doc.document_id
    assert reconstructed.title == doc.title
    assert reconstructed.content == doc.content
    assert reconstructed.source_url == doc.source_url
    assert reconstructed.content_hash == doc.content_hash
    assert reconstructed.fetched_at == doc.fetched_at
    assert reconstructed.status == doc.status
