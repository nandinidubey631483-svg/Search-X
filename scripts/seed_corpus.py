"""
Seed corpus ingestion script for SearchX.
Indexes representative educational documents covering Information Retrieval,
Inverted Indexes, BM25, TF-IDF, Crawling, and Web Systems.
"""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from crawler.app.models import Document
from backend.app.services.search_service import SearchEngineService
from backend.app.db.database import get_database

DOCUMENTS = [
    {
        "document_id": "doc_ir_overview",
        "title": "Information Retrieval: Core Principles and Systems",
        "source_url": "https://nlp.stanford.edu/IR-book/information-retrieval.html",
        "content": (
            "Information retrieval is the science of searching for documents, information within documents, "
            "and metadata about documents. Modern search engines rely on inverted indexes, tokenization pipelines, "
            "and statistical ranking algorithms such as TF-IDF and Okapi BM25 to return relevant results quickly."
        ),
        "description": "Foundational concepts and principles in modern information retrieval.",
    },
    {
        "document_id": "doc_inverted_index",
        "title": "Inverted Index Architecture and Postings Lists",
        "source_url": "https://en.wikipedia.org/wiki/Inverted_index",
        "content": (
            "An inverted index is a database index storing a mapping from content, such as words or numbers, "
            "to its locations in a table, or in a document, or in a collection of documents. The inverted index "
            "consists of a term dictionary and postings lists containing document IDs, term frequencies, and "
            "optional token positions for phrase searching and snippet generation."
        ),
        "description": "Deep dive into the inverted index data structure, dictionary lookup, and postings traversal.",
    },
    {
        "document_id": "doc_bm25_ranking",
        "title": "Okapi BM25 Scoring and Length Normalization",
        "source_url": "https://en.wikipedia.org/wiki/Okapi_BM25",
        "content": (
            "Okapi BM25 is a ranking function used by search engines to estimate the relevance of documents to a given "
            "search query. It is based on the probabilistic relevance framework. BM25 improves on standard TF-IDF by "
            "introducing term frequency saturation controlled by parameter k1 and document length normalization controlled by parameter b."
        ),
        "description": "Mathematical formulation and parameter tuning for the Okapi BM25 ranking algorithm.",
    },
    {
        "document_id": "doc_tfidf_scoring",
        "title": "Term Frequency-Inverse Document Frequency (TF-IDF)",
        "source_url": "https://en.wikipedia.org/wiki/Tf%E2%80%93idf",
        "content": (
            "TF-IDF is a numerical statistic intended to reflect how important a word is to a document in a collection or corpus. "
            "The tf-idf value increases proportionally to the number of times a word appears in the document and is offset by the "
            "number of documents in the corpus that contain the word, which helps adjust for common words."
        ),
        "description": "Understanding term weighting, sublinear TF scaling, and smooth inverse document frequency.",
    },
    {
        "document_id": "doc_web_crawler",
        "title": "Web Crawling Architecture and Safety Policies",
        "source_url": "https://en.wikipedia.org/wiki/Web_crawler",
        "content": (
            "A web crawler, or spider, is an Internet bot that systematically browses the World Wide Web, typically operated by search engines "
            "for the purpose of Web indexing. Safe crawlers respect the Robots Exclusion Standard (robots.txt), enforce rate limits, avoid spider traps, "
            "and validate IP addresses to protect against Server-Side Request Forgery (SSRF)."
        ),
        "description": "Techniques for building robust, polite, and safe automated web crawlers.",
    },
    {
        "document_id": "doc_fastapi_backend",
        "title": "FastAPI Web Framework and High-Performance APIs",
        "source_url": "https://fastapi.tiangolo.com/",
        "content": (
            "FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints. "
            "It provides automatic interactive API documentation via OpenAPI and Swagger UI, fast request validation with Pydantic, "
            "and seamless integration with database ORMs and asynchronous event loops."
        ),
        "description": "Using FastAPI for search engine backend orchestration and administrative services.",
    },
    {
        "document_id": "doc_redis_caching",
        "title": "Redis Query Caching and Cache Invalidation Strategies",
        "source_url": "https://redis.io/topics/caching",
        "content": (
            "Redis is an open-source, in-memory data structure store used as a database, cache, streaming engine, and message broker. "
            "In search engines, Redis caches frequent query results and autocomplete suggestions with time-to-live (TTL) limits. "
            "Automatic cache invalidation ensures that stale search results are purged when new documents are indexed."
        ),
        "description": "High-throughput query caching and invalidation patterns with Redis.",
    },
    {
        "document_id": "doc_postgresql_storage",
        "title": "PostgreSQL Relational Storage for Document Metadata",
        "source_url": "https://www.postgresql.org/",
        "content": (
            "PostgreSQL is a powerful, open-source object-relational database system with a strong reputation for reliability, "
            "feature robustness, and performance. In SearchX, PostgreSQL persists document metadata, crawler job history, allowed "
            "domain configurations, and query analytics with atomic upsert operations."
        ),
        "description": "Durable transactional metadata persistence in modern search systems.",
    },
    {
        "document_id": "doc_react_ui",
        "title": "React User Interface and Accessible Search Experience",
        "source_url": "https://react.dev/",
        "content": (
            "React is a JavaScript library for building user interfaces based on components. The SearchX React frontend provides an "
            "interactive search homepage, live autocomplete suggestions, filter toggles between BM25 and TF-IDF, contextual snippet "
            "highlighting, pagination controls, and an administrative dashboard for source management."
        ),
        "description": "Designing accessible, reactive search user experiences.",
    },
    {
        "document_id": "doc_machine_learning",
        "title": "Machine Learning: Concepts, Methods, and Algorithms",
        "source_url": "https://en.wikipedia.org/wiki/Machine_learning",
        "content": (
            "Machine learning is a field of inquiry devoted to understanding and building methods that 'learn' — that is, methods that "
            "leverage data to improve performance on some set of tasks. It is seen as a part of artificial intelligence. Machine learning "
            "algorithms build a model based on training data in order to make predictions or decisions without being explicitly programmed to do so. "
            "Core paradigms include supervised learning, unsupervised learning, reinforcement learning, and modern neural network models."
        ),
        "description": "Foundations of machine learning, training data, predictive algorithms, and AI paradigms.",
    },
    {
        "document_id": "doc_deep_learning",
        "title": "Deep Learning and Artificial Neural Networks",
        "source_url": "https://en.wikipedia.org/wiki/Deep_learning",
        "content": (
            "Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. "
            "Deep neural network architectures including convolutional neural networks, recurrent networks, and transformers have revolutionized "
            "computer vision, natural language processing, speech recognition, and search engine ranking functions."
        ),
        "description": "Exploration of deep learning architectures, neural representations, and transformers.",
    },
    {
        "document_id": "doc_nlp_embeddings",
        "title": "Natural Language Processing and Dense Vector Search",
        "source_url": "https://en.wikipedia.org/wiki/Natural_language_processing",
        "content": (
            "Natural language processing (NLP) enables computers to understand, interpret, and manipulate human language. "
            "Modern search engines combine lexical inverted indexes with dense vector embeddings produced by machine learning models to perform "
            "hybrid semantic search, capturing both exact keyword matches and conceptual synonyms."
        ),
        "description": "NLP techniques, text representations, and hybrid semantic retrieval.",
    },
    {
        "document_id": "doc_ai_overview",
        "title": "Artificial Intelligence: Past, Present, and Future",
        "source_url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "content": (
            "Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural intelligence displayed by animals and humans. "
            "Major AI subfields include machine learning, deep learning, automated reasoning, robotics, computer vision, and cognitive computing. "
            "Information retrieval systems increasingly integrate AI models for query reformulation, intent understanding, and neural ranking."
        ),
        "description": "Comprehensive survey of artificial intelligence subfields and neural search applications.",
    },
]

def main():
    print("Initializing database schema...")
    db = get_database()
    db.create_tables()

    print(f"Indexing {len(DOCUMENTS)} educational documents...")
    service = SearchEngineService()

    doc_objects = [
        Document.create(
            document_id=d["document_id"],
            title=d["title"],
            content=d["content"],
            source_url=d["source_url"],
            description=d.get("description", ""),
        )
        for d in DOCUMENTS
    ]

    indexed_count = service.index_documents(doc_objects)
    print(f"Successfully indexed {indexed_count} documents into SearchX C++ engine and database!")

    stats = service.get_stats()
    print(f"Index Statistics: {stats.total_documents} documents, {stats.vocabulary_size} vocabulary terms, avg length: {stats.average_document_length}")

if __name__ == "__main__":
    main()
