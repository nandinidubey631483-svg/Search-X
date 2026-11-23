"""
Seed corpus ingestion script for SearchX.
Indexes representative educational documents covering Information Retrieval,
Inverted Indexes, BM25, TF-IDF, Crawling, Python, JavaScript/MDN, React, Rust,
Distributed Systems, PostgreSQL, Redis, Kubernetes, Machine Learning, and Web Architecture.
"""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from crawler.app.models import Document
from backend.app.services.search_service import SearchEngineService
from backend.app.db.database import get_database
from backend.app.db.repository import DatabaseRepository

ALLOWED_SOURCES = [
    # Web & General Knowledge
    "docs.python.org",
    "developer.mozilla.org",
    "en.wikipedia.org",
    "github.com",
    "stackoverflow.com",
    "reddit.com",
    "react.dev",
    "doc.rust-lang.org",
    "en.cppreference.com",
    "fastapi.tiangolo.com",
    # Images & Visual Media
    "unsplash.com",
    "pexels.com",
    "pixabay.com",
    "commons.wikimedia.org",
    "openverse.org",
    "svgrepo.com",
    # Documents & Technical Manuals
    "rfc-editor.org",
    "w3.org",
    "devdocs.io",
    "readthedocs.org",
    "kernel.org",
    "postgresql.org",
    "redis.io",
    "kubernetes.io",
    "docs.docker.com",
    # News & Tech Publications
    "news.ycombinator.com",
    "techcrunch.com",
    "theverge.com",
    "arstechnica.com",
    "bleepingcomputer.com",
    "infoq.com",
    # Scholar & Academic Research
    "arxiv.org",
    "scholar.google.com",
    "semanticscholar.org",
    "dl.acm.org",
    "ieeexplore.ieee.org",
    "stanford.edu",
    "pytorch.org",
]

DOCUMENTS = [
    # 1. Information Retrieval & Core Engine
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

    # 2. Python Documentation (docs.python.org)
    {
        "document_id": "doc_python_ds",
        "title": "Python 3.13 Data Structures Tutorial",
        "source_url": "https://docs.python.org/3/tutorial/datastructures.html",
        "content": (
            "This tutorial demonstrates more on lists, using lists as stacks and queues, list comprehensions, "
            "the del statement, tuples and sequences, sets, and dictionaries. Understanding Python data structure time complexity "
            "is essential for high-throughput backend services and indexing pipelines."
        ),
        "description": "Official Python tutorial covering built-in sequence and mapping types.",
    },
    {
        "document_id": "doc_python_asyncio",
        "title": "Python asyncio: Asynchronous I/O and Concurrency",
        "source_url": "https://docs.python.org/3/library/asyncio.html",
        "content": (
            "asyncio is a library to write concurrent code using the async/await syntax. asyncio is used as a foundation for multiple Python "
            "asynchronous frameworks that provide high-performance network and web-servers, database connection libraries, distributed task queues, "
            "and non-blocking crawler routines."
        ),
        "description": "Official documentation for Python's built-in asynchronous event loop and task management.",
    },
    {
        "document_id": "doc_python_collections",
        "title": "Python Collections: Container Datatypes",
        "source_url": "https://docs.python.org/3/library/collections.html",
        "content": (
            "The collections module implements specialized container datatypes providing alternatives to Python's general purpose built-in "
            "containers, dict, list, set, and tuple. Essential containers include deque for double-ended queues, Counter for multiset frequency counts, "
            "OrderedDict, and defaultdict."
        ),
        "description": "Specialized container structures in Python standard library.",
    },

    # 3. Mozilla Developer Network (developer.mozilla.org)
    {
        "document_id": "doc_mdn_event_loop",
        "title": "JavaScript Event Loop, Microtasks, and Call Stack",
        "source_url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Event_loop",
        "content": (
            "JavaScript has a runtime model based on an event loop, which is responsible for executing the code, collecting and processing events, "
            "and executing queued sub-tasks. The call stack tracks function frames, while the microtask queue processes resolved promises and MutationObservers "
            "before rendering frames and macrotasks like setTimeout."
        ),
        "description": "In-depth guide to JavaScript concurrency model and event loop execution.",
    },
    {
        "document_id": "doc_mdn_css_grid",
        "title": "CSS Grid Layout and Flexible Responsive Design",
        "source_url": "https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Grids",
        "content": (
            "CSS Grid Layout is a two-dimensional layout system for the web. It lets you organize content into rows and columns, making it much easier "
            "to design complex responsive web pages without having to use floats or positioning hacks. Combined with Flexbox, Grid forms the basis of "
            "modern clean search engine interfaces."
        ),
        "description": "Two-dimensional responsive grid layout specifications on MDN Web Docs.",
    },
    {
        "document_id": "doc_mdn_cors_security",
        "title": "Cross-Origin Resource Sharing (CORS) and Web Security",
        "source_url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS",
        "content": (
            "Cross-Origin Resource Sharing (CORS) is an HTTP-header based mechanism that allows a server to indicate any origins (domain, scheme, or port) "
            "other than its own from which a browser should permit loading resources. Preflight OPTIONS requests verify permissions before mutating APIs."
        ),
        "description": "Browser security policies, CORS headers, and origin boundaries on MDN.",
    },
    {
        "document_id": "doc_mdn_fetch_api",
        "title": "Web Fetch API, Promises, and Streaming Requests",
        "source_url": "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API",
        "content": (
            "The Fetch API provides an interface for fetching resources (including across the network). It is a modern replacement for XMLHttpRequest. "
            "Fetch utilizes JavaScript Promises, Request, Response, and Headers objects, supporting stream processing and request cancellation via AbortController."
        ),
        "description": "Network request processing and streaming on modern web browsers.",
    },

    # 4. React & Modern Frontend (react.dev)
    {
        "document_id": "doc_react_architecture",
        "title": "React 19 Architecture: Server Components and Actions",
        "source_url": "https://react.dev/learn",
        "content": (
            "React lets you build user interfaces out of individual pieces called components. React 19 introduces native Server Components, "
            "Action state management, optimistic UI updates, and compiler optimizations that reduce client bundle size and improve Core Web Vitals."
        ),
        "description": "Component-driven architecture and modern React design patterns.",
    },
    {
        "document_id": "doc_react_hooks",
        "title": "React Hooks: Managing State and Side Effects",
        "source_url": "https://react.dev/reference/react/hooks",
        "content": (
            "Hooks let you use different React features from your components. You can either use the built-in Hooks or combine them to build your own. "
            "Key hooks include useState for local state, useEffect for external system synchronization, useMemo for caching computations, and useCallback for function identity."
        ),
        "description": "Comprehensive reference for standard React hooks.",
    },

    # 5. Rust Systems Programming (doc.rust-lang.org)
    {
        "document_id": "doc_rust_ownership",
        "title": "Rust Ownership and the Borrow Checker",
        "source_url": "https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html",
        "content": (
            "Ownership is Rust's most unique feature and has deep implications for the rest of the language. It enables Rust to make memory safety "
            "guarantees without needing a garbage collector. The borrow checker enforces that references must always be valid and data races are prevented at compile time."
        ),
        "description": "Foundational guide to memory safety and zero-cost abstractions in Rust.",
    },
    {
        "document_id": "doc_rust_concurrency",
        "title": "Fearless Concurrency and Multi-Threading in Rust",
        "source_url": "https://doc.rust-lang.org/book/ch16-00-concurrency.html",
        "content": (
            "Handling concurrent programming safely and efficiently is another of Rust's major goals. Rust leverages Send and Sync traits "
            "to guarantee thread safety across shared memory (Arc and Mutex) or message-passing channels (mpsc), eliminating data races before code executes."
        ),
        "description": "Multi-threaded programming and concurrency safety in Rust.",
    },

    # 6. Distributed Systems & Databases (redis.io, postgresql.org, kubernetes.io)
    {
        "document_id": "doc_redis_caching",
        "title": "Redis Query Cache: In-Memory High Throughput",
        "source_url": "https://redis.io/docs/data-types/",
        "content": (
            "Redis is an open source, in-memory data structure store used as a database, cache, streaming engine, and message broker. "
            "In SearchX, Redis serves as the L1 query acceleration cache, storing serialized search responses with TTL expiration and automatic invalidation on ingestion."
        ),
        "description": "In-memory caching architectures and low-latency query acceleration.",
    },
    {
        "document_id": "doc_postgresql_mvcc",
        "title": "PostgreSQL Architecture: Postgres MVCC and ACID Relational Persistence",
        "source_url": "https://www.postgresql.org/docs/current/mvcc.html",
        "content": (
            "PostgreSQL (often known as Postgres) maintains data consistency by using a Multi-Version Concurrency Control (MVCC) model. This means that each query sees a snapshot "
            "of data (a database version) as it was some time ago, regardless of the current state of the underlying data. Write-Ahead Logging (WAL) guarantees durability."
        ),
        "description": "Relational database reliability, transactions, and concurrency control.",
    },
    {
        "document_id": "doc_kubernetes_orchestration",
        "title": "Kubernetes: Automated Container Orchestration at Scale",
        "source_url": "https://kubernetes.io/docs/concepts/overview/",
        "content": (
            "Kubernetes is an open-source system for automating deployment, scaling, and management of containerized applications. "
            "It groups containers that make up an application into logical units for easy management and discovery, managing Pods, Services, Deployments, and Ingress routers."
        ),
        "description": "Cloud-native infrastructure and distributed container management.",
    },
    {
        "document_id": "doc_distributed_raft",
        "title": "Distributed Consensus and the Raft Protocol",
        "source_url": "https://raft.github.io/",
        "content": (
            "Raft is a consensus algorithm that is designed to be easy to understand. It's equivalent to Paxos in fault-tolerance and performance. "
            "The consensus algorithm decomposes consensus into leader election, log replication, and safety constraints across distributed cluster nodes."
        ),
        "description": "Cluster coordination and consensus algorithms in distributed systems.",
    },

    # 7. Machine Learning, NLP & AI (arxiv.org, pytorch.org, en.wikipedia.org)
    {
        "document_id": "doc_transformer_attention",
        "title": "Attention Is All You Need: Transformer Neural Architecture",
        "source_url": "https://arxiv.org/abs/1706.03762",
        "content": (
            "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose the Transformer, "
            "a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output. "
            "Scaled dot-product attention and multi-head attention form the backbone of modern LLMs."
        ),
        "description": "The landmark 2017 research paper introducing the Transformer deep learning architecture.",
    },
    {
        "document_id": "doc_pytorch_tensors",
        "title": "PyTorch: Deep Learning with Dynamic Computation Graphs",
        "source_url": "https://pytorch.org/docs/stable/torch.html",
        "content": (
            "PyTorch is an optimized tensor library for deep learning using GPUs and CPUs. It features dynamic neural networks, autograd automatic differentiation, "
            "and an intuitive Pythonic API widely used across natural language processing, computer vision, and dense vector embedding generation."
        ),
        "description": "Tensors, autograd, and GPU-accelerated deep learning in PyTorch.",
    },
    {
        "document_id": "doc_llm_overview",
        "title": "Large Language Models: Pre-training, Fine-Tuning, and Inference",
        "source_url": "https://en.wikipedia.org/wiki/Large_language_model",
        "content": (
            "A large language model (LLM) is a computational model notable for its ability to achieve general-purpose language generation and understanding. "
            "LLMs acquire these abilities by learning statistical relationships from text corpora during a self-supervised and semi-supervised training process. "
            "Retrieval-Augmented Generation (RAG) pairs LLMs with inverted index search engines."
        ),
        "description": "Comprehensive guide to generative AI and foundation models.",
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

    # 8. Web Protocols & Operating Systems (en.wikipedia.org, kernel.org)
    {
        "document_id": "doc_tcp_ip_networking",
        "title": "TCP/IP Protocol Suite and Computer Networking Fundamentals",
        "source_url": "https://en.wikipedia.org/wiki/Internet_protocol_suite",
        "content": (
            "The Internet protocol suite, commonly known as TCP/IP, is the framework for organizing the set of communication protocols used in the Internet. "
            "Transmission Control Protocol (TCP) provides reliable, ordered, and error-checked delivery of a stream of octets between applications running on hosts, "
            "employing three-way handshakes, sliding windows, and congestion control."
        ),
        "description": "Internet protocol layers, socket communication, and reliable packet transfer.",
    },
    {
        "document_id": "doc_linux_kernel",
        "title": "Linux Kernel Architecture and System Calls",
        "source_url": "https://en.wikipedia.org/wiki/Linux_kernel",
        "content": (
            "The Linux kernel is a free and open-source, monolithic, modular, multitasking, Unix-like operating system kernel. "
            "It manages CPU scheduling, memory mapping, virtual filesystem (VFS), network sockets, and hardware drivers, exposing POSIX system calls "
            "to userland applications."
        ),
        "description": "Operating system kernel internals, process management, and VFS.",
    },
    {
        "document_id": "doc_pagerank_algorithm",
        "title": "The PageRank Algorithmic Citation Link Analysis",
        "source_url": "https://en.wikipedia.org/wiki/PageRank",
        "content": (
            "PageRank is an algorithm used by Google Search to rank web pages in their search engine results. It was named after Larry Page. "
            "PageRank works by counting the number and quality of links to a page to determine a rough estimate of how important the website is, "
            "modeling a random surfer traversing directed hyperlinks with a damping factor d."
        ),
        "description": "Graph theory, eigenvector centrality, and hyperlink link analysis.",
    },

    # 9. DevOps & Containers (docs.docker.com, github.com)
    {
        "document_id": "doc_docker_containers",
        "title": "Docker Containerization: Namespaces and Cgroups",
        "source_url": "https://docs.docker.com/get-started/",
        "content": (
            "Docker is a set of platform as a service products that use OS-level virtualization to deliver software in packages called containers. "
            "Containers are isolated from one another and bundle their own software, libraries and configuration files. Linux namespaces provide process isolation, "
            "while control groups (cgroups) meter and constrain CPU and memory usage."
        ),
        "description": "Container virtualization, images, layers, and daemon architecture.",
    },
    {
        "document_id": "doc_github_actions_cicd",
        "title": "Continuous Integration and GitHub Actions Workflows",
        "source_url": "https://docs.github.com/en/actions",
        "content": (
            "GitHub Actions is a continuous integration and continuous delivery (CI/CD) platform that allows you to automate your build, test, and deployment pipeline. "
            "You can create workflows that build and test every pull request to your repository, or deploy merged pull requests to production environments."
        ),
        "description": "Automated build matrices, testing harnesses, and CI/CD automation.",
    },

    # 10. Web APIs & C++ Engine
    {
        "document_id": "doc_fastapi_backend",
        "title": "FastAPI Web Framework and High-Performance APIs",
        "source_url": "https://fastapi.tiangolo.com/",
        "content": (
            "FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints. "
            "It provides automatic interactive API documentation via OpenAPI and Swagger UI, fast request validation with Pydantic, "
            "and asynchronous request handling built on top of Starlette and Uvicorn."
        ),
        "description": "High-performance Python web services with type hints and automatic validation.",
    },
    {
        "document_id": "doc_cpp_standard",
        "title": "C++17 Standard Library and Memory Architecture",
        "source_url": "https://en.cppreference.com/w/cpp/17",
        "content": (
            "C++17 is a version of the ISO/IEC 14882 standard for the C++ programming language. Key features include std::string_view for zero-allocation "
            "string referencing, std::filesystem for portable path navigation, structured bindings, if-constexpr for compile-time branching, "
            "and optimized STL container performance essential for high-throughput search engines."
        ),
        "description": "Modern C++ features and standard library utilities for high-performance systems.",
    },

    # 11. Images & Visual Media (unsplash.com, pexels.com, pixabay.com, commons.wikimedia.org, openverse.org, svgrepo.com)
    {
        "document_id": "doc_unsplash_photography",
        "title": "Unsplash: High-Resolution Photography, Stock Imagery and Visual Media",
        "source_url": "https://unsplash.com/",
        "content": (
            "Unsplash provides over 5 million free high-resolution images, creative photography, and aesthetic wallpapers contributed by global photographers. "
            "SearchX indexes visual metadata, resolution dimensions, color palettes, and descriptive tags for graphic designers and developers seeking visual creative commons assets."
        ),
        "description": "High-resolution stock photography and visual assets repository on Unsplash.",
    },
    {
        "document_id": "doc_pexels_stock",
        "title": "Pexels: Free Stock Photos, Royalty-Free Wallpapers and Creative Media",
        "source_url": "https://www.pexels.com/",
        "content": (
            "Pexels offers free stock photos, royalty-free wallpapers, and visual design assets. Creative professionals use Pexels for desktop backgrounds, "
            "UI mockups, and responsive web backgrounds with zero attribution required under the permissive Pexels license."
        ),
        "description": "Royalty-free photo collection and desktop wallpaper search on Pexels.",
    },
    {
        "document_id": "doc_pixabay_vectors",
        "title": "Pixabay: Free Vector Graphics, Illustrations and High-Def Media",
        "source_url": "https://pixabay.com/",
        "content": (
            "Pixabay is a vibrant community of creatives sharing copyright-free images, vector graphics, animations, and illustrations. "
            "All media are released under the Pixabay license, safe for commercial use without attribution, spanning vector icons, clip art, and photo galleries."
        ),
        "description": "Vector illustrations and copyright-free media catalog on Pixabay.",
    },
    {
        "document_id": "doc_wikimedia_commons",
        "title": "Wikimedia Commons: Educational Media, Scientific Schematics and Historical Images",
        "source_url": "https://commons.wikimedia.org/",
        "content": (
            "Wikimedia Commons is a database of 100+ million freely usable media files. It hosts scientific diagrams, public domain anatomical charts, "
            "geographic maps, and architectural photographs used across Wikipedia, research papers, and educational textbooks."
        ),
        "description": "Free educational media and scientific diagram archive on Wikimedia Commons.",
    },
    {
        "document_id": "doc_openverse_media",
        "title": "Openverse: Openly Licensed Media Search and Creative Commons Discovery",
        "source_url": "https://openverse.org/",
        "content": (
            "Openverse is an open-source search engine for openly licensed and public domain images, audio, and visual works. "
            "Openverse searches across more than 700 million creative works indexed from cultural institutions, museums, and digital libraries worldwide."
        ),
        "description": "Universal Creative Commons media search engine powered by WordPress.",
    },
    {
        "document_id": "doc_svgrepo_vectors",
        "title": "SVG Repo: Free Vector SVG Icons, UI Graphics and Scalable Schematics",
        "source_url": "https://www.svgrepo.com/",
        "content": (
            "SVG Repo provides over 500,000 free SVG vectors, interface icons, and UI visual schematics. Scalable vector graphics allow loss-less rendering "
            "across high-DPI displays, making SVG the industry standard for modern web application icons, flowchart diagrams, and technical blueprints."
        ),
        "description": "Scalable vector graphics and interface icon repository on SVG Repo.",
    },

    # 12. Documents & Official Specifications (rfc-editor.org, w3.org, devdocs.io, kernel.org, readthedocs.org)
    {
        "document_id": "doc_rfc_http3_quic",
        "title": "RFC 9114: HTTP/3 Protocol and QUIC Transport Specifications",
        "source_url": "https://www.rfc-editor.org/rfc/rfc9114.html",
        "content": (
            "RFC 9114 specifies HTTP/3, the third major version of the Hypertext Transfer Protocol. HTTP/3 maps HTTP semantics over QUIC, "
            "an encrypted UDP-based transport protocol that eliminates head-of-line blocking, accelerates connection handshakes with 0-RTT, and boosts mobile performance."
        ),
        "description": "Official IETF Internet Standards documentation for HTTP/3 and QUIC transport.",
    },
    {
        "document_id": "doc_w3c_html5_spec",
        "title": "W3C Recommendation: HTML5 Semantic Elements and Web Architecture",
        "source_url": "https://www.w3.org/TR/html52/",
        "content": (
            "The W3C HTML5 specification defines the fifth major version of the core language of the World Wide Web. It standardizes semantic markup elements "
            "like article, section, nav, and main, alongside native video/audio playback, canvas 2D graphics, WebSockets, and offline web application caching."
        ),
        "description": "W3C standard recommendation for modern web document semantics and DOM APIs.",
    },
    {
        "document_id": "doc_devdocs_reference",
        "title": "DevDocs: Unified Fast Offline API Documentation for Developers",
        "source_url": "https://devdocs.io/",
        "content": (
            "DevDocs combines multiple API documentations in a fast, organized, and searchable interface. It provides instant offline documentation for C++, "
            "Python, JavaScript, CSS, HTML, Go, Rust, and PostgreSQL with keyboard shortcuts, fuzzy search, and clean developer typography."
        ),
        "description": "Comprehensive multi-language developer API documentation browser on DevDocs.",
    },
    {
        "document_id": "doc_kernel_memory_management",
        "title": "The Linux Kernel Documentation: Virtual Memory and Page Allocation",
        "source_url": "https://www.kernel.org/doc/html/latest/admin-guide/mm/index.html",
        "content": (
            "The Linux kernel virtual memory subsystem manages physical RAM allocation, swap space, and memory mapping. Key concepts include page cache management, "
            "slab allocators (SLUB/SLAB), transparent huge pages (THP), and out-of-memory (OOM) killer heuristics in high-concurrency server environments."
        ),
        "description": "Linux kernel architecture and memory management documentation from kernel.org.",
    },
    {
        "document_id": "doc_readthedocs_platform",
        "title": "Read the Docs: Open Source Technical Documentation Platform",
        "source_url": "https://readthedocs.org/",
        "content": (
            "Read the Docs simplifies software documentation by automating building, versioning, and hosting of technical docs. Supporting Sphinx, MkDocs, "
            "and Markdown, it generates searchable PDF and HTML manuals for thousands of open-source libraries and scientific software projects."
        ),
        "description": "Continuous documentation hosting and versioning system on Read the Docs.",
    },

    # 13. News & Tech Journalism (news.ycombinator.com, techcrunch.com, theverge.com, arstechnica.com, bleepingcomputer.com, infoq.com)
    {
        "document_id": "doc_hackernews_engineering",
        "title": "Hacker News: Software Engineering Discussions and Architecture Insights",
        "source_url": "https://news.ycombinator.com/",
        "content": (
            "Hacker News is a social news website focusing on computer science, entrepreneurship, and software engineering. It features real-time breaking discussions "
            "on new compiler releases, system performance benchmarks, database architectures, and security advisories curated by the global tech community."
        ),
        "description": "Real-time engineering discussions and startup news portal on Hacker News.",
    },
    {
        "document_id": "doc_techcrunch_ai_funding",
        "title": "TechCrunch: AI Industry Headlines, Cloud Infrastructure and Tech Funding",
        "source_url": "https://techcrunch.com/",
        "content": (
            "TechCrunch delivers breaking news and analysis on technology companies, artificial intelligence advancements, and venture capital funding rounds. "
            "Coverage includes foundational model developments, enterprise SaaS acquisitions, and emerging developer tooling."
        ),
        "description": "Global technology industry journalism and artificial intelligence coverage on TechCrunch.",
    },
    {
        "document_id": "doc_theverge_tech_culture",
        "title": "The Verge: Emerging Technologies, Consumer Electronics and Digital Culture",
        "source_url": "https://www.theverge.com/",
        "content": (
            "The Verge covers the intersection of technology, science, art, and modern culture. Reporting highlights consumer hardware reviews, semiconductor innovations, "
            "browser platform wars, and regulatory antitrust developments shaping the open internet."
        ),
        "description": "In-depth technology journalism, platform reviews, and hardware reporting on The Verge.",
    },
    {
        "document_id": "doc_arstechnica_security",
        "title": "Ars Technica: In-Depth Technology Analysis, Linux Systems and Cybersecurity",
        "source_url": "https://arstechnica.com/",
        "content": (
            "Ars Technica publishes authoritative technical reporting for technologists and IT professionals. Articles explore Linux kernel releases, "
            "microarchitecture side-channel vulnerabilities, cryptographic algorithms, distributed systems resiliency, and broadband policy."
        ),
        "description": "Deep-dive technological analysis and cybersecurity reporting on Ars Technica.",
    },
    {
        "document_id": "doc_bleepingcomputer_threats",
        "title": "BleepingComputer: Cybersecurity Alerts, Zero-Day Vulnerabilities and CVE Reports",
        "source_url": "https://www.bleepingcomputer.com/",
        "content": (
            "BleepingComputer is a premier cybersecurity news site providing timely threat intelligence on ransomware campaigns, zero-day software exploits, "
            "CVE security patches, and data breach disclosures affecting cloud infrastructure and enterprise networks."
        ),
        "description": "Cybersecurity vulnerability reporting and malware threat intelligence on BleepingComputer.",
    },
    {
        "document_id": "doc_infoq_architecture",
        "title": "InfoQ: Software Architecture Trends, Microservices and DevOps Practices",
        "source_url": "https://www.infoq.com/",
        "content": (
            "InfoQ provides enterprise software developers with peer-driven news on software architecture, DevOps pipelines, containerized deployments, "
            "and microservices patterns. It covers language roadmaps, cloud native computing, and reactive systems design."
        ),
        "description": "Enterprise software architecture and distributed systems news on InfoQ.",
    },

    # 14. Scholar & Academic Citations (scholar.google.com, semanticscholar.org, dl.acm.org, ieeexplore.ieee.org)
    {
        "document_id": "doc_google_scholar_metrics",
        "title": "Google Scholar: Academic Research Indexing and Citation Bibliometrics",
        "source_url": "https://scholar.google.com/",
        "content": (
            "Google Scholar provides a simple way to broadly search for scholarly literature across many disciplines and sources: articles, theses, books, abstracts, "
            "and court opinions. It calculates h-index metrics and citation graphs linking foundational research to modern scientific citations."
        ),
        "description": "Broad academic research literature search and citation tracking on Google Scholar.",
    },
    {
        "document_id": "doc_semanticscholar_ai",
        "title": "Semantic Scholar: AI-Powered Scientific Literature Exploration and Citation Graphs",
        "source_url": "https://www.semanticscholar.org/",
        "content": (
            "Semantic Scholar is a free AI-powered research tool developed by the Allen Institute for AI. Using natural language processing, Semantic Scholar "
            "extracts key insights, highly influential citations, and methodological relationships across millions of peer-reviewed papers."
        ),
        "description": "AI-driven scientific literature navigation and research graphs on Semantic Scholar.",
    },
    {
        "document_id": "doc_acm_digital_library",
        "title": "ACM Digital Library: Peer-Reviewed Computer Science Research and Conference Proceedings",
        "source_url": "https://dl.acm.org/",
        "content": (
            "The ACM Digital Library is the most comprehensive database of full-text articles and bibliographic records covering computing and information technology. "
            "It archives Turing Award lectures, SIGMOD database research, SIGIR information retrieval breakthroughs, and SOSP operating systems conferences."
        ),
        "description": "Official ACM archive of peer-reviewed computer science literature and conference papers.",
    },
    {
        "document_id": "doc_ieee_xplore_research",
        "title": "IEEE Xplore: Electrical Engineering, Computer Science and Telecommunications Standards",
        "source_url": "https://ieeexplore.ieee.org/",
        "content": (
            "IEEE Xplore is a scholarly research database indexing over 5 million documents from IEEE and IET publications. It covers neural networks, "
            "machine learning algorithms, wireless telecommunications standards (802.11 Wi-Fi, 5G), robotics, and signal processing."
        ),
        "description": "Peer-reviewed technical literature and international engineering standards on IEEE Xplore.",
    },
]

def main():
    print("Initializing database schema...")
    db = get_database()
    db.create_tables()

    repo = DatabaseRepository(db=db)
    print(f"Registering {len(ALLOWED_SOURCES)} allowed crawl sources...")
    for domain in ALLOWED_SOURCES:
        repo.save_source(domain, enabled=True)
    print(f"Registered {len(ALLOWED_SOURCES)} allowed sources into database.")

    print(f"Indexing {len(DOCUMENTS)} educational documents across top web domains...")
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
    print(f"Index Statistics: {stats.total_documents} documents, {stats.vocabulary_size} vocabulary terms, avg length: {stats.average_document_length:.1f} words")

if __name__ == "__main__":
    main()
