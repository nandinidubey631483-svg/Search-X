#include "inverted_index.hpp"
#include "index_serializer.hpp"
#include "ranking.hpp"
#include "document.hpp"

// Ensure assert() is ALWAYS active in test suite, even when compiled in Release mode (-DNDEBUG)
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

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

void test_roundtrip_save_and_load() {
    const std::string filepath = "test_roundtrip.bin";

    InvertedIndex original;
    original.add_document(
        make_doc("d1", "Information Retrieval", "information retrieval and web search", "h1"),
        make_tokens({"information", "retrieval", "and", "web", "search"})
    );
    original.add_document(
        make_doc("d2", "Search Engine", "search engine architecture retrieval", "h2"),
        make_tokens({"search", "engine", "architecture", "retrieval"})
    );
    original.add_document(
        make_doc("d3", "Database Systems", "database systems and storage", "h3"),
        make_tokens({"database", "systems", "and", "storage"})
    );

    // Baseline ranking queries on original index
    Ranker ranker_orig(original);
    auto orig_results_bm25 = ranker_orig.rank({"retrieval", "search"}, RankingAlgorithm::BM25, MatchMode::ANY_TERM);
    auto orig_results_tfidf = ranker_orig.rank({"retrieval", "search"}, RankingAlgorithm::TF_IDF, MatchMode::ALL_TERMS);

    // Save to disk
    std::string err;
    bool save_ok = original.save(filepath, &err);
    assert(save_ok);

    // Load into a fresh index
    InvertedIndex loaded;
    bool load_ok = loaded.load(filepath, &err);
    assert(load_ok);

    // Verify corpus statistics
    assert(loaded.total_documents() == original.total_documents());
    assert(loaded.vocabulary_size() == original.vocabulary_size());
    assert(loaded.average_document_length() == original.average_document_length());

    // Verify document lookups
    for (const char* id : {"d1", "d2", "d3"}) {
        const Document* orig_d = original.get_document_by_string_id(id);
        const Document* load_d = loaded.get_document_by_string_id(id);
        assert(orig_d != nullptr);
        assert(load_d != nullptr);
        assert(orig_d->document_id == load_d->document_id);
        assert(orig_d->title == load_d->title);
        assert(orig_d->content == load_d->content);
        assert(orig_d->content_hash == load_d->content_hash);
    }

    // Verify posting lists
    for (const char* term : {"information", "retrieval", "search", "database"}) {
        const auto* p_orig = original.get_postings(term);
        const auto* p_load = loaded.get_postings(term);
        assert(p_orig != nullptr);
        assert(p_load != nullptr);
        assert(p_orig->size() == p_load->size());
        for (size_t i = 0; i < p_orig->size(); ++i) {
            assert((*p_orig)[i].term_frequency == (*p_load)[i].term_frequency);
            assert((*p_orig)[i].positions == (*p_load)[i].positions);
        }
    }

    // Run identical ranking queries on loaded index
    Ranker ranker_loaded(loaded);
    auto load_results_bm25 = ranker_loaded.rank({"retrieval", "search"}, RankingAlgorithm::BM25, MatchMode::ANY_TERM);
    auto load_results_tfidf = ranker_loaded.rank({"retrieval", "search"}, RankingAlgorithm::TF_IDF, MatchMode::ALL_TERMS);

    assert(load_results_bm25.size() == orig_results_bm25.size());
    for (size_t i = 0; i < load_results_bm25.size(); ++i) {
        assert(load_results_bm25[i].string_doc_id == orig_results_bm25[i].string_doc_id);
        assert(std::abs(load_results_bm25[i].score - orig_results_bm25[i].score) < 1e-9);
    }

    assert(load_results_tfidf.size() == orig_results_tfidf.size());
    for (size_t i = 0; i < load_results_tfidf.size(); ++i) {
        assert(load_results_tfidf[i].string_doc_id == orig_results_tfidf[i].string_doc_id);
        assert(std::abs(load_results_tfidf[i].score - orig_results_tfidf[i].score) < 1e-9);
    }

    std::remove(filepath.c_str());
    std::cout << "[PASS] test_roundtrip_save_and_load" << std::endl;
}

void test_non_existent_file() {
    InvertedIndex index;
    std::string err;
    bool ok = index.load("path_does_not_exist_at_all.idx", &err);
    assert(!ok);
    assert(!err.empty());
    std::cout << "[PASS] test_non_existent_file" << std::endl;
}

void test_corrupted_header() {
    const std::string filepath = "test_corrupt_header.bin";
    {
        std::ofstream ofs(filepath, std::ios::binary);
        ofs << "INVALID_HEADER_GARBAGE_BYTES_HERE";
    }

    InvertedIndex index;
    std::string err;
    bool ok = index.load(filepath, &err);
    assert(!ok);
    assert(err.find("header signature mismatch") != std::string::npos);

    std::remove(filepath.c_str());
    std::cout << "[PASS] test_corrupted_header" << std::endl;
}

void test_truncated_file() {
    const std::string filepath_valid = "test_valid_for_trunc.bin";
    const std::string filepath_trunc = "test_truncated.bin";

    InvertedIndex index;
    index.add_document(
        make_doc("d1", "Title", "the quick brown fox", "h1"),
        make_tokens({"the", "quick", "brown", "fox"})
    );
    bool save_ok = index.save(filepath_valid);
    assert(save_ok);

    // Read half of the file and write to truncated file
    std::ifstream src(filepath_valid, std::ios::binary | std::ios::ate);
    assert(src.is_open());
    std::streamsize size = src.tellg();
    assert(size > 0);
    src.seekg(0, std::ios::beg);
    std::vector<char> buffer(size / 2);
    src.read(buffer.data(), buffer.size());
    src.close();

    {
        std::ofstream dst(filepath_trunc, std::ios::binary);
        dst.write(buffer.data(), buffer.size());
    }

    InvertedIndex loaded;
    std::string err;
    bool ok = loaded.load(filepath_trunc, &err);
    assert(!ok);
    assert(!err.empty());

    std::remove(filepath_valid.c_str());
    std::remove(filepath_trunc.c_str());
    std::cout << "[PASS] test_truncated_file" << std::endl;
}

void test_missing_footer() {
    const std::string filepath_valid = "test_valid_footer.bin";
    const std::string filepath_bad_footer = "test_bad_footer.bin";

    InvertedIndex index;
    index.add_document(
        make_doc("d1", "Title", "content text here", "h1"),
        make_tokens({"content", "text", "here"})
    );
    bool save_ok = index.save(filepath_valid);
    assert(save_ok);

    // Remove footer bytes (last 11 bytes)
    std::ifstream src(filepath_valid, std::ios::binary | std::ios::ate);
    assert(src.is_open());
    std::streamsize size = src.tellg();
    src.seekg(0, std::ios::beg);
    size_t footer_len = std::strlen(IndexSerializer::MAGIC_FOOTER);
    assert(size > static_cast<std::streamsize>(footer_len));

    std::vector<char> buffer(size - footer_len);
    src.read(buffer.data(), buffer.size());
    src.close();

    {
        std::ofstream dst(filepath_bad_footer, std::ios::binary);
        dst.write(buffer.data(), buffer.size());
    }

    InvertedIndex loaded;
    std::string err;
    bool ok = loaded.load(filepath_bad_footer, &err);
    assert(!ok);
    assert(err.find("footer signature mismatch") != std::string::npos);

    std::remove(filepath_valid.c_str());
    std::remove(filepath_bad_footer.c_str());
    std::cout << "[PASS] test_missing_footer" << std::endl;
}

void test_state_preservation_on_load_failure() {
    const std::string filepath_corrupt = "test_corrupt_rollback.bin";
    {
        std::ofstream ofs(filepath_corrupt, std::ios::binary);
        ofs << "INVALID_DATA";
    }

    InvertedIndex index;
    index.add_document(
        make_doc("safe_doc", "Safe Doc", "this document should remain untouched", "h_safe"),
        make_tokens({"this", "document", "should", "remain", "untouched"})
    );
    assert(index.total_documents() == 1);
    assert(index.has_document("safe_doc"));

    // Attempting to load corrupted file into this index
    std::string err;
    bool ok = index.load(filepath_corrupt, &err);
    assert(!ok);

    // Verify original index state was preserved without partial destruction
    assert(index.total_documents() == 1);
    assert(index.has_document("safe_doc"));
    assert(index.lookup_term("untouched").size() == 1);

    std::remove(filepath_corrupt.c_str());
    std::cout << "[PASS] test_state_preservation_on_load_failure" << std::endl;
}

int main() {
    std::cout << "Running Index Persistence C++ unit tests..." << std::endl;
    test_roundtrip_save_and_load();
    test_non_existent_file();
    test_corrupted_header();
    test_truncated_file();
    test_missing_footer();
    test_state_preservation_on_load_failure();
    std::cout << "All Index Persistence unit tests passed successfully!" << std::endl;
    return 0;
}
