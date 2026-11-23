#include "ranking.hpp"

#include <algorithm>
#include <cmath>
#include <unordered_map>

namespace searchx {

Ranker::Ranker(const InvertedIndex& index, BM25Params bm25_params)
    : index_(index), bm25_params_(bm25_params) {}

void Ranker::set_bm25_params(BM25Params params) {
    bm25_params_ = params;
}

const BM25Params& Ranker::get_bm25_params() const {
    return bm25_params_;
}

double Ranker::compute_tf_idf_term(uint32_t tf, size_t df, size_t N) const {
    if (tf == 0 || df == 0 || N == 0) {
        return 0.0;
    }
    // Sublinear term frequency scaling
    double tf_comp = 1.0 + std::log(static_cast<double>(tf));
    // Smooth inverse document frequency
    double idf = std::log(1.0 + (static_cast<double>(N) / static_cast<double>(df)));
    return tf_comp * idf;
}

double Ranker::compute_bm25_term(uint32_t tf, size_t df, size_t N, uint32_t doc_len, double avgdl) const {
    if (tf == 0 || df == 0 || N == 0) {
        return 0.0;
    }

    // Robertson-Spärck Jones IDF with smoothing (+1.0 prevents negative IDF for high-frequency terms)
    double numerator = static_cast<double>(N) - static_cast<double>(df) + 0.5;
    double denominator = static_cast<double>(df) + 0.5;
    double idf = std::log((numerator / denominator) + 1.0);
    if (idf < 0.0) {
        idf = 0.0;
    }

    // Document length normalization
    double len_norm = 1.0 - bm25_params_.b;
    if (avgdl > 0.0) {
        len_norm += bm25_params_.b * (static_cast<double>(doc_len) / avgdl);
    }

    // Term frequency saturation
    double tf_d = static_cast<double>(tf);
    double tf_comp = (tf_d * (bm25_params_.k1 + 1.0)) / (tf_d + bm25_params_.k1 * len_norm);

    return idf * tf_comp;
}

std::vector<ScoredResult> Ranker::rank(
    const std::vector<std::string>& query_terms,
    RankingAlgorithm algo,
    MatchMode mode,
    size_t top_k
) const {
    // Collect non-empty distinct query terms
    std::vector<std::string> valid_terms;
    for (const auto& term : query_terms) {
        if (!term.empty()) {
            valid_terms.push_back(term);
        }
    }

    if (valid_terms.empty() || index_.total_documents() == 0) {
        return {};
    }

    // Identify candidate documents
    std::vector<uint32_t> candidates;
    if (mode == MatchMode::ALL_TERMS) {
        candidates = index_.lookup_and(valid_terms);
    } else {
        candidates = index_.lookup_or(valid_terms);
    }

    if (candidates.empty()) {
        return {};
    }

    size_t N = index_.total_documents();
    double avgdl = index_.average_document_length();

    // Cache posting lists and document frequencies for query terms
    struct TermPostingInfo {
        size_t df = 0;
        const std::vector<Posting>* postings = nullptr;
    };
    std::vector<TermPostingInfo> term_infos;
    term_infos.reserve(valid_terms.size());

    for (const auto& term : valid_terms) {
        const auto* postings = index_.get_postings(term);
        size_t df = index_.document_frequency(term);
        term_infos.push_back(TermPostingInfo{df, postings});
    }

    std::vector<ScoredResult> results;
    results.reserve(candidates.size());

    for (uint32_t doc_id : candidates) {
        double score = 0.0;
        uint32_t doc_len = index_.document_length(doc_id);

        for (const auto& info : term_infos) {
            if (!info.postings || info.df == 0) {
                continue;
            }

            // Binary search in posting list (postings are sorted in ascending doc_id)
            auto it = std::lower_bound(
                info.postings->begin(), info.postings->end(), doc_id,
                [](const Posting& p, uint32_t id) { return p.doc_id < id; }
            );

            if (it != info.postings->end() && it->doc_id == doc_id) {
                uint32_t tf = it->term_frequency;
                if (algo == RankingAlgorithm::TF_IDF) {
                    score += compute_tf_idf_term(tf, info.df, N);
                } else {
                    score += compute_bm25_term(tf, info.df, N, doc_len, avgdl);
                }
            }
        }

        if (score > 0.0) {
            const Document* doc_ptr = index_.get_document(doc_id);
            std::string str_id = doc_ptr ? doc_ptr->document_id : "";
            results.push_back(ScoredResult{doc_id, std::move(str_id), score});
        }
    }

    // Deterministic sort: descending score; ties broken by ascending doc_id
    std::sort(results.begin(), results.end());

    // Truncate to top_k if requested
    if (top_k > 0 && results.size() > top_k) {
        results.resize(top_k);
    }

    return results;
}

} // namespace searchx
