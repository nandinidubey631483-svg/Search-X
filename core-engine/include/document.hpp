#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
#include <sstream>
#include <iomanip>
#include <algorithm>

namespace searchx {

/**
 * @brief Token with positional metadata and character offsets.
 * Strictly mirrors Python Token in crawler/app/models.py and ADR 0001.
 */
struct Token {
    std::string term;
    uint32_t position = 0;
    uint32_t char_start = 0;
    uint32_t char_end = 0;

    bool operator==(const Token& other) const {
        return term == other.term &&
               position == other.position &&
               char_start == other.char_start &&
               char_end == other.char_end;
    }
};

/**
 * @brief Canonical Document model for SearchX.
 * Strictly mirrors Python Document in crawler/app/models.py and ADR 0001.
 */
struct Document {
    std::string document_id;
    std::string source_url;
    std::string title;
    std::string content;
    std::string description;
    std::string language = "en";
    std::string content_hash;
    std::string fetched_at;
    std::string status = "ingested";

    /**
     * @brief Validate that required fields satisfy the contract.
     * @return true if document is valid, false otherwise.
     */
    bool is_valid() const {
        if (document_id.empty()) return false;
        if (title.empty() && source_url.empty()) return false;
        if (content.empty()) return false;
        if (content_hash.empty()) return false;
        if (fetched_at.empty()) return false;
        if (status != "ingested" && status != "indexed" &&
            status != "failed" && status != "archived") {
            return false;
        }
        return true;
    }

    /**
     * @brief Checks if this document has identical content hash to another document.
     */
    bool is_duplicate_of(const Document& other) const {
        return !content_hash.empty() && content_hash == other.content_hash;
    }

    /**
     * @brief Escapes a string for JSON output.
     */
    static std::string escape_json(std::string_view s) {
        std::ostringstream o;
        for (char c : s) {
            switch (c) {
                case '"': o << "\\\""; break;
                case '\\': o << "\\\\"; break;
                case '\b': o << "\\b"; break;
                case '\f': o << "\\f"; break;
                case '\n': o << "\\n"; break;
                case '\r': o << "\\r"; break;
                case '\t': o << "\\t"; break;
                default:
                    if (static_cast<unsigned char>(c) <= 0x1f) {
                        o << "\\u" << std::hex << std::setw(4) << std::setfill('0') << static_cast<int>(c);
                    } else {
                        o << c;
                    }
            }
        }
        return o.str();
    }

    /**
     * @brief Serialize Document to a JSON string.
     */
    std::string to_json() const {
        std::ostringstream ss;
        ss << "{"
           << "\"document_id\":\"" << escape_json(document_id) << "\","
           << "\"source_url\":\"" << escape_json(source_url) << "\","
           << "\"title\":\"" << escape_json(title) << "\","
           << "\"content\":\"" << escape_json(content) << "\","
           << "\"description\":\"" << escape_json(description) << "\","
           << "\"language\":\"" << escape_json(language) << "\","
           << "\"content_hash\":\"" << escape_json(content_hash) << "\","
           << "\"fetched_at\":\"" << escape_json(fetched_at) << "\","
           << "\"status\":\"" << escape_json(status) << "\""
           << "}";
        return ss.str();
    }
};

} // namespace searchx
