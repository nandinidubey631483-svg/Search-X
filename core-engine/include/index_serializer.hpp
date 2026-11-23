#pragma once

#include "inverted_index.hpp"

#include <string>

namespace searchx {

/**
 * @brief Binary serializer and deserializer for InvertedIndex.
 * Complies with PROJECT_CONTEXT.md Milestone 5.
 */
class IndexSerializer {
public:
    static constexpr const char* MAGIC_HEADER = "SEARCHX_IDX";
    static constexpr const char* MAGIC_FOOTER = "SEARCHX_END";
    static constexpr uint32_t FORMAT_VERSION = 1;

    /**
     * @brief Serialize InvertedIndex to a binary file.
     * @param index InvertedIndex to save.
     * @param filepath Destination file path.
     * @param error_msg Optional pointer to receive detailed error message on failure.
     * @return true on success, false on error.
     */
    static bool save(const InvertedIndex& index, const std::string& filepath, std::string* error_msg = nullptr);

    /**
     * @brief Deserialize and validate InvertedIndex from a binary file.
     * Preserves existing index state if deserialization fails due to corruption.
     * @param index InvertedIndex to populate.
     * @param filepath Source file path.
     * @param error_msg Optional pointer to receive detailed error message on failure.
     * @return true on success, false on corruption or I/O error.
     */
    static bool load(InvertedIndex& index, const std::string& filepath, std::string* error_msg = nullptr);
};

} // namespace searchx
