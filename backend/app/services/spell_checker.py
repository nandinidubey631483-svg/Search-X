"""
Query Spell Correction and Typo-Tolerance Engine for SearchX.
Uses Damerau-Levenshtein edit distance combined with corpus document frequency weighting
to generate accurate 'Did You Mean?' suggestions for misspelled search queries.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class CorrectionResult:
    """Result of query spell correction."""
    original_query: str
    corrected_query: str
    has_correction: bool
    confidence: float
    changed_terms: Dict[str, str]


class SpellChecker:
    """
    Fast, vocabulary-driven spell checker using Damerau-Levenshtein distance
    and term document frequency weighting.
    """

    def __init__(self, max_edit_distance: int = 2) -> None:
        self.max_edit_distance = max_edit_distance

    @staticmethod
    def damerau_levenshtein(s1: str, s2: str) -> int:
        """
        Compute Damerau-Levenshtein distance between two strings,
        supporting insertion, deletion, substitution, and transposition of adjacent characters.
        """
        len1, len2 = len(s1), len(s2)
        if len1 == 0:
            return len2
        if len2 == 0:
            return len1

        # Truncate check if length difference exceeds max possible edit distance
        if abs(len1 - len2) > 3:
            return abs(len1 - len2)

        # Distance matrix
        d: List[List[int]] = [[0] * (len2 + 2) for _ in range(len1 + 2)]
        inf = len1 + len2
        d[0][0] = inf

        for i in range(0, len1 + 1):
            d[i + 1][0] = inf
            d[i + 1][1] = i
        for j in range(0, len2 + 1):
            d[0][j + 1] = inf
            d[1][j + 1] = j

        da: Dict[str, int] = {}

        for i in range(1, len1 + 1):
            db = 0
            for j in range(1, len2 + 1):
                i1 = da.get(s2[j - 1], 0)
                j1 = db
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                if cost == 0:
                    db = j

                d[i + 1][j + 1] = min(
                    d[i][j] + cost,          # Substitution
                    d[i + 1][j] + 1,         # Insertion
                    d[i][j + 1] + 1,         # Deletion
                    d[i1][j1] + (i - i1 - 1) + 1 + (j - j1 - 1)  # Transposition
                )

            da[s1[i - 1]] = i

        return d[len1 + 1][len2 + 1]

    def find_best_term_candidate(
        self,
        token: str,
        vocab_frequencies: Dict[str, int],
    ) -> Optional[Tuple[str, float]]:
        """
        Find closest candidate for token in vocabulary, weighted by document frequency.
        Returns (candidate_term, score) or None if no valid candidate found within max distance.
        """
        token_lower = token.lower()
        # If term already exists in vocabulary with positive frequency, no typo
        if vocab_frequencies.get(token_lower, 0) > 0:
            return token_lower, 1.0

        candidates: List[Tuple[str, int, int]] = []  # (term, distance, doc_freq)

        # Length filtering: only consider words whose length differs by at most max_edit_distance
        token_len = len(token_lower)
        min_len = max(1, token_len - self.max_edit_distance)
        max_len = token_len + self.max_edit_distance

        for word, df in vocab_frequencies.items():
            if not (min_len <= len(word) <= max_len):
                continue

            dist = self.damerau_levenshtein(token_lower, word)
            if dist <= self.max_edit_distance:
                candidates.append((word, dist, df))

        if not candidates:
            return None

        # Rank candidates by:
        # 1. Edit distance ascending (prefer distance 1 over 2)
        # 2. Document frequency descending (prefer common corpus terms)
        # 3. Alphabetical tie-breaking for determinism
        candidates.sort(key=lambda c: (c[1], -c[2], c[0]))

        best_word, best_dist, best_df = candidates[0]
        # Confidence score inversely proportional to distance and weighted by df
        confidence = 1.0 / (best_dist + 1)
        return best_word, confidence

    def check_query(
        self,
        query: str,
        vocab_frequencies: Dict[str, int],
    ) -> CorrectionResult:
        """
        Analyze search query and generate 'Did you mean' correction if typos detected.
        Preserves non-alphanumeric casing and structure.
        """
        if not query or not query.strip() or not vocab_frequencies:
            return CorrectionResult(
                original_query=query,
                corrected_query=query,
                has_correction=False,
                confidence=1.0,
                changed_terms={},
            )

        # Split into alphanumeric words while preserving punctuation and spacing
        tokens = re.findall(r"\w+|[^\w\s]+|\s+", query)
        corrected_tokens: List[str] = []
        changed_terms: Dict[str, str] = {}
        total_confidence = 1.0
        corrected_count = 0

        for tok in tokens:
            # Only spell-check alphanumeric tokens with length >= 3
            if tok.isalnum() and len(tok) >= 3:
                candidate = self.find_best_term_candidate(tok, vocab_frequencies)
                if candidate:
                    best_word, conf = candidate
                    if best_word.lower() != tok.lower():
                        # Preserve original capitalisation format (e.g. Title case or Lowercase)
                        if tok.istitle():
                            best_word = best_word.capitalize()
                        elif tok.isupper():
                            best_word = best_word.upper()

                        changed_terms[tok] = best_word
                        corrected_tokens.append(best_word)
                        total_confidence = min(total_confidence, conf)
                        corrected_count += 1
                        continue

            corrected_tokens.append(tok)

        corrected_query = "".join(corrected_tokens)
        has_correction = corrected_count > 0 and corrected_query.strip() != query.strip()

        return CorrectionResult(
            original_query=query,
            corrected_query=corrected_query,
            has_correction=has_correction,
            confidence=total_confidence if has_correction else 1.0,
            changed_terms=changed_terms,
        )
