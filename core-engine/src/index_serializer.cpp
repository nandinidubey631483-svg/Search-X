#include "index_serializer.hpp"

#include <cstring>
#include <fstream>
#include <iostream>

namespace searchx {

namespace {

template <typename T>
bool write_val(std::ostream& os, const T& val) {
    return static_cast<bool>(os.write(reinterpret_cast<const char*>(&val), sizeof(T)));
}

template <typename T>
bool read_val(std::istream& is, T& val) {
    return static_cast<bool>(is.read(reinterpret_cast<char*>(&val), sizeof(T)));
}

bool write_str(std::ostream& os, const std::string& str) {
    uint32_t len = static_cast<uint32_t>(str.size());
    if (!write_val(os, len)) return false;
    if (len > 0) {
        if (!os.write(str.data(), len)) return false;
    }
    return true;
}

bool read_str(std::istream& is, std::string& str) {
    uint32_t len = 0;
    if (!read_val(is, len)) return false;
    // Bounded allocation protection: 50 MB max string length
    if (len > 50 * 1024 * 1024) return false;
    str.resize(len);
    if (len > 0) {
        if (!is.read(&str[0], len)) return false;
    }
    return true;
}

void set_err(std::string* error_msg, const std::string& msg) {
    if (error_msg) {
        *error_msg = msg;
    }
}

} // namespace

bool IndexSerializer::save(const InvertedIndex& index, const std::string& filepath, std::string* error_msg) {
    std::ofstream ofs(filepath, std::ios::binary | std::ios::trunc);
    if (!ofs.is_open()) {
        set_err(error_msg, "Failed to open destination file for writing: " + filepath);
        return false;
    }

    // 1. Magic Header
    size_t header_len = std::strlen(MAGIC_HEADER);
    if (!ofs.write(MAGIC_HEADER, header_len)) {
        set_err(error_msg, "Failed to write header");
        return false;
    }

    // 2. Format Version
    if (!write_val(ofs, FORMAT_VERSION)) {
        set_err(error_msg, "Failed to write version");
        return false;
    }

    // 3. Corpus metadata
    if (!write_val(ofs, index.next_doc_id_)) return false;
    if (!write_val(ofs, index.total_corpus_tokens_)) return false;

    // 4. Documents count & records
    uint32_t doc_count = static_cast<uint32_t>(index.documents_.size());
    if (!write_val(ofs, doc_count)) return false;

    for (const auto& [doc_id, doc] : index.documents_) {
        if (!write_val(ofs, doc_id)) return false;
        if (!write_str(ofs, doc.document_id)) return false;
        if (!write_str(ofs, doc.source_url)) return false;
        if (!write_str(ofs, doc.title)) return false;
        if (!write_str(ofs, doc.content)) return false;
        if (!write_str(ofs, doc.description)) return false;
        if (!write_str(ofs, doc.language)) return false;
        if (!write_str(ofs, doc.content_hash)) return false;
        if (!write_str(ofs, doc.fetched_at)) return false;
        if (!write_str(ofs, doc.status)) return false;

        auto len_it = index.doc_lengths_.find(doc_id);
        uint32_t doc_len = (len_it != index.doc_lengths_.end()) ? len_it->second : 0;
        if (!write_val(ofs, doc_len)) return false;
    }

    // 5. Dictionary & Posting Lists
    uint32_t vocab_size = static_cast<uint32_t>(index.dictionary_.size());
    if (!write_val(ofs, vocab_size)) return false;

    for (const auto& [term, postings] : index.dictionary_) {
        if (!write_str(ofs, term)) return false;
        uint32_t p_count = static_cast<uint32_t>(postings.size());
        if (!write_val(ofs, p_count)) return false;

        for (const auto& p : postings) {
            if (!write_val(ofs, p.doc_id)) return false;
            if (!write_val(ofs, p.term_frequency)) return false;
            uint32_t pos_count = static_cast<uint32_t>(p.positions.size());
            if (!write_val(ofs, pos_count)) return false;
            for (uint32_t pos : p.positions) {
                if (!write_val(ofs, pos)) return false;
            }
        }
    }

    // 6. Magic Footer
    size_t footer_len = std::strlen(MAGIC_FOOTER);
    if (!ofs.write(MAGIC_FOOTER, footer_len)) {
        set_err(error_msg, "Failed to write footer");
        return false;
    }

    ofs.flush();
    if (!ofs.good()) {
        set_err(error_msg, "Stream error after writing index");
        return false;
    }

    return true;
}

bool IndexSerializer::load(InvertedIndex& index, const std::string& filepath, std::string* error_msg) {
    std::ifstream ifs(filepath, std::ios::binary);
    if (!ifs.is_open()) {
        set_err(error_msg, "Failed to open index file for reading: " + filepath);
        return false;
    }

    // 1. Verify Magic Header
    size_t header_len = std::strlen(MAGIC_HEADER);
    std::string header_buf(header_len, '\0');
    if (!ifs.read(&header_buf[0], header_len) || header_buf != MAGIC_HEADER) {
        set_err(error_msg, "Invalid index file: header signature mismatch");
        return false;
    }

    // 2. Verify Version
    uint32_t version = 0;
    if (!read_val(ifs, version) || version != FORMAT_VERSION) {
        set_err(error_msg, "Unsupported index format version: " + std::to_string(version));
        return false;
    }

    // Use a temporary index object to guarantee existing index is unchanged if load fails
    InvertedIndex temp;

    // 3. Corpus metadata
    if (!read_val(ifs, temp.next_doc_id_)) {
        set_err(error_msg, "Corrupt file: unexpected EOF reading next_doc_id");
        return false;
    }
    if (!read_val(ifs, temp.total_corpus_tokens_)) {
        set_err(error_msg, "Corrupt file: unexpected EOF reading total_corpus_tokens");
        return false;
    }

    // 4. Documents
    uint32_t doc_count = 0;
    if (!read_val(ifs, doc_count)) {
        set_err(error_msg, "Corrupt file: unexpected EOF reading doc_count");
        return false;
    }

    for (uint32_t i = 0; i < doc_count; ++i) {
        uint32_t doc_id = 0;
        Document doc;
        uint32_t doc_len = 0;

        if (!read_val(ifs, doc_id)) { set_err(error_msg, "Corrupt doc_id"); return false; }
        if (!read_str(ifs, doc.document_id)) { set_err(error_msg, "Corrupt document_id"); return false; }
        if (!read_str(ifs, doc.source_url)) { set_err(error_msg, "Corrupt source_url"); return false; }
        if (!read_str(ifs, doc.title)) { set_err(error_msg, "Corrupt title"); return false; }
        if (!read_str(ifs, doc.content)) { set_err(error_msg, "Corrupt content"); return false; }
        if (!read_str(ifs, doc.description)) { set_err(error_msg, "Corrupt description"); return false; }
        if (!read_str(ifs, doc.language)) { set_err(error_msg, "Corrupt language"); return false; }
        if (!read_str(ifs, doc.content_hash)) { set_err(error_msg, "Corrupt content_hash"); return false; }
        if (!read_str(ifs, doc.fetched_at)) { set_err(error_msg, "Corrupt fetched_at"); return false; }
        if (!read_str(ifs, doc.status)) { set_err(error_msg, "Corrupt status"); return false; }
        if (!read_val(ifs, doc_len)) { set_err(error_msg, "Corrupt doc_len"); return false; }

        if (!doc.is_valid()) {
            set_err(error_msg, "Invalid document record encountered during deserialization");
            return false;
        }

        temp.documents_[doc_id] = doc;
        temp.string_id_to_doc_id_[doc.document_id] = doc_id;
        temp.hash_to_doc_id_[doc.content_hash] = doc_id;
        temp.doc_lengths_[doc_id] = doc_len;
    }

    // 5. Dictionary & Posting Lists
    uint32_t vocab_size = 0;
    if (!read_val(ifs, vocab_size)) {
        set_err(error_msg, "Corrupt file: unexpected EOF reading vocab_size");
        return false;
    }

    for (uint32_t i = 0; i < vocab_size; ++i) {
        std::string term;
        uint32_t p_count = 0;

        if (!read_str(ifs, term)) { set_err(error_msg, "Corrupt term"); return false; }
        if (!read_val(ifs, p_count)) { set_err(error_msg, "Corrupt postings count"); return false; }

        std::vector<Posting> postings;
        postings.reserve(p_count);

        for (uint32_t j = 0; j < p_count; ++j) {
            Posting p;
            uint32_t pos_count = 0;

            if (!read_val(ifs, p.doc_id)) { set_err(error_msg, "Corrupt posting doc_id"); return false; }
            if (!read_val(ifs, p.term_frequency)) { set_err(error_msg, "Corrupt posting tf"); return false; }
            if (!read_val(ifs, pos_count)) { set_err(error_msg, "Corrupt pos_count"); return false; }

            p.positions.resize(pos_count);
            for (uint32_t k = 0; k < pos_count; ++k) {
                if (!read_val(ifs, p.positions[k])) { set_err(error_msg, "Corrupt position entry"); return false; }
            }

            temp.doc_terms_[p.doc_id].insert(term);
            postings.push_back(std::move(p));
        }

        temp.dictionary_[std::move(term)] = std::move(postings);
    }

    // 6. Verify Magic Footer
    size_t footer_len = std::strlen(MAGIC_FOOTER);
    std::string footer_buf(footer_len, '\0');
    if (!ifs.read(&footer_buf[0], footer_len) || footer_buf != MAGIC_FOOTER) {
        set_err(error_msg, "Corrupt or truncated index file: footer signature mismatch");
        return false;
    }

    // Deserialization succeeded completely -> atomic swap
    index = std::move(temp);
    return true;
}

// InvertedIndex member methods delegating to IndexSerializer
bool InvertedIndex::save(const std::string& filepath, std::string* error_msg) const {
    return IndexSerializer::save(*this, filepath, error_msg);
}

bool InvertedIndex::load(const std::string& filepath, std::string* error_msg) {
    return IndexSerializer::load(*this, filepath, error_msg);
}

} // namespace searchx
