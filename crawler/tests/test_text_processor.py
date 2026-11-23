"""Unit tests for TextProcessor (Module C)."""
from crawler.app.text_processor import TextProcessor


def test_normalize_text_case_folding():
    processor = TextProcessor()
    assert processor.normalize_text("SearchX Engine") == "searchx engine"
    assert processor.normalize_text("UPPERCASE") == "uppercase"
    assert processor.normalize_text("") == ""


def test_normalize_text_unicode_nfkc():
    processor = TextProcessor()
    # Ligature 'fi' (\uFB01) decomposes to 'fi' under NFKC
    assert processor.normalize_text("ﬁle") == "file"
    # Accented text
    assert processor.normalize_text("Café Résumé") == "café résumé"


def test_tokenize_basic():
    processor = TextProcessor()
    text = "Search engines index documents"
    tokens = processor.tokenize(text)

    assert len(tokens) == 4
    assert [t.term for t in tokens] == ["search", "engines", "index", "documents"]
    assert [t.position for t in tokens] == [0, 1, 2, 3]

    # Verify character offsets
    for token in tokens:
        assert text[token.char_start:token.char_end].lower() == token.term


def test_tokenize_punctuation_and_whitespace():
    processor = TextProcessor()
    text = "Hello, world!  This is... SearchX."
    tokens = processor.tokenize(text)

    terms = [t.term for t in tokens]
    assert terms == ["hello", "world", "this", "is", "searchx"]
    assert [t.position for t in tokens] == [0, 1, 2, 3, 4]


def test_tokenize_hyphen_and_contractions():
    processor = TextProcessor()
    text = "The user's state-of-the-art engine."
    tokens = processor.tokenize(text)

    terms = [t.term for t in tokens]
    assert "user's" in terms
    assert "state-of-the-art" in terms


def test_tokenize_stopwords_filtering():
    processor = TextProcessor()
    text = "this is a test of the search system"

    all_tokens = processor.tokenize(text, filter_stopwords=False)
    filtered_tokens = processor.tokenize(text, filter_stopwords=True)

    assert len(all_tokens) > len(filtered_tokens)
    assert [t.term for t in filtered_tokens] == ["test", "search", "system"]
    # Verify sequential positions are maintained
    assert [t.position for t in filtered_tokens] == [0, 1, 2]


def test_tokenize_empty_and_whitespace():
    processor = TextProcessor()
    assert processor.tokenize("") == []
    assert processor.tokenize("   \n\t  ") == []
    assert processor.tokenize("!@#$%^&*()") == []


def test_tokenize_query_consistency():
    processor = TextProcessor()
    query = "SearchX Inverted-Index!"
    doc_text = "searchx inverted-index"

    query_terms = processor.tokenize_query(query)
    doc_terms = [t.term for t in processor.tokenize(doc_text)]

    assert query_terms == doc_terms
    assert query_terms == ["searchx", "inverted-index"]


def test_clean_html():
    raw_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ignored in Body</title>
        <style>body { color: red; }</style>
        <script>console.log("Ignore me");</script>
    </head>
    <body>
        <h1>SearchX Architecture</h1>
        <p>This is the <b>first</b> paragraph &amp; overview.</p>
        <div>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>
        <noscript>JavaScript is required</noscript>
    </body>
    </html>
    """
    clean_text = TextProcessor.clean_html(raw_html)

    assert "SearchX Architecture" in clean_text
    assert "first paragraph & overview" in clean_text
    assert "Item 1 Item 2" in clean_text
    assert "console.log" not in clean_text
    assert "color: red" not in clean_text
    assert "JavaScript is required" not in clean_text
    assert "<" not in clean_text
    assert ">" not in clean_text
