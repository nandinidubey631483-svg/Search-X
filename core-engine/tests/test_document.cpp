#include "document.hpp"
#include <cassert>
#include <iostream>

void test_token_equality() {
    searchx::Token t1{"search", 0, 0, 6};
    searchx::Token t2{"search", 0, 0, 6};
    searchx::Token t3{"engine", 1, 7, 13};

    assert(t1 == t2);
    assert(!(t1 == t3));
    std::cout << "[PASS] test_token_equality" << std::endl;
}

void test_document_validity() {
    searchx::Document doc;
    doc.document_id = "doc_1";
    doc.title = "Search Engines";
    doc.content = "Inverted index and ranking algorithms.";
    doc.content_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
    doc.fetched_at = "2026-11-23T09:00:00Z";
    doc.status = "ingested";

    assert(doc.is_valid());

    // Missing document_id
    searchx::Document invalid_doc = doc;
    invalid_doc.document_id = "";
    assert(!invalid_doc.is_valid());

    // Missing content
    invalid_doc = doc;
    invalid_doc.content = "";
    assert(!invalid_doc.is_valid());

    // Invalid status
    invalid_doc = doc;
    invalid_doc.status = "not_a_valid_status";
    assert(!invalid_doc.is_valid());

    std::cout << "[PASS] test_document_validity" << std::endl;
}

void test_document_deduplication() {
    searchx::Document d1;
    d1.content_hash = "abc123hash";

    searchx::Document d2;
    d2.content_hash = "abc123hash";

    searchx::Document d3;
    d3.content_hash = "xyz999hash";

    assert(d1.is_duplicate_of(d2));
    assert(!d1.is_duplicate_of(d3));

    std::cout << "[PASS] test_document_deduplication" << std::endl;
}

void test_document_json_serialization() {
    searchx::Document doc;
    doc.document_id = "doc_42";
    doc.source_url = "https://example.com/test";
    doc.title = "Test \"Special\" & 'Chars'";
    doc.content = "Line 1\nLine 2";
    doc.content_hash = "hash123";
    doc.fetched_at = "2026-11-23T09:00:00Z";
    doc.status = "ingested";

    std::string json = doc.to_json();
    assert(json.find("\"document_id\":\"doc_42\"") != std::string::npos);
    assert(json.find("\\\"Special\\\"") != std::string::npos);
    assert(json.find("\\n") != std::string::npos);

    std::cout << "[PASS] test_document_json_serialization" << std::endl;
}

int main() {
    std::cout << "Running C++ document contract tests..." << std::endl;
    test_token_equality();
    test_document_validity();
    test_document_deduplication();
    test_document_json_serialization();
    std::cout << "All C++ document contract tests passed successfully!" << std::endl;
    return 0;
}
