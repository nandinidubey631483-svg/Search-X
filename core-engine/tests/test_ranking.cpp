#include "ranking.hpp"
#include "inverted_index.hpp"
#include "document.hpp"

#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>
#include <string>

using namespace searchx;

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

void test_hand_checkable_tf_idf() {
    InvertedIndex index;
    // D1: "information retrieval" (tf of "retrieval" = 1)
    index.add_document(make_doc("d1", "D1", "information retrieval", "h1"),
                       make_tokens({"information", "retrieval"}));
    // D2: "retrieval search retrieval system" (tf of "retrieval" = 2)
    index.add_document(make_doc("d2", "D2", "retrieval search retrieval system", "h2"),
                       make_tokens({"retrieval", "search", "retrieval", "system"}));
    // D3: "database system" (no "retrieval")
    index.add_document(make_doc("d3", "D3", "database system", "h3"),
                       make_tokens({"database", "system"}));

    Ranker ranker(index);
    auto results = ranker.rank({"retrieval"}, RankingAlgorithm::TF_IDF, MatchMode::ANY_TERM);

    assert(results.size() == 2);
    // D2 has TF=2, D1 has TF=1 -> D2 must rank first
    assert(results[0].string_doc_id == "d2");
    assert(results[1].string_doc_id == "d1");
    assert(results[0].score > results[1].score);

    // Verify mathematical bounds
    // N = 3, DF = 2. IDF = ln(1 + 3/2) = ln(2.5) ~ 0.9163
    // D1 score = (1 + ln(1)) * ln(2.5) = ln(2.5) ~ 0.9163
    // D2 score = (1 + ln(2)) * ln(2.5) ~ 1.6931 * 0.9163 ~ 1.5514
    double expected_d1_score = std::log(2.5);
    double expected_d2_score = (1.0 + std::log(2.0)) * std::log(2.5);
    assert(std::abs(results[1].score - expected_d1_score) < 1e-4);
    assert(std::abs(results[0].score - expected_d2_score) < 1e-4);

    std::cout << "[PASS] test_hand_checkable_tf_idf" << std::endl;
}

void test_bm25_length_normalization() {
    InvertedIndex index;

    // Both documents contain the term "search" with TF=1.
    // Short doc (len = 2 tokens)
    index.add_document(make_doc("doc_short", "Short", "search engine", "h_short"),
                       make_tokens({"search", "engine"}));

    // Long doc (len = 8 tokens)
    index.add_document(make_doc("doc_long", "Long", "search engine with modern distributed architecture and performance", "h_long"),
                       make_tokens({"search", "engine", "with", "modern", "distributed", "architecture", "and", "performance"}));

    Ranker ranker(index); // default b = 0.75
    auto results = ranker.rank({"search"}, RankingAlgorithm::BM25, MatchMode::ANY_TERM);

    assert(results.size() == 2);
    // Because b > 0, the shorter document has higher term density and MUST rank above the longer document
    assert(results[0].string_doc_id == "doc_short");
    assert(results[1].string_doc_id == "doc_long");
    assert(results[0].score > results[1].score);

    // Test parameter sensitivity: if b = 0, document length normalization is disabled
    ranker.set_bm25_params(BM25Params{1.2, 0.0});
    auto results_no_len_norm = ranker.rank({"search"}, RankingAlgorithm::BM25, MatchMode::ANY_TERM);
    assert(results_no_len_norm.size() == 2);
    // With b = 0 and identical TF, both documents should have identical scores
    assert(std::abs(results_no_len_norm[0].score - results_no_len_norm[1].score) < 1e-9);

    std::cout << "[PASS] test_bm25_length_normalization" << std::endl;
}

void test_boolean_match_modes() {
    InvertedIndex index;
    // D1: matches both "cpp" and "search"
    index.add_document(make_doc("d1", "D1", "cpp search", "h1"), make_tokens({"cpp", "search"}));
    // D2: matches only "cpp"
    index.add_document(make_doc("d2", "D2", "cpp compiler", "h2"), make_tokens({"cpp", "compiler"}));
    // D3: matches only "search"
    index.add_document(make_doc("d3", "D3", "python search", "h3"), make_tokens({"python", "search"}));

    Ranker ranker(index);

    // MatchMode::ALL_TERMS (AND)
    auto and_results = ranker.rank({"cpp", "search"}, RankingAlgorithm::BM25, MatchMode::ALL_TERMS);
    assert(and_results.size() == 1);
    assert(and_results[0].string_doc_id == "d1");

    // MatchMode::ANY_TERM (OR)
    auto or_results = ranker.rank({"cpp", "search"}, RankingAlgorithm::BM25, MatchMode::ANY_TERM);
    assert(or_results.size() == 3);
    // d1 matches both terms, so it must score higher than d2 and d3 which each only match one
    assert(or_results[0].string_doc_id == "d1");

    std::cout << "[PASS] test_boolean_match_modes" << std::endl;
}

void test_deterministic_tie_breaking() {
    InvertedIndex index;
    // Two documents with same TF and same length
    index.add_document(make_doc("d_alpha", "Title Alpha", "apple banana", "h_alpha"),
                       make_tokens({"apple", "banana"}));
    index.add_document(make_doc("d_beta", "Title Beta", "apple banana", "h_beta"),
                       make_tokens({"apple", "banana"}));

    Ranker ranker(index);
    auto results = ranker.rank({"apple"}, RankingAlgorithm::BM25, MatchMode::ANY_TERM);

    assert(results.size() == 2);
    assert(std::abs(results[0].score - results[1].score) < 1e-9);
    // Tie-breaker: smaller internal doc_id comes first
    assert(results[0].doc_id < results[1].doc_id);
    assert(results[0].string_doc_id == "d_alpha");
    assert(results[1].string_doc_id == "d_beta");

    std::cout << "[PASS] test_deterministic_tie_breaking" << std::endl;
}

void test_top_k_truncation() {
    InvertedIndex index;
    for (int i = 1; i <= 10; ++i) {
        std::string id = "doc_" + std::to_string(i);
        // Varying frequencies
        std::vector<std::string> terms;
        for (int j = 0; j < i; ++j) {
            terms.push_back("term");
        }
        index.add_document(make_doc(id, id, id, "hash_" + id), make_tokens(terms));
    }

    Ranker ranker(index);
    auto results_all = ranker.rank({"term"}, RankingAlgorithm::BM25, MatchMode::ANY_TERM, 0);
    assert(results_all.size() == 10);

    auto results_top3 = ranker.rank({"term"}, RankingAlgorithm::BM25, MatchMode::ANY_TERM, 3);
    assert(results_top3.size() == 3);
    assert(results_top3[0].string_doc_id == results_all[0].string_doc_id);
    assert(results_top3[1].string_doc_id == results_all[1].string_doc_id);
    assert(results_top3[2].string_doc_id == results_all[2].string_doc_id);

    std::cout << "[PASS] test_top_k_truncation" << std::endl;
}

void test_empty_and_unknown_queries() {
    InvertedIndex index;
    index.add_document(make_doc("d1", "D1", "hello world", "h1"), make_tokens({"hello", "world"}));

    Ranker ranker(index);

    // Empty query terms
    auto res_empty = ranker.rank({});
    assert(res_empty.empty());

    // Term not in vocabulary
    auto res_unknown = ranker.rank({"nonexistent"});
    assert(res_unknown.empty());

    // Mixed: one known, one unknown under AND
    auto res_and_unknown = ranker.rank({"hello", "nonexistent"}, RankingAlgorithm::BM25, MatchMode::ALL_TERMS);
    assert(res_and_unknown.empty());

    // Mixed: one known, one unknown under OR
    auto res_or_mixed = ranker.rank({"hello", "nonexistent"}, RankingAlgorithm::BM25, MatchMode::ANY_TERM);
    assert(res_or_mixed.size() == 1);
    assert(res_or_mixed[0].string_doc_id == "d1");

    std::cout << "[PASS] test_empty_and_unknown_queries" << std::endl;
}

int main() {
    std::cout << "Running Retrieval and Ranking C++ unit tests (TF-IDF & BM25)..." << std::endl;
    test_hand_checkable_tf_idf();
    test_bm25_length_normalization();
    test_boolean_match_modes();
    test_deterministic_tie_breaking();
    test_top_k_truncation();
    test_empty_and_unknown_queries();
    std::cout << "All Retrieval and Ranking unit tests passed successfully!" << std::endl;
    return 0;
}
