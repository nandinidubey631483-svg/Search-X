"""
Text Normalization and Tokenization Pipeline for SearchX.
Complies with ADR 0001 and PROJECT_CONTEXT.md Module C.
"""
from __future__ import annotations

import html
import re
import unicodedata
from html.parser import HTMLParser
from typing import List, Optional, Set

from .models import Token

# Standard English stopwords
DEFAULT_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
    "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
    "your", "yours", "yourself", "yourselves"
}

# Regex matching words and numbers, allowing internal apostrophes/hyphens
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+(?:['\u2019\-][a-zA-Z0-9]+)*")


class _HTMLTextExtractor(HTMLParser):
    """HTML Parser that strips tags, ignores scripts/styles, and extracts readable text."""

    IGNORED_TAGS = {"script", "style", "noscript", "svg", "head", "iframe"}
    BLOCK_TAGS = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "section", "article"}

    def __init__(self) -> None:
        super().__init__()
        self._pieces: List[str] = []
        self._ignore_depth = 0

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.IGNORED_TAGS:
            self._ignore_depth += 1
        elif tag_lower in self.BLOCK_TAGS:
            self._pieces.append(" ")

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.IGNORED_TAGS:
            self._ignore_depth = max(0, self._ignore_depth - 1)
        elif tag_lower in self.BLOCK_TAGS:
            self._pieces.append(" ")

    def handle_data(self, data: str) -> None:
        if self._ignore_depth == 0 and data:
            self._pieces.append(data)

    def get_text(self) -> str:
        raw_text = "".join(self._pieces)
        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", raw_text).strip()
        return html.unescape(cleaned)


class TextProcessor:
    """Provides consistent HTML extraction, text normalization, and tokenization."""

    def __init__(self, stopwords: Optional[Set[str]] = None) -> None:
        self.stopwords = stopwords if stopwords is not None else DEFAULT_STOPWORDS

    @staticmethod
    def clean_html(raw_html: str) -> str:
        """Extract clean plain text from raw HTML markup."""
        if not raw_html:
            return ""
        extractor = _HTMLTextExtractor()
        extractor.feed(raw_html)
        extractor.close()
        return extractor.get_text()

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text using Unicode NFKC and lowercasing.
        Guarantees identical representation between documents and queries.
        """
        if not text:
            return ""
        nfkc = unicodedata.normalize("NFKC", text)
        return nfkc.lower()

    def tokenize(
        self,
        text: str,
        filter_stopwords: bool = False,
        custom_stopwords: Optional[Set[str]] = None,
    ) -> List[Token]:
        """
        Tokenize normalized text into a list of Token objects with position and char offsets.
        Offsets (char_start, char_end) match the input string positions.
        """
        if not text:
            return []

        active_stopwords = custom_stopwords if custom_stopwords is not None else self.stopwords
        tokens: List[Token] = []
        position = 0

        # Iterate over word matches with their character offsets
        for match in TOKEN_PATTERN.finditer(text):
            raw_match = match.group(0)
            term = self.normalize_text(raw_match)
            if not term:
                continue

            if filter_stopwords and term in active_stopwords:
                continue

            tokens.append(
                Token(
                    term=term,
                    position=position,
                    char_start=match.start(),
                    char_end=match.end(),
                )
            )
            position += 1

        return tokens

    def tokenize_query(
        self,
        query: str,
        filter_stopwords: bool = False,
    ) -> List[str]:
        """
        Tokenize a search query using identical normalization.
        Returns a list of normalized term strings.
        """
        tokens = self.tokenize(query, filter_stopwords=filter_stopwords)
        return [t.term for t in tokens]
