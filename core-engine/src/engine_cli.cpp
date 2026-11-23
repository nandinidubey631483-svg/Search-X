#include "inverted_index.hpp"
#include "ranking.hpp"
#include "document.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace searchx;

namespace {

// Simple JSON string unescape helper for CLI parsing
std::string unescape_str(const std::string& in) {
    std::string out;
    out.reserve(in.size());
    for (size_t i = 0; i < in.size(); ++i) {
        if (in[i] == '\\' && i + 1 < in.size()) {
            switch (in[i + 1]) {
                case '"': out += '"'; ++i; break;
                case '\\': out += '\\'; ++i; break;
                case 'n': out += '\n'; ++i; break;
                case 'r': out += '\r'; ++i; break;
                case 't': out += '\t'; ++i; break;
                default: out += in[i + 1]; ++i; break;
            }
        } else {
            out += in[i];
        }
    }
    return out;
}

} // namespace

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: searchx_engine <stats|document|search|index|suggestions|vocab> [args...]" << std::endl;
        return 1;
    }

    std::string command = argv[1];

    if (command == "stats") {
        if (argc < 3) {
            std::cerr << "{\"error\": \"Missing index_path\"}" << std::endl;
            return 1;
        }
        std::string index_path = argv[2];
        InvertedIndex index;
        std::string err;
        if (!index.load(index_path, &err)) {
            // Index file might not exist yet -> empty stats
            std::cout << "{\"status\":\"ok\",\"total_documents\":0,\"vocabulary_size\":0,\"average_document_length\":0.0}" << std::endl;
            return 0;
        }

        std::cout << "{"
                  << "\"status\":\"ok\","
                  << "\"total_documents\":" << index.total_documents() << ","
                  << "\"vocabulary_size\":" << index.vocabulary_size() << ","
                  << "\"average_document_length\":" << index.average_document_length()
                  << "}" << std::endl;
        return 0;
    }

    if (command == "document") {
        if (argc < 4) {
            std::cerr << "{\"error\": \"Missing index_path or doc_id\"}" << std::endl;
            return 1;
        }
        std::string index_path = argv[2];
        std::string doc_id = argv[3];

        InvertedIndex index;
        std::string err;
        if (!index.load(index_path, &err)) {
            std::cout << "{\"error\":\"Index not found\"}" << std::endl;
            return 1;
        }

        const Document* doc = index.get_document_by_string_id(doc_id);
        if (!doc) {
            std::cout << "{\"error\":\"Document not found\"}" << std::endl;
            return 1;
        }

        std::cout << doc->to_json() << std::endl;
        return 0;
    }

    if (command == "search") {
        if (argc < 6) {
            std::cerr << "{\"error\": \"Usage: search <index_path> <algo: bm25|tf_idf> <mode: any|all> <top_k> [terms...]\"}" << std::endl;
            return 1;
        }
        std::string index_path = argv[2];
        std::string algo_str = argv[3];
        std::string mode_str = argv[4];
        int top_k = std::stoi(argv[5]);

        std::vector<std::string> query_terms;
        for (int i = 6; i < argc; ++i) {
            query_terms.push_back(argv[i]);
        }

        InvertedIndex index;
        std::string err;
        if (!index.load(index_path, &err)) {
            std::cout << "[]" << std::endl;
            return 0;
        }

        RankingAlgorithm algo = (algo_str == "tf_idf") ? RankingAlgorithm::TF_IDF : RankingAlgorithm::BM25;
        MatchMode mode = (mode_str == "all") ? MatchMode::ALL_TERMS : MatchMode::ANY_TERM;

        Ranker ranker(index);
        auto results = ranker.rank(query_terms, algo, mode, top_k);

        std::ostringstream ss;
        ss << "[";
        for (size_t i = 0; i < results.size(); ++i) {
            const auto& r = results[i];
            const Document* doc = index.get_document(r.doc_id);
            if (i > 0) ss << ",";
            ss << "{"
               << "\"doc_id\":" << r.doc_id << ","
               << "\"document_id\":\"" << Document::escape_json(r.string_doc_id) << "\","
               << "\"score\":" << r.score << ","
               << "\"title\":\"" << Document::escape_json(doc ? doc->title : "") << "\","
               << "\"url\":\"" << Document::escape_json(doc ? doc->source_url : "") << "\","
               << "\"content\":\"" << Document::escape_json(doc ? doc->content : "") << "\""
               << "}";
        }
        ss << "]";
        std::cout << ss.str() << std::endl;
        return 0;
    }

    if (command == "vocab") {
        if (argc < 3) {
            std::cout << "{}" << std::endl;
            return 0;
        }
        std::string index_path = argv[2];
        InvertedIndex index;
        std::string err;
        if (!index.load(index_path, &err)) {
            std::cout << "{}" << std::endl;
            return 0;
        }

        std::stringstream ss;
        ss << "{";
        bool first = true;
        for (const auto& kv : index.dictionary()) {
            if (!first) ss << ",";
            first = false;
            ss << "\"" << Document::escape_json(kv.first) << "\":" << kv.second.size();
        }
        ss << "}";
        std::cout << ss.str() << std::endl;
        return 0;
    }

    if (command == "suggestions") {
        if (argc < 5) {
            std::cout << "[]" << std::endl;
            return 0;
        }
        std::string index_path = argv[2];
        std::string prefix = argv[3];
        size_t limit = std::stoul(argv[4]);

        InvertedIndex index;
        std::string err;
        if (!index.load(index_path, &err)) {
            std::cout << "[]" << std::endl;
            return 0;
        }

        // Suggestions based on terms matching prefix, ordered by document frequency
        struct TermMatch {
            std::string term;
            size_t df;
        };
        std::vector<TermMatch> matches;

        // Iterate vocabulary
        // We test prefix match against terms
        std::string prefix_lower = prefix;
        std::transform(prefix_lower.begin(), prefix_lower.end(), prefix_lower.begin(), ::tolower);

        // Scan vocabulary terms matching prefix
        for (const auto& kv : index.dictionary()) {
            const std::string& term = kv.first;
            const auto& postings = kv.second;
            if (term.rfind(prefix_lower, 0) == 0) {
                matches.push_back({term, postings.size()});
            }
        }

        // Sort by document frequency descending, then alphabetical
        std::sort(matches.begin(), matches.end(), [](const TermMatch& a, const TermMatch& b) {
            if (a.df != b.df) return a.df > b.df;
            return a.term < b.term;
        });

        // Output JSON array of suggestions
        std::cout << "[";
        for (size_t i = 0; i < matches.size() && i < limit; ++i) {
            if (i > 0) std::cout << ",";
            std::cout << "\"" << Document::escape_json(matches[i].term) << "\"";
        }
        std::cout << "]" << std::endl;
        return 0;
    }

    if (command == "index") {
        if (argc < 4) {
            std::cerr << "{\"error\": \"Usage: index <index_path> <tsv_payload_path>\"}" << std::endl;
            return 1;
        }
        std::string index_path = argv[2];
        std::string payload_path = argv[3];

        InvertedIndex index;
        std::string err;
        // Load existing index if present
        index.load(index_path, &err);

        std::ifstream ifs(payload_path);
        if (!ifs.is_open()) {
            std::cout << "{\"status\":\"error\",\"message\":\"Cannot open payload file\"}" << std::endl;
            return 1;
        }

        std::string line;
        uint32_t count = 0;
        while (std::getline(ifs, line)) {
            if (line.rfind("DOC\t", 0) == 0) {
                // Parse tab-delimited doc line: DOC\tdoc_id\tsource_url\ttitle\thash\tfetched_at\tstatus\tcontent
                std::vector<std::string> parts;
                std::stringstream ss(line);
                std::string item;
                while (std::getline(ss, item, '\t')) {
                    parts.push_back(unescape_str(item));
                }
                if (parts.size() < 8) continue;

                Document doc;
                doc.document_id = parts[1];
                doc.source_url = parts[2];
                doc.title = parts[3];
                doc.content_hash = parts[4];
                doc.fetched_at = parts[5];
                doc.status = parts[6];
                doc.content = parts[7];

                // Read next line for tokens: TOKENS\tterm:pos:start:end\t...
                std::vector<Token> tokens;
                if (std::getline(ifs, line) && line.rfind("TOKENS\t", 0) == 0) {
                    std::stringstream tss(line.substr(7));
                    std::string tok_str;
                    while (std::getline(tss, tok_str, '\t')) {
                        if (tok_str.empty()) continue;
                        std::stringstream tok_ss(tok_str);
                        std::string term, s_pos, s_start, s_end;
                        if (std::getline(tok_ss, term, ':') &&
                            std::getline(tok_ss, s_pos, ':') &&
                            std::getline(tok_ss, s_start, ':') &&
                            std::getline(tok_ss, s_end, ':')) {
                            Token tok;
                            tok.term = unescape_str(term);
                            tok.position = std::stoul(s_pos);
                            tok.char_start = std::stoul(s_start);
                            tok.char_end = std::stoul(s_end);
                            tokens.push_back(std::move(tok));
                        }
                    }
                }

                if (index.add_document(doc, tokens)) {
                    count++;
                }
            }
        }

        if (!index.save(index_path, &err)) {
            std::cout << "{\"status\":\"error\",\"message\":\"" << Document::escape_json(err) << "\"}" << std::endl;
            return 1;
        }

        std::cout << "{"
                  << "\"status\":\"ok\","
                  << "\"indexed_count\":" << count << ","
                  << "\"total_documents\":" << index.total_documents()
                  << "}" << std::endl;
        return 0;
    }

    std::cerr << "{\"error\": \"Unknown command: " << command << "\"}" << std::endl;
    return 1;
}
