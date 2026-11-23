#pragma once

#include "document.hpp"

#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <optional>
#include <algorithm>

namespace searchx {

/**
 * @brief Represents an entry in a term's posting list.
 * Identifies the document, frequency of occurrence, and token positions.
 */
struct Posting {
    uint32_t doc_id = 0;
    uint32_t term_frequency = 0;
    std::vector<uint32_t> positions;

    bool operator==(const Posting& other) const {
        return doc_id == other.doc_id &&
               term_frequency == other.term_frequency &&
               positions == other.positions;
    }
};

/**
 * @brief Core Inverted Index Engine for SearchX.
 * Maps terms to postings, preserves positional data, and maintains corpus statistics.
 *
 * Data structure decisions & trade-offs:
 * - Term Dictionary: std::unordered_map<std::string, std::vector<Posting>>
 *   Average O(1) term lookup time vs O(log T) in std::map.
 * - Postings: std::vector<Posting>
 *   Contiguous memory layout ensures CPU cache friendliness and fast traversal.
 * - Document storage: std::unordered_map<uint32_t, Document>
 *   O(1) lookup of document metadata by internal integer ID.
 */
class InvertedIndex {
public:
    InvertedIndex() = default;

    /**
     * @brief Add or re-index a document with its pre-tokenized tokens.
     * Rejects duplicate documents based on content_hash.
     * If the document_id already exists with different content, it updates it cleanly.
     * @return true if successfully added or updated, false if rejected (e.g. duplicate or invalid).
     */
    bool add_document(const Document& doc, const std::vector<Token>& tokens);

    /**
     * @brief Remove a document and its postings from the index.
     * @return true if removed, false if not found.
     */
    bool remove_document(const std::string& string_doc_id);

    /**
     * @brief Check whether a document ID is present in the index.
     */
    bool has_document(const std::string& string_doc_id) const;

    /**
     * @brief Retrieve document metadata by internal numeric ID.
     */
    const Document* get_document(uint32_t doc_id) const;

    /**
     * @brief Retrieve document metadata by external string ID.
     */
    const Document* get_document_by_string_id(const std::string& string_doc_id) const;

    /**
     * @brief Resolve external string ID to internal numeric ID.
     */
    std::optional<uint32_t> get_internal_doc_id(const std::string& string_doc_id) const;

    /**
     * @brief Retrieve pointer to postings list for a given term.
     * @return pointer to postings vector or nullptr if term is not in dictionary.
     */
    const std::vector<Posting>* get_postings(const std::string& term) const;

    /**
     * @brief Single-term lookup: returns document IDs containing the term.
     */
    std::vector<uint32_t> lookup_term(const std::string& term) const;

    /**
     * @brief Boolean AND lookup: returns document IDs containing all specified terms.
     */
    std::vector<uint32_t> lookup_and(const std::vector<std::string>& terms) const;

    /**
     * @brief Boolean OR lookup: returns document IDs containing at least one term.
     */
    std::vector<uint32_t> lookup_or(const std::vector<std::string>& terms) const;

    /**
     * @brief Total number of indexed documents in the corpus (N).
     */
    size_t total_documents() const;

    /**
     * @brief Total distinct terms in the vocabulary.
     */
    size_t vocabulary_size() const;

    /**
     * @brief Document frequency (DF): number of documents containing the term.
     */
    size_t document_frequency(const std::string& term) const;

    /**
     * @brief Total token length for a given document.
     */
    uint32_t document_length(uint32_t doc_id) const;

    /**
     * @brief Average document length across the entire indexed corpus (avgdl).
     */
    double average_document_length() const;

    /**
     * @brief Clear all indexed data, metadata, and statistics.
     */
    void clear();

private:
    uint32_t next_doc_id_ = 1;
    uint64_t total_corpus_tokens_ = 0;

    // Dictionary: term -> list of Postings
    std::unordered_map<std::string, std::vector<Posting>> dictionary_;

    // Document metadata storage: internal numeric doc_id -> Document
    std::unordered_map<uint32_t, Document> documents_;

    // External string ID -> internal numeric doc_id
    std::unordered_map<std::string, uint32_t> string_id_to_doc_id_;

    // Content hash -> internal numeric doc_id (for deduplication)
    std::unordered_map<std::string, uint32_t> hash_to_doc_id_;

    // Internal doc_id -> total token count in that document
    std::unordered_map<uint32_t, uint32_t> doc_lengths_;

    // Internal doc_id -> set of distinct terms present in that document (for fast removal)
    std::unordered_map<uint32_t, std::unordered_set<std::string>> doc_terms_;
};

} // namespace searchx
