#include "inverted_index.hpp"

#include <algorithm>
#include <numeric>

namespace searchx {

bool InvertedIndex::add_document(const Document& doc, const std::vector<Token>& tokens) {
    if (!doc.is_valid()) {
        return false;
    }

    // Check duplicate content via content_hash
    auto hash_it = hash_to_doc_id_.find(doc.content_hash);
    if (hash_it != hash_to_doc_id_.end()) {
        uint32_t existing_doc_id = hash_it->second;
        const Document* existing_doc = get_document(existing_doc_id);
        if (existing_doc && existing_doc->document_id != doc.document_id) {
            // Distinct document ID with identical content: reject duplicate
            return false;
        }
    }

    // If document_id already exists, remove previous version first (clean update)
    if (has_document(doc.document_id)) {
        remove_document(doc.document_id);
    }

    // Allocate internal numeric doc_id
    uint32_t doc_id = next_doc_id_++;

    // Register metadata lookups
    documents_[doc_id] = doc;
    string_id_to_doc_id_[doc.document_id] = doc_id;
    hash_to_doc_id_[doc.content_hash] = doc_id;

    // Aggregate tokens by term: calculate frequencies and collect positions
    struct TermAccumulator {
        uint32_t frequency = 0;
        std::vector<uint32_t> positions;
    };
    std::unordered_map<std::string, TermAccumulator> term_stats;

    for (const auto& token : tokens) {
        if (token.term.empty()) continue;
        auto& acc = term_stats[token.term];
        acc.frequency++;
        acc.positions.push_back(token.position);
    }

    // Append to posting lists
    for (auto& [term, acc] : term_stats) {
        dictionary_[term].push_back(Posting{doc_id, acc.frequency, std::move(acc.positions)});
        doc_terms_[doc_id].insert(term);
    }

    // Track document length and corpus token total
    uint32_t doc_len = static_cast<uint32_t>(tokens.size());
    doc_lengths_[doc_id] = doc_len;
    total_corpus_tokens_ += doc_len;

    return true;
}

bool InvertedIndex::remove_document(const std::string& string_doc_id) {
    auto id_it = string_id_to_doc_id_.find(string_doc_id);
    if (id_it == string_id_to_doc_id_.end()) {
        return false;
    }

    uint32_t doc_id = id_it->second;

    // Remove postings from dictionary for all terms contained in this document
    auto terms_it = doc_terms_.find(doc_id);
    if (terms_it != doc_terms_.end()) {
        for (const auto& term : terms_it->second) {
            auto dict_it = dictionary_.find(term);
            if (dict_it != dictionary_.end()) {
                auto& postings = dict_it->second;
                postings.erase(
                    std::remove_if(postings.begin(), postings.end(),
                                   [doc_id](const Posting& p) { return p.doc_id == doc_id; }),
                    postings.end()
                );
                // If posting list is now empty, remove term from dictionary
                if (postings.empty()) {
                    dictionary_.erase(dict_it);
                }
            }
        }
        doc_terms_.erase(terms_it);
    }

    // Subtract document length from corpus token count
    auto len_it = doc_lengths_.find(doc_id);
    if (len_it != doc_lengths_.end()) {
        total_corpus_tokens_ -= len_it->second;
        doc_lengths_.erase(len_it);
    }

    // Clean up metadata lookups
    auto doc_it = documents_.find(doc_id);
    if (doc_it != documents_.end()) {
        hash_to_doc_id_.erase(doc_it->second.content_hash);
        documents_.erase(doc_it);
    }
    string_id_to_doc_id_.erase(id_it);

    return true;
}

bool InvertedIndex::has_document(const std::string& string_doc_id) const {
    return string_id_to_doc_id_.find(string_doc_id) != string_id_to_doc_id_.end();
}

const Document* InvertedIndex::get_document(uint32_t doc_id) const {
    auto it = documents_.find(doc_id);
    return it != documents_.end() ? &it->second : nullptr;
}

const Document* InvertedIndex::get_document_by_string_id(const std::string& string_doc_id) const {
    auto id_it = string_id_to_doc_id_.find(string_doc_id);
    if (id_it == string_id_to_doc_id_.end()) {
        return nullptr;
    }
    return get_document(id_it->second);
}

std::optional<uint32_t> InvertedIndex::get_internal_doc_id(const std::string& string_doc_id) const {
    auto it = string_id_to_doc_id_.find(string_doc_id);
    if (it != string_id_to_doc_id_.end()) {
        return it->second;
    }
    return std::nullopt;
}

const std::vector<Posting>* InvertedIndex::get_postings(const std::string& term) const {
    auto it = dictionary_.find(term);
    return it != dictionary_.end() ? &it->second : nullptr;
}

std::vector<uint32_t> InvertedIndex::lookup_term(const std::string& term) const {
    const auto* postings = get_postings(term);
    if (!postings) {
        return {};
    }
    std::vector<uint32_t> doc_ids;
    doc_ids.reserve(postings->size());
    for (const auto& p : *postings) {
        doc_ids.push_back(p.doc_id);
    }
    return doc_ids;
}

std::vector<uint32_t> InvertedIndex::lookup_and(const std::vector<std::string>& terms) const {
    // Filter out empty terms
    std::vector<std::string> valid_terms;
    for (const auto& t : terms) {
        if (!t.empty()) valid_terms.push_back(t);
    }

    if (valid_terms.empty()) {
        return {};
    }

    // Collect posting lists; if any term does not exist, AND intersection is empty
    std::vector<const std::vector<Posting>*> posting_lists;
    posting_lists.reserve(valid_terms.size());

    for (const auto& term : valid_terms) {
        const auto* p = get_postings(term);
        if (!p || p->empty()) {
            return {};
        }
        posting_lists.push_back(p);
    }

    // Sort posting lists by size ascending to minimize intersection steps
    std::sort(posting_lists.begin(), posting_lists.end(),
              [](const auto* a, const auto* b) { return a->size() < b->size(); });

    // Initialize result with document IDs from smallest posting list
    std::vector<uint32_t> result;
    result.reserve(posting_lists[0]->size());
    for (const auto& posting : *posting_lists[0]) {
        result.push_back(posting.doc_id);
    }

    // Intersect sequentially with remaining posting lists using two-pointer merge
    for (size_t i = 1; i < posting_lists.size(); ++i) {
        const auto& next_list = *posting_lists[i];
        std::vector<uint32_t> intersected;
        size_t p1 = 0, p2 = 0;

        while (p1 < result.size() && p2 < next_list.size()) {
            uint32_t id1 = result[p1];
            uint32_t id2 = next_list[p2].doc_id;

            if (id1 == id2) {
                intersected.push_back(id1);
                ++p1;
                ++p2;
            } else if (id1 < id2) {
                ++p1;
            } else {
                ++p2;
            }
        }

        result = std::move(intersected);
        if (result.empty()) {
            break;
        }
    }

    return result;
}

std::vector<uint32_t> InvertedIndex::lookup_or(const std::vector<std::string>& terms) const {
    std::unordered_set<uint32_t> unique_doc_ids;

    for (const auto& term : terms) {
        if (term.empty()) continue;
        const auto* postings = get_postings(term);
        if (postings) {
            for (const auto& p : *postings) {
                unique_doc_ids.insert(p.doc_id);
            }
        }
    }

    std::vector<uint32_t> result(unique_doc_ids.begin(), unique_doc_ids.end());
    std::sort(result.begin(), result.end());
    return result;
}

size_t InvertedIndex::total_documents() const {
    return documents_.size();
}

size_t InvertedIndex::vocabulary_size() const {
    return dictionary_.size();
}

size_t InvertedIndex::document_frequency(const std::string& term) const {
    const auto* postings = get_postings(term);
    return postings ? postings->size() : 0;
}

uint32_t InvertedIndex::document_length(uint32_t doc_id) const {
    auto it = doc_lengths_.find(doc_id);
    return it != doc_lengths_.end() ? it->second : 0;
}

double InvertedIndex::average_document_length() const {
    size_t n = total_documents();
    return n > 0 ? static_cast<double>(total_corpus_tokens_) / static_cast<double>(n) : 0.0;
}

void InvertedIndex::clear() {
    dictionary_.clear();
    documents_.clear();
    string_id_to_doc_id_.clear();
    hash_to_doc_id_.clear();
    doc_lengths_.clear();
    doc_terms_.clear();
    next_doc_id_ = 1;
    total_corpus_tokens_ = 0;
}

} // namespace searchx
