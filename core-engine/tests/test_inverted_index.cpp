#include "inverted_index.hpp"
#include "document.hpp"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <iostream>
#include <vector>
#include <string>

using namespace searchx;

// Helper to construct a Document with a synthetic hash
Document make_doc(const std::string& id, const std::string& title, const std::string& content, const std::string& hash) {
    Document doc;
    doc.document_id = id;
    doc.title = title;
    doc.content = content;
    doc.source_url = "https://example.com/" + id;
    doc.content_hash = hash;
    doc.fetched_at = "2026-11-23T09:00:00Z";
    doc.status = "ingested";
    return doc;
}

// Helper to construct tokens from terms
std::vector<Token> make_tokens(const std::vector<std::string>& terms) {
    std::vector<Token> tokens;
    uint32_t pos = 0;
    uint32_t offset = 0;
    for (const auto& term : terms) {
        tokens.push_back(Token{term, pos, offset, offset + static_cast<uint32_t>(term.length())});
        offset += static_cast<uint32_t>(term.length()) + 1;
        pos++;
    }
    return tokens;
}

void test_build_and_single_term_lookup() {
    InvertedIndex index;

    // Doc 1: "python" "search" "engine"
    Document d1 = make_doc("doc_1", "Python Search", "python search engine", "hash_1");
    std::vector<Token> t1 = make_tokens({"python", "search", "engine"});
    assert(index.add_document(d1, t1));

    // Doc 2: "python" "programming" "language" "python"
    Document d2 = make_doc("doc_2", "Python Programming", "python programming language python", "hash_2");
    std::vector<Token> t2 = make_tokens({"python", "programming", "language", "python"});
    assert(index.add_document(d2, t2));

    // Check total documents and vocabulary
    assert(index.total_documents() == 2);
    assert(index.vocabulary_size() == 5); // python, search, engine, programming, language (5 distinct terms)

    // Single term lookup
    auto py_docs = index.lookup_term("python");
    assert(py_docs.size() == 2);

    auto search_docs = index.lookup_term("search");
    assert(search_docs.size() == 1);
    assert(search_docs[0] == *index.get_internal_doc_id("doc_1"));

    // Verify postings details
    const auto* py_postings = index.get_postings("python");
    assert(py_postings != nullptr);
    assert(py_postings->size() == 2);

    // In doc 1, "python" appeared once at pos 0
    assert((*py_postings)[0].term_frequency == 1);
    assert((*py_postings)[0].positions == std::vector<uint32_t>{0});

    // In doc 2, "python" appeared twice at pos 0 and pos 3
    assert((*py_postings)[1].term_frequency == 2);
    std::vector<uint32_t> expected_pos{0, 3};
    assert((*py_postings)[1].positions == expected_pos);

    std::cout << "[PASS] test_build_and_single_term_lookup" << std::endl;
}

void test_boolean_and_lookup() {
    InvertedIndex index;

    // Doc 1: python search
    index.add_document(make_doc("d1", "T1", "python search", "h1"),
                       make_tokens({"python", "search"}));
    // Doc 2: python web development
    index.add_document(make_doc("d2", "T2", "python web development", "h2"),
                       make_tokens({"python", "web", "development"}));
    // Doc 3: search engine development python
    index.add_document(make_doc("d3", "T3", "search engine development python", "h3"),
                       make_tokens({"search", "engine", "development", "python"}));

    // AND "python" AND "search" -> Doc 1 and Doc 3
    auto and_results = index.lookup_and({"python", "search"});
    assert(and_results.size() == 2);
    assert(and_results[0] == *index.get_internal_doc_id("d1"));
    assert(and_results[1] == *index.get_internal_doc_id("d3"));

    // AND "python" AND "development" -> Doc 2 and Doc 3
    auto dev_results = index.lookup_and({"python", "development"});
    assert(dev_results.size() == 2);
    assert(dev_results[0] == *index.get_internal_doc_id("d2"));
    assert(dev_results[1] == *index.get_internal_doc_id("d3"));

    // AND "python" AND "search" AND "engine" -> Doc 3 only
    auto triple_results = index.lookup_and({"python", "search", "engine"});
    assert(triple_results.size() == 1);
    assert(triple_results[0] == *index.get_internal_doc_id("d3"));

    // AND with non-existent term -> empty
    auto empty_results = index.lookup_and({"python", "nonexistent_term"});
    assert(empty_results.empty());

    std::cout << "[PASS] test_boolean_and_lookup" << std::endl;
}

void test_boolean_or_lookup() {
    InvertedIndex index;

    index.add_document(make_doc("d1", "T1", "c++", "h1"), make_tokens({"cpp"}));
    index.add_document(make_doc("d2", "T2", "rust", "h2"), make_tokens({"rust"}));
    index.add_document(make_doc("d3", "T3", "python", "h3"), make_tokens({"python"}));

    // OR "cpp" OR "rust" -> d1, d2
    auto or_results = index.lookup_or({"cpp", "rust"});
    assert(or_results.size() == 2);
    assert(or_results[0] == *index.get_internal_doc_id("d1"));
    assert(or_results[1] == *index.get_internal_doc_id("d2"));

    // OR including non-existent term
    auto or_with_empty = index.lookup_or({"rust", "go"});
    assert(or_with_empty.size() == 1);
    assert(or_with_empty[0] == *index.get_internal_doc_id("d2"));

    std::cout << "[PASS] test_boolean_or_lookup" << std::endl;
}

void test_non_existent_and_empty_queries() {
    InvertedIndex index;
    index.add_document(make_doc("d1", "T1", "alpha beta", "h1"), make_tokens({"alpha", "beta"}));

    // Lookup missing term
    assert(index.lookup_term("gamma").empty());
    assert(index.get_postings("gamma") == nullptr);
    assert(index.document_frequency("gamma") == 0);

    // Empty queries
    assert(index.lookup_term("").empty());
    assert(index.lookup_and({}).empty());
    assert(index.lookup_or({}).empty());
    assert(index.lookup_and({""}).empty());

    std::cout << "[PASS] test_non_existent_and_empty_queries" << std::endl;
}

void test_document_removal_and_update() {
    InvertedIndex index;

    Document d1 = make_doc("d1", "Title 1", "quick brown fox", "h1");
    Document d2 = make_doc("d2", "Title 2", "lazy dog", "h2");

    index.add_document(d1, make_tokens({"quick", "brown", "fox"}));
    index.add_document(d2, make_tokens({"lazy", "dog"}));

    assert(index.total_documents() == 2);
    assert(index.vocabulary_size() == 5);

    // Remove d1
    assert(index.remove_document("d1"));
    assert(!index.has_document("d1"));
    assert(index.total_documents() == 1);
    // "quick", "brown", "fox" should now be purged from vocabulary
    assert(index.vocabulary_size() == 2);
    assert(index.lookup_term("quick").empty());
    assert(index.lookup_term("dog").size() == 1);

    // Re-indexing / Updating d2
    Document d2_updated = make_doc("d2", "Title 2 Updated", "active energetic dog", "h2_updated");
    assert(index.add_document(d2_updated, make_tokens({"active", "energetic", "dog"})));
    assert(index.total_documents() == 1);
    assert(index.lookup_term("lazy").empty()); // previous term purged
    assert(index.lookup_term("energetic").size() == 1);

    std::cout << "[PASS] test_document_removal_and_update" << std::endl;
}

void test_duplicate_rejection() {
    InvertedIndex index;

    Document d1 = make_doc("doc_original", "Original", "Exact identical content", "sha256_identical_hash");
    Document d2 = make_doc("doc_duplicate", "Duplicate", "Exact identical content", "sha256_identical_hash");

    assert(index.add_document(d1, make_tokens({"exact", "identical", "content"})));
    // Second doc with same hash but different ID must be rejected
    assert(!index.add_document(d2, make_tokens({"exact", "identical", "content"})));
    assert(index.total_documents() == 1);

    std::cout << "[PASS] test_duplicate_rejection" << std::endl;
}

void test_corpus_statistics() {
    InvertedIndex index;

    // Doc 1 has 3 tokens
    index.add_document(make_doc("d1", "T1", "one two three", "h1"), make_tokens({"one", "two", "three"}));
    // Doc 2 has 5 tokens
    index.add_document(make_doc("d2", "T2", "one two three four five", "h2"), make_tokens({"one", "two", "three", "four", "five"}));

    assert(index.total_documents() == 2);
    uint32_t id1 = *index.get_internal_doc_id("d1");
    uint32_t id2 = *index.get_internal_doc_id("d2");

    assert(index.document_length(id1) == 3);
    assert(index.document_length(id2) == 5);
    // Average document length: (3 + 5) / 2 = 4.0
    assert(index.average_document_length() == 4.0);

    // Document frequencies
    assert(index.document_frequency("one") == 2);
    assert(index.document_frequency("four") == 1);
    assert(index.document_frequency("six") == 0);

    std::cout << "[PASS] test_corpus_statistics" << std::endl;
}

int main() {
    std::cout << "Running InvertedIndex C++ unit tests..." << std::endl;
    test_build_and_single_term_lookup();
    test_boolean_and_lookup();
    test_boolean_or_lookup();
    test_non_existent_and_empty_queries();
    test_document_removal_and_update();
    test_duplicate_rejection();
    test_corpus_statistics();
    std::cout << "All InvertedIndex unit tests passed successfully!" << std::endl;
    return 0;
}
