#pragma once

#include "inverted_index.hpp"

#include <cmath>
#include <cstdint>
#include <string>
#include <vector>

namespace searchx {

/**
 * @brief Ranking algorithm selection.
 */
enum class RankingAlgorithm {
    TF_IDF,
    BM25
};

/**
 * @brief Document candidate matching mode.
 */
enum class MatchMode {
    ANY_TERM, // Boolean OR: score documents containing at least one query term
    ALL_TERMS // Boolean AND: score documents containing all query terms
};

/**
 * @brief Configurable parameters for Okapi BM25 scoring.
 */
struct BM25Params {
    double k1 = 1.2;  // Term frequency saturation parameter (typically 1.2 - 2.0)
    double b = 0.75;  // Document length normalization parameter (0.0 - 1.0)
};

/**
 * @brief Search result with document metadata reference and relevance score.
 */
struct ScoredResult {
    uint32_t doc_id = 0;
    std::string string_doc_id;
    double score = 0.0;

    /**
     * @brief Strict deterministic tie-breaking:
     * Descending score; if scores are equal within epsilon, ascending doc_id.
     */
    bool operator<(const ScoredResult& other) const {
        constexpr double EPS = 1e-9;
        if (std::abs(score - other.score) > EPS) {
            return score > other.score;
        }
        return doc_id < other.doc_id;
    }
};

/**
 * @brief Relevance Ranker implementing TF-IDF and Okapi BM25 algorithms.
 * Complies with PROJECT_CONTEXT.md Module E.
 */
class Ranker {
public:
    explicit Ranker(const InvertedIndex& index, BM25Params bm25_params = BM25Params{});

    /**
     * @brief Compute TF-IDF contribution for a single term in a document.
     * Formula:
     *   TF(t, d) = tf > 0 ? (1.0 + ln(tf)) : 0.0
     *   IDF(t) = ln(1.0 + (N / df))
     *   TF-IDF = TF(t, d) * IDF(t)
     */
    double compute_tf_idf_term(uint32_t tf, size_t df, size_t N) const;

    /**
     * @brief Compute Okapi BM25 contribution for a single term in a document.
     * Formula:
     *   IDF(t) = ln((N - df + 0.5) / (df + 0.5) + 1.0)
     *   TF_comp = (tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * (doc_len / avgdl)))
     *   BM25 = IDF(t) * TF_comp
     */
    double compute_bm25_term(uint32_t tf, size_t df, size_t N, uint32_t doc_len, double avgdl) const;

    /**
     * @brief Rank documents against a normalized query terms list.
     * @param query_terms Terms from query (must be normalized).
     * @param algo RankingAlgorithm::BM25 or RankingAlgorithm::TF_IDF.
     * @param mode MatchMode::ANY_TERM (OR) or MatchMode::ALL_TERMS (AND).
     * @param top_k Maximum results to return (0 = return all matches).
     * @return Sorted vector of ScoredResult in descending relevance order.
     */
    std::vector<ScoredResult> rank(
        const std::vector<std::string>& query_terms,
        RankingAlgorithm algo = RankingAlgorithm::BM25,
        MatchMode mode = MatchMode::ANY_TERM,
        size_t top_k = 0
    ) const;

    void set_bm25_params(BM25Params params);
    const BM25Params& get_bm25_params() const;

private:
    const InvertedIndex& index_;
    BM25Params bm25_params_;
};

} // namespace searchx
