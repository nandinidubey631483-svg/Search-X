"""
Unit tests for Query Spell Correction & Typo-Tolerance Engine.
Tests Damerau-Levenshtein distance, vocabulary candidate matching,
document frequency tie-breaking, casing preservation, and multi-word queries.
"""
import pytest
from backend.app.services.spell_checker import SpellChecker, CorrectionResult


@pytest.fixture
def spell_checker():
    return SpellChecker(max_edit_distance=2)


@pytest.fixture
def mock_vocab():
    return {
        "python": 100,
        "inverted": 50,
        "index": 60,
        "algorithm": 45,
        "retrieval": 40,
        "ranking": 35,
        "crawler": 30,
        "search": 80,
        "engine": 75,
        "database": 25,
        "redis": 20,
        "postgres": 15,
        # Specific terms for tie-breaking
        "cat": 10,
        "car": 50,
    }


def test_damerau_levenshtein_distance(spell_checker):
    # Identical
    assert spell_checker.damerau_levenshtein("python", "python") == 0
    # Deletion
    assert spell_checker.damerau_levenshtein("pythn", "python") == 1
    # Insertion
    assert spell_checker.damerau_levenshtein("pythons", "python") == 1
    # Substitution
    assert spell_checker.damerau_levenshtein("pytbon", "python") == 1
    # Transposition of adjacent letters
    assert spell_checker.damerau_levenshtein("pyhton", "python") == 1
    # Distance 2
    assert spell_checker.damerau_levenshtein("pyth", "python") == 2


def test_find_best_term_candidate_exact(spell_checker, mock_vocab):
    candidate = spell_checker.find_best_term_candidate("python", mock_vocab)
    assert candidate is not None
    term, conf = candidate
    assert term == "python"
    assert conf == 1.0


def test_find_best_term_candidate_typos(spell_checker, mock_vocab):
    # Deletion: "pythn" -> "python"
    term, conf = spell_checker.find_best_term_candidate("pythn", mock_vocab)
    assert term == "python"
    assert conf == 0.5  # 1 / (1 + 1)

    # Transposition: "pyhton" -> "python"
    term, conf = spell_checker.find_best_term_candidate("pyhton", mock_vocab)
    assert term == "python"

    # Substitution: "invertd" -> "inverted"
    term, conf = spell_checker.find_best_term_candidate("invertd", mock_vocab)
    assert term == "inverted"


def test_tie_breaking_by_document_frequency(spell_checker, mock_vocab):
    # "ca" is distance 1 from both "cat" (df=10) and "car" (df=50)
    # The higher frequency candidate "car" must be chosen
    term, _ = spell_checker.find_best_term_candidate("ca", mock_vocab)
    assert term == "car"


def test_check_query_multi_word_and_casing(spell_checker, mock_vocab):
    res = spell_checker.check_query("Invertd Indx", mock_vocab)
    assert res.has_correction is True
    # Capitalization preserved
    assert res.corrected_query == "Inverted Index"
    assert "Invertd" in res.changed_terms
    assert "Indx" in res.changed_terms


def test_check_query_no_typo(spell_checker, mock_vocab):
    res = spell_checker.check_query("python search engine", mock_vocab)
    assert res.has_correction is False
    assert res.corrected_query == "python search engine"
    assert len(res.changed_terms) == 0


def test_check_query_empty_or_special_chars(spell_checker, mock_vocab):
    res = spell_checker.check_query("", mock_vocab)
    assert res.has_correction is False

    res2 = spell_checker.check_query("   ", mock_vocab)
    assert res2.has_correction is False
