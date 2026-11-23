import React, { useState, useEffect, useCallback } from 'react';
import { api } from './services/api';
import { Navbar } from './components/Navbar';
import { SearchBar } from './components/SearchBar';
import { SearchResultCard } from './components/SearchResultCard';
import { Pagination } from './components/Pagination';
import { DocumentModal } from './components/DocumentModal';
import { AdminDashboard } from './components/AdminDashboard';
import { SmartImage } from './components/SmartImage';
import { ImageLightboxModal } from './components/ImageLightboxModal';
import {
  IconSearch,
  IconTrendingUp,
  IconZap,
  IconAlertCircle,
  IconSettings,
  IconGlobe,
  IconImage,
  IconFileText,
  IconNewspaper,
  IconGraduationCap,
  IconExternalLink,
} from './components/Icons';
import './index.css';

export function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [activeCategory, setActiveCategory] = useState('web');
  const [query, setQuery] = useState('');
  const [algo, setAlgo] = useState('bm25');
  const [mode, setMode] = useState('any');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const [loading, setLoading] = useState(false);
  const [searchResponse, setSearchResponse] = useState(null);
  const [error, setError] = useState(null);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [health, setHealth] = useState(null);

  // Dark / Light Theme State
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('searchx_dark_mode') === 'true';
  });

  const toggleDarkMode = () => {
    const nextMode = !darkMode;
    setDarkMode(nextMode);
    localStorage.setItem('searchx_dark_mode', String(nextMode));
  };

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Check backend health on mount
  const checkHealth = useCallback(async () => {
    try {
      const data = await api.checkHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // Execute Search
  const executeSearch = useCallback(
    async (searchQuery, targetPage = 1, searchAlgo = algo, searchMode = mode) => {
      if (!searchQuery.trim()) return;

      setLoading(true);
      setError(null);
      setQuery(searchQuery);
      setPage(targetPage);

      const offset = (targetPage - 1) * pageSize;

      try {
        const res = await api.search({
          query: searchQuery,
          algo: searchAlgo,
          mode: searchMode,
          limit: pageSize,
          offset,
        });
        setSearchResponse(res);
      } catch (err) {
        setError(err.message || 'Search request failed. Please check backend connection.');
        setSearchResponse(null);
      } finally {
        setLoading(false);
      }
    },
    [algo, mode, pageSize]
  );

  const handleAlgoChange = (newAlgo) => {
    setAlgo(newAlgo);
    if (query.trim()) {
      executeSearch(query, 1, newAlgo, mode);
    }
  };

  const handleModeChange = (newMode) => {
    setMode(newMode);
    if (query.trim()) {
      executeSearch(query, 1, algo, newMode);
    }
  };

  const handleCategoryChange = (newCategory) => {
    setActiveCategory(newCategory);
    if (query.trim()) {
      executeSearch(query, 1, algo, mode);
    }
  };

  const handlePageChange = (newPage) => {
    executeSearch(query, newPage, algo, mode);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const categoryWebsites = {
    web: [
      {
        name: 'Wikipedia',
        domain: 'en.wikipedia.org',
        url: 'https://en.wikipedia.org/',
        desc: 'The free encyclopedia covering science, mathematics, world history, and computer science.',
        query: 'inverted index wikipedia',
        badge: 'Encyclopedia',
      },
      {
        name: 'GitHub',
        domain: 'github.com',
        url: 'https://github.com/',
        desc: 'Open source software repositories, developer collaboration, and CI/CD pipelines.',
        query: 'github actions continuous integration',
        badge: 'Code & Repos',
      },
      {
        name: 'MDN Web Docs',
        domain: 'developer.mozilla.org',
        url: 'https://developer.mozilla.org/',
        desc: 'Web standards, JavaScript APIs, CSS Grid, and browser runtime documentation.',
        query: 'javascript event loop mdn',
        badge: 'Web Standards',
      },
      {
        name: 'Python.org',
        domain: 'docs.python.org',
        url: 'https://docs.python.org/',
        desc: 'Official documentation, standard library references, and language specifications.',
        query: 'python asyncio event loop',
        badge: 'Core Language',
      },
      {
        name: 'Stack Overflow',
        domain: 'stackoverflow.com',
        url: 'https://stackoverflow.com/',
        desc: 'Developer knowledge base, programming bug solutions, and architecture questions.',
        query: 'distributed concurrency memory safety',
        badge: 'Developer Q&A',
      },
      {
        name: 'React.dev',
        domain: 'react.dev',
        url: 'https://react.dev/',
        desc: 'Official guide to React 19, Server Components, Hooks lifecycle, and modern UI state.',
        query: 'react server components actions',
        badge: 'UI Library',
      },
    ],
    images: [
      {
        name: 'Unsplash',
        domain: 'unsplash.com',
        url: 'https://unsplash.com/',
        bannerImg: 'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=600&auto=format&fit=crop&q=80',
        desc: 'High-resolution photography, creative wallpapers, and royalty-free visual media.',
        query: 'unsplash photography high resolution',
        badge: 'Stock Photos',
      },
      {
        name: 'Pexels',
        domain: 'pexels.com',
        url: 'https://www.pexels.com/',
        bannerImg: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600&auto=format&fit=crop&q=80',
        desc: 'Free stock photos, aesthetic desktop backgrounds, and royalty-free visual assets.',
        query: 'pexels stock photos wallpapers',
        badge: 'Wallpapers',
      },
      {
        name: 'Pixabay',
        domain: 'pixabay.com',
        url: 'https://pixabay.com/',
        bannerImg: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&auto=format&fit=crop&q=80',
        desc: 'Copyright-free vector graphics, digital illustrations, clip art, and photo media.',
        query: 'pixabay vector graphics illustrations',
        badge: 'Vector & Art',
      },
      {
        name: 'Wikimedia Commons',
        domain: 'commons.wikimedia.org',
        url: 'https://commons.wikimedia.org/',
        bannerImg: 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&auto=format&fit=crop&q=80',
        desc: 'Public domain educational schematics, anatomical diagrams, and historical archives.',
        query: 'wikimedia commons scientific diagrams',
        badge: 'Educational Media',
      },
      {
        name: 'Openverse',
        domain: 'openverse.org',
        url: 'https://openverse.org/',
        bannerImg: 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600&auto=format&fit=crop&q=80',
        desc: 'Universal search across 700M+ openly licensed Creative Commons images and cultural works.',
        query: 'openverse creative commons discovery',
        badge: 'Open License',
      },
      {
        name: 'SVG Repo',
        domain: 'svgrepo.com',
        url: 'https://www.svgrepo.com/',
        bannerImg: 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600&auto=format&fit=crop&q=80',
        desc: '500,000+ scalable vector SVG icons, UI elements, and technical flowchart schematics.',
        query: 'svg repo vector icons schematics',
        badge: 'SVG Vectors',
      },
    ],
    documents: [
      {
        name: 'RFC Editor',
        domain: 'rfc-editor.org',
        url: 'https://www.rfc-editor.org/',
        desc: 'Official Internet Engineering Task Force (IETF) RFC protocol standards (HTTP/3, QUIC).',
        query: 'rfc http3 quic specifications',
        badge: 'IETF Standards',
      },
      {
        name: 'W3C Specifications',
        domain: 'w3.org',
        url: 'https://www.w3.org/',
        desc: 'World Wide Web Consortium standards for HTML5 semantics, DOM APIs, and CSS specs.',
        query: 'w3c html5 semantic elements',
        badge: 'Web Consortia',
      },
      {
        name: 'DevDocs',
        domain: 'devdocs.io',
        url: 'https://devdocs.io/',
        desc: 'Fast offline API documentation browser for C++, Rust, Python, Go, and PostgreSQL.',
        query: 'devdocs offline api documentation',
        badge: 'API Browser',
      },
      {
        name: 'Linux Kernel Docs',
        domain: 'kernel.org',
        url: 'https://www.kernel.org/doc/html/latest/',
        desc: 'Virtual memory management, slab allocators, process scheduling, and kernel drivers.',
        query: 'linux kernel virtual memory page',
        badge: 'OS Architecture',
      },
      {
        name: 'Read the Docs',
        domain: 'readthedocs.org',
        url: 'https://readthedocs.org/',
        desc: 'Automated technical documentation hosting and versioning for open-source libraries.',
        query: 'read the docs technical documentation',
        badge: 'Doc Hosting',
      },
      {
        name: 'Rust Lang Book',
        domain: 'doc.rust-lang.org',
        url: 'https://doc.rust-lang.org/book/',
        desc: 'Memory safety guarantees, ownership borrow checker, and fearless concurrency specs.',
        query: 'rust ownership borrow checker',
        badge: 'Language Book',
      },
    ],
    news: [
      {
        name: 'Hacker News',
        domain: 'news.ycombinator.com',
        url: 'https://news.ycombinator.com/',
        desc: 'Real-time breaking discussions on computer science, distributed systems, and startups.',
        query: 'hacker news engineering discussions',
        badge: 'Tech Community',
      },
      {
        name: 'TechCrunch',
        domain: 'techcrunch.com',
        url: 'https://techcrunch.com/',
        desc: 'Artificial intelligence headlines, cloud startups, and venture capital funding news.',
        query: 'techcrunch ai industry funding',
        badge: 'VC & Startups',
      },
      {
        name: 'The Verge',
        domain: 'theverge.com',
        url: 'https://www.theverge.com/',
        desc: 'Consumer hardware, semiconductor innovations, browser wars, and modern tech culture.',
        query: 'the verge emerging technologies',
        badge: 'Digital Culture',
      },
      {
        name: 'Ars Technica',
        domain: 'arstechnica.com',
        url: 'https://arstechnica.com/',
        desc: 'Deep-dive IT analysis, microarchitecture vulnerabilities, and cybersecurity policy.',
        query: 'ars technica security linux',
        badge: 'Deep Tech',
      },
      {
        name: 'BleepingComputer',
        domain: 'bleepingcomputer.com',
        url: 'https://www.bleepingcomputer.com/',
        desc: 'Cybersecurity alerts, zero-day vulnerabilities, ransomware intelligence, and CVEs.',
        query: 'bleepingcomputer cybersecurity vulnerabilities',
        badge: 'Cyber Threat Intel',
      },
      {
        name: 'InfoQ',
        domain: 'infoq.com',
        url: 'https://www.infoq.com/',
        desc: 'Enterprise software architecture, microservices, cloud-native DevOps, and frameworks.',
        query: 'infoq software architecture microservices',
        badge: 'Enterprise Architecture',
      },
    ],
    scholar: [
      {
        name: 'arXiv.org',
        domain: 'arxiv.org',
        url: 'https://arxiv.org/',
        desc: 'Open-access scientific preprints in artificial intelligence, deep learning, and physics.',
        query: 'arxiv attention transformer neural',
        badge: 'Preprint Archive',
      },
      {
        name: 'Google Scholar',
        domain: 'scholar.google.com',
        url: 'https://scholar.google.com/',
        desc: 'Scholarly literature search, citation tracking, h-index metrics, and journal articles.',
        query: 'google scholar citation bibliometrics',
        badge: 'Citation Index',
      },
      {
        name: 'Semantic Scholar',
        domain: 'semanticscholar.org',
        url: 'https://www.semanticscholar.org/',
        desc: 'AI-powered scientific research discovery, literature navigation, and citation graphs.',
        query: 'semantic scholar literature exploration',
        badge: 'AI Research Graph',
      },
      {
        name: 'ACM Digital Library',
        domain: 'dl.acm.org',
        url: 'https://dl.acm.org/',
        desc: 'Peer-reviewed computing research, Turing Award lectures, and SIGIR/SIGMOD papers.',
        query: 'acm digital library computer science',
        badge: 'Peer-Reviewed CS',
      },
      {
        name: 'IEEE Xplore',
        domain: 'ieeexplore.ieee.org',
        url: 'https://ieeexplore.ieee.org/',
        desc: 'Electrical engineering, neural networks, telecommunications, and IEEE standards.',
        query: 'ieee xplore electrical engineering',
        badge: 'Engineering Journal',
      },
      {
        name: 'Stanford InfoLab',
        domain: 'stanford.edu',
        url: 'https://nlp.stanford.edu/IR-book/',
        desc: 'Information retrieval foundations, vector space ranking, and web graph crawling.',
        query: 'stanford information retrieval principles',
        badge: 'Academic Research',
      },
    ],
  };

  const categoryHeaders = {
    web: {
      title: 'Featured Web & Knowledge Sources',
      desc: 'Authoritative encyclopedias, open-source repositories, and developer knowledge bases.',
      badge: '6 Verified Sources',
    },
    images: {
      title: 'Indexed Image & Visual Media Websites',
      desc: 'High-resolution photography, SVG vector icons, wallpapers, and scientific schematics.',
      badge: '6 Visual Media Sites',
    },
    documents: {
      title: 'Official Technical Documentation & Specification Portals',
      desc: 'Direct access to internet protocol RFCs, W3C standards, kernel docs, and language books.',
      badge: '6 Documentation Portals',
    },
    news: {
      title: 'Engineering & Technology News Portals',
      desc: 'Breaking developer discussions, cybersecurity threat alerts, and software architecture trends.',
      badge: '6 Tech News Outlets',
    },
    scholar: {
      title: 'Academic Research Repositories & Citation Indexes',
      desc: 'Open-access scientific preprints, peer-reviewed computer science literature, and bibliometrics.',
      badge: '6 Research Repositories',
    },
  };

  const trendingTopics = [
    { label: 'Generative AI', icon: <IconZap size={13} />, query: 'artificial intelligence generative' },
    { label: 'System Design', icon: <IconTrendingUp size={13} />, query: 'distributed system architecture' },
    { label: 'Machine Learning', icon: <IconTrendingUp size={13} />, query: 'machine learning' },
    { label: 'DevOps', icon: <IconTrendingUp size={13} />, query: 'docker deployment pipeline' },
    { label: 'Inverted Index', icon: <IconTrendingUp size={13} />, query: 'inverted index postings' },
    { label: 'Cloud Computing', icon: <IconTrendingUp size={13} />, query: 'cloud computing redis' },
  ];

  // Helper function to map documents to rich visual previews
  function getDocumentImageUrl(doc) {
    const text = `${doc.title || ''} ${doc.snippet || ''} ${doc.document_id || ''} ${doc.url || ''}`.toLowerCase();
    if (text.includes('unsplash') || text.includes('photo')) {
      return 'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=700&auto=format&fit=crop&q=80';
    }
    if (text.includes('pexels') || text.includes('wallpaper')) {
      return 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=700&auto=format&fit=crop&q=80';
    }
    if (text.includes('pixabay') || text.includes('vector') || text.includes('svg')) {
      return 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=700&auto=format&fit=crop&q=80';
    }
    if (text.includes('wikimedia') || text.includes('commons') || text.includes('diagram') || text.includes('schematic')) {
      return 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=700&auto=format&fit=crop&q=80';
    }
    if (text.includes('inverted') || text.includes('index') || text.includes('retrieval') || text.includes('postings')) {
      return 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=700&auto=format&fit=crop&q=80';
    }
    if (text.includes('bm25') || text.includes('ranking') || text.includes('score') || text.includes('tfidf')) {
      return 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=700&auto=format&fit=crop&q=80';
    }
    if (text.includes('redis') || text.includes('cache') || text.includes('memory')) {
      return 'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=700&auto=format&fit=crop&q=80';
    }
    if (text.includes('neural') || text.includes('attention') || text.includes('transformer') || text.includes('pytorch') || text.includes('scholar')) {
      return 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=700&auto=format&fit=crop&q=80';
    }
    if (text.includes('docker') || text.includes('container') || text.includes('kubernetes')) {
      return 'https://images.unsplash.com/photo-1607799279861-4dd421887fb3?w=700&auto=format&fit=crop&q=80';
    }
    if (text.includes('linux') || text.includes('kernel') || text.includes('rust') || text.includes('cpp')) {
      return 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=700&auto=format&fit=crop&q=80';
    }
    if (text.includes('python') || text.includes('fastapi') || text.includes('javascript') || text.includes('react')) {
      return 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=700&auto=format&fit=crop&q=80';
    }
    return 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=700&auto=format&fit=crop&q=80';
  }

  // Visual Image Showcase Cards with Real High-Res URLs and Procedural Fallbacks
  const visualGallery = [
    {
      title: 'Inverted Index Postings List Architecture',
      subtitle: 'Term dictionary with binary delta-encoded docID lists and skipping pointers',
      dim: '3840×2160 UHD',
      imageUrl: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&auto=format&fit=crop&q=80',
      query: 'inverted index postings architecture',
      badge: 'Core Engine Spec',
      category: 'schematic',
    },
    {
      title: 'Okapi BM25 Ranking Saturation Curve',
      subtitle: 'Score vs Term Frequency with document length normalization (k1=1.2, b=0.75)',
      dim: '2560×1440 2K',
      imageUrl: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop&q=80',
      query: 'bm25 scoring normalization',
      badge: 'Algorithm Diagram',
      category: 'schematic',
    },
    {
      title: 'Redis Multi-Tier Query Cache Topology',
      subtitle: 'Sub-millisecond L1 memory cache with atomic TTL and invalidation',
      dim: '1920×1080 FHD',
      imageUrl: 'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&auto=format&fit=crop&q=80',
      query: 'redis query cache invalidation',
      badge: 'Cache Architecture',
      category: 'schematic',
    },
    {
      title: 'Transformer Attention & Neural Synapses',
      subtitle: 'Scaled dot-product attention and multi-head global sequence dependencies',
      dim: '3840×2160 4K',
      imageUrl: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&auto=format&fit=crop&q=80',
      query: 'transformer attention neural architecture',
      badge: 'Deep Learning',
      category: 'wallpaper',
    },
    {
      title: 'Web Crawler Safety & SSRF Guard',
      subtitle: 'Robots exclusion standard, DNS loopback block, and depth bounds',
      dim: '1920×1080 Diagram',
      imageUrl: 'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&auto=format&fit=crop&q=80',
      query: 'web crawler robots ssrf',
      badge: 'Security Blueprint',
      category: 'schematic',
    },
    {
      title: 'FastAPI & C++ Core Engine Bridge',
      subtitle: 'Subprocess stdin/stdout query dispatch pipeline with JSON streaming',
      dim: '1920×1080 Schematic',
      imageUrl: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&auto=format&fit=crop&q=80',
      query: 'fastapi backend architecture',
      badge: 'Pipeline Schematic',
      category: 'schematic',
    },
    {
      title: 'Distributed Consensus & Raft Cluster State',
      subtitle: 'Leader election, log replication, and split-brain resilience',
      dim: '3840×2160 4K',
      imageUrl: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80',
      query: 'distributed consensus raft',
      badge: 'Distributed Systems',
      category: 'wallpaper',
    },
    {
      title: 'Linux Kernel Virtual Memory Subsystem',
      subtitle: 'Page allocation, slab allocators, and hardware memory mapping',
      dim: '2560×1440 2K',
      imageUrl: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop&q=80',
      query: 'linux kernel virtual memory page',
      badge: 'Kernel Blueprint',
      category: 'schematic',
    },
  ];

  // Curated Technical Document Repository
  const documentLibrary = [
    {
      docId: 'doc_python_ds',
      title: 'Python 3.13 Data Structures Deep Dive',
      category: 'Documentation Tutorial',
      readTime: '5 min read',
      desc: 'Comprehensive overview of Python lists, dicts, sets, and algorithmic performance.',
      query: 'python data structures tutorial',
    },
    {
      docId: 'doc_ir_overview',
      title: 'Information Retrieval: Core Principles and Systems',
      category: 'Foundational Whitepaper',
      readTime: '4 min read',
      desc: 'Modern search engine principles, tokenization pipelines, and statistical scoring.',
      query: 'information retrieval principles',
    },
    {
      docId: 'doc_bm25_ranking',
      title: 'Okapi BM25 Scoring and Length Normalization',
      category: 'Algorithmic Specification',
      readTime: '6 min read',
      desc: 'Mathematical formulation of term saturation and length normalization parameters.',
      query: 'okapi bm25 scoring',
    },
    {
      docId: 'doc_fastapi_backend',
      title: 'FastAPI High-Performance Asynchronous APIs',
      category: 'Engineering Guide',
      readTime: '4 min read',
      desc: 'Building sub-millisecond REST search endpoints with Pydantic validation.',
      query: 'fastapi web framework',
    },
    {
      docId: 'doc_distributed_raft',
      title: 'Distributed Consensus and Raft State Machine',
      category: 'Distributed Systems Spec',
      readTime: '7 min read',
      desc: 'Consensus protocols, replicated logs, and high-availability clustered architectures.',
      query: 'distributed consensus raft',
    },
    {
      docId: 'doc_cpp_standard',
      title: 'C++17 Inverted Index Memory Architecture',
      category: 'Engine Specification',
      readTime: '5 min read',
      desc: 'STL hash maps, binary serialization, and zero-copy postings traversal.',
      query: 'cpp17 standard library',
    },
  ];

  // Engineering News & Releases
  const engineeringNews = [
    {
      title: 'SearchX Inverted Index Engine v1.0 Deployed',
      date: 'Today',
      author: 'SearchX Core Team',
      desc: 'Sub-millisecond term posting traversal compiled with MinGW-w64 GCC C++17.',
      query: 'inverted index postings',
    },
    {
      title: 'Redis Multi-Tier Query Caching Activated',
      date: 'Today',
      author: 'Performance Infra',
      desc: 'Achieved sub-millisecond cache hit response with atomic TTL expiration and crawl invalidation.',
      query: 'redis query cache',
    },
    {
      title: 'PostgreSQL Relational Persistence Layer Verified',
      date: 'Yesterday',
      author: 'Database Systems',
      desc: 'Full ACID relational storage with URL content hashing and automated schema migrations.',
      query: 'postgresql persistence storage',
    },
    {
      title: 'Web Crawler SSRF Security Boundaries Enforced',
      date: '2 days ago',
      author: 'Security Operations',
      desc: 'Strict RFC 1918 loopback blocking and robots.txt parsing validated across all targets.',
      query: 'web crawler robots ssrf',
    },
  ];

  // Academic Research Papers & Citations
  const scholarPapers = [
    {
      title: 'Okapi at TREC-3: Probabilistic Term Weighting and Relevance Feedback',
      authors: 'S. E. Robertson, S. Walker, S. Jones, M. M. Hancock-Beaulieu, M. Gatford',
      year: '1994',
      citations: '8,420 citations',
      desc: 'The landmark paper introducing the BM25 probabilistic retrieval ranking formulation.',
      query: 'robertson okapi trec3 bm25',
    },
    {
      title: 'Term-Weighting Approaches in Automatic Text Retrieval',
      authors: 'G. Salton, C. Buckley',
      year: '1988',
      citations: '14,350 citations',
      desc: 'Evaluation of TF-IDF weighting schemes, cosine similarity, and sublinear scaling.',
      query: 'tfidf term weighting salton',
    },
    {
      title: 'Inverted Files for Text Search Engines: Query Processing and Compression',
      authors: 'J. Zobel, A. Moffat',
      year: '2006',
      citations: '2,890 citations',
      desc: 'Comprehensive survey of index compression, postings list traversal, and caching strategies.',
      query: 'inverted files text search engines zobel',
    },
    {
      title: 'The Anatomy of a Large-Scale Hypertextual Web Search Engine',
      authors: 'S. Brin, L. Page',
      year: '1998',
      citations: '32,100 citations',
      desc: 'Foundational architecture of modern web crawling, inverted indexing, and link analysis.',
      query: 'anatomy large scale web search engine brin page',
    },
  ];

  const queryTerms = query ? query.toLowerCase().split(/\s+/).filter(Boolean) : [];

  return (
    <div className={`app-layout ${darkMode ? 'theme-dark' : 'theme-light'}`}>
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        health={health}
        darkMode={darkMode}
        onToggleDarkMode={toggleDarkMode}
      />

      <main className="main-content">
        {activeTab === 'admin' ? (
          <AdminDashboard onSourceAdded={checkHealth} />
        ) : (
          <div className="search-page-container">
            {/* Search Hero */}
            <div className={`search-hero ${searchResponse ? 'has-results' : ''}`}>
              {!searchResponse && (
                <div className="hero-branding">
                  {/* Glowing 3D X Emblem */}
                  <div className="hero-3d-emblem">
                    <div className="emblem-glow"></div>
                    <span className="emblem-sparkle left">✦</span>
                    <span className="emblem-x">✕</span>
                    <span className="emblem-sparkle right">✦</span>
                  </div>

                  <h1 className="hero-title">Search<span className="brand-accent">X</span></h1>
                  <p className="hero-subtitle">
                    <span className="divider-line"></span>
                    A Smarter Search Experience
                    <span className="divider-line"></span>
                  </p>
                </div>
              )}

              <SearchBar
                initialQuery={query}
                onSearch={(q) => executeSearch(q, 1)}
                loading={loading}
                algo={algo}
                setAlgo={handleAlgoChange}
                mode={mode}
                setMode={handleModeChange}
                activeCategory={activeCategory}
                onSelectCategory={handleCategoryChange}
              />

              {/* Dynamic Showcase based on activeCategory */}
              {!searchResponse && (
                <div key={activeCategory} className="category-showcase-section animate-slide-fade">
                  {/* Common Category Verified Websites Directory */}
                  <div className="category-view-box">
                    <div className="category-sources-section">
                      <div className="category-view-header">
                        <div>
                          <h3 className="category-view-title">{categoryHeaders[activeCategory]?.title}</h3>
                          <p className="category-view-desc">{categoryHeaders[activeCategory]?.desc}</p>
                        </div>
                        <span className="category-view-badge">{categoryHeaders[activeCategory]?.badge}</span>
                      </div>

                      <div className="category-sources-grid">
                        {(categoryWebsites[activeCategory] || []).map((site, siteIdx) => (
                          <div
                            key={site.domain}
                            className="category-source-card"
                            style={{ '--card-index': siteIdx }}
                          >
                            {site.bannerImg && (
                              <div className="source-banner-wrap">
                                <SmartImage
                                  src={site.bannerImg}
                                  alt={site.name}
                                  aspectRatio="16/9"
                                  category="wallpaper"
                                  onPreviewClick={() =>
                                    setSelectedImage({
                                      title: `${site.name} Visual Media Portal`,
                                      subtitle: site.desc,
                                      imageUrl: site.bannerImg,
                                      badge: site.badge,
                                      query: site.query,
                                      dim: '3840×2160 UHD',
                                      url: site.url,
                                    })
                                  }
                                />
                              </div>
                            )}
                            <div className="source-card-header">
                              <div className="source-title-row">
                                <span className="source-name">{site.name}</span>
                                <span className="source-badge">{site.badge}</span>
                              </div>
                              <span className="source-domain">
                                <span className="source-domain-dot"></span>
                                {site.domain}
                              </span>
                            </div>
                            <p className="source-desc">{site.desc}</p>
                            <div className="source-actions">
                              <button
                                type="button"
                                className="btn-source-search"
                                onClick={() => executeSearch(site.query, 1)}
                                title={`Search ${site.name} documents on SearchX`}
                              >
                                <IconSearch size={13} /> Search in SearchX
                              </button>
                              <a
                                href={site.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn-source-visit"
                                title={`Visit ${site.domain} directly`}
                              >
                                <IconExternalLink size={13} /> Visit Site
                              </a>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Category 1: WEB -> Trending Searches */}
                    {activeCategory === 'web' && (
                      <div className="trending-section">
                        <div className="trending-header">
                          <span className="trending-icon">
                            <IconTrendingUp size={15} />
                          </span>
                          <span className="trending-title">Trending Searches</span>
                        </div>

                        <div className="trending-pills">
                          {trendingTopics.map((item) => (
                            <button
                              key={item.label}
                              type="button"
                              className="trending-pill"
                              onClick={() => executeSearch(item.query, 1)}
                            >
                              <span className="pill-icon">{item.icon}</span>
                              <span className="pill-text">{item.label}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Category 2: IMAGES -> Visual Architecture & Diagram Schematics */}
                    {activeCategory === 'images' && (
                      <div className="category-content-subblock">
                        <div className="category-section-subtitle">
                          <IconImage size={15} /> Curated Visual Gallery & Wallpapers
                        </div>
                        <div className="image-showcase-grid">
                          {visualGallery.map((item, idx) => (
                            <div
                              key={idx}
                              className="image-showcase-card"
                              style={{ '--card-index': idx }}
                            >
                              <SmartImage
                                src={item.imageUrl}
                                alt={item.title}
                                aspectRatio="16/9"
                                category={item.category || 'schematic'}
                                onPreviewClick={() => setSelectedImage(item)}
                              />
                              <div
                                className="image-card-info"
                                onClick={() => setSelectedImage(item)}
                              >
                                <div className="image-card-header-row">
                                  <span className="image-spec-badge">{item.badge}</span>
                                  <span className="image-dim-tag">{item.dim}</span>
                                </div>
                                <h4 className="image-card-title">{item.title}</h4>
                                <p className="image-card-sub">{item.subtitle}</p>
                                <div className="image-card-action">
                                  <span className="action-link">Expand Image &rarr;</span>
                                  <button
                                    type="button"
                                    className="btn-source-search"
                                    style={{ flex: 'none', padding: '0.3rem 0.65rem', fontSize: '0.74rem' }}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      executeSearch(item.query, 1);
                                    }}
                                  >
                                    Search Topic
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Category 3: DOCUMENTS -> Curated Technical Document Library */}
                    {activeCategory === 'documents' && (
                      <div className="category-content-subblock">
                        <div className="category-section-subtitle">
                          <IconFileText size={15} /> Ingested Technical Whitepapers & Manuals
                        </div>
                        <div className="docs-showcase-grid">
                          {documentLibrary.map((doc) => (
                            <div key={doc.docId} className="doc-showcase-card">
                              <div className="doc-card-top">
                                <span className="doc-type-pill">{doc.category}</span>
                                <span className="doc-read-time">{doc.readTime}</span>
                              </div>
                              <h4 className="doc-card-title">{doc.title}</h4>
                              <p className="doc-card-desc">{doc.desc}</p>
                              <div className="doc-card-actions">
                                <button
                                  type="button"
                                  className="btn-doc-read"
                                  onClick={() => setSelectedDocId(doc.docId)}
                                >
                                  <IconFileText size={14} className="btn-inline-icon" /> Read Document
                                </button>
                                <button
                                  type="button"
                                  className="btn-doc-search"
                                  onClick={() => executeSearch(doc.query, 1)}
                                >
                                  Search Topic &rarr;
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Category 4: NEWS -> Engineering Releases & Ingestion Logs */}
                    {activeCategory === 'news' && (
                      <div className="category-content-subblock">
                        <div className="category-section-subtitle">
                          <IconNewspaper size={15} /> SearchX Core Ingestion Changelog
                        </div>
                        <div className="news-showcase-list">
                          {engineeringNews.map((item, idx) => (
                            <div
                              key={idx}
                              className="news-showcase-item"
                              onClick={() => executeSearch(item.query, 1)}
                              role="button"
                              tabIndex={0}
                            >
                              <div className="news-meta-row">
                                <span className="news-date-pill">{item.date}</span>
                                <span className="news-author">{item.author}</span>
                              </div>
                              <h4 className="news-item-title">{item.title}</h4>
                              <p className="news-item-desc">{item.desc}</p>
                              <span className="news-read-link">Search Ingestion Topic &rarr;</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Category 5: SCHOLAR -> Academic Research & Formulations */}
                    {activeCategory === 'scholar' && (
                      <div className="category-content-subblock">
                        <div className="category-section-subtitle">
                          <IconGraduationCap size={15} /> Landmark Peer-Reviewed Papers
                        </div>
                        <div className="scholar-showcase-list">
                          {scholarPapers.map((paper, idx) => (
                            <div
                              key={idx}
                              className="scholar-showcase-item"
                              onClick={() => executeSearch(paper.query, 1)}
                              role="button"
                              tabIndex={0}
                            >
                              <div className="scholar-meta-row">
                                <span className="scholar-pdf-badge">[PDF Research]</span>
                                <span className="scholar-citations">{paper.citations}</span>
                                <span className="scholar-year">&bull; {paper.year}</span>
                              </div>
                              <h4 className="scholar-paper-title">{paper.title}</h4>
                              <p className="scholar-authors">{paper.authors}</p>
                              <p className="scholar-desc">{paper.desc}</p>
                              <span className="scholar-search-action">Retrieve Scholarly Topic &rarr;</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Error State */}
            {error && (
              <div className="search-error-banner" role="alert">
                <span className="error-icon">
                  <IconAlertCircle size={18} />
                </span>
                <div className="error-text">
                  <strong>Search Failed:</strong> {error}
                </div>
                <button
                  type="button"
                  className="btn-retry"
                  onClick={() => executeSearch(query, page)}
                >
                  Retry
                </button>
              </div>
            )}

            {/* Loading Skeleton */}
            {loading && (
              <div className="loading-state" aria-live="polite">
                <div className="skeleton-card"></div>
                <div className="skeleton-card"></div>
                <div className="skeleton-card"></div>
              </div>
            )}

            {/* Search Results Display */}
            {!loading && searchResponse && (
              <section
                key={`${searchResponse.query}-${searchResponse.page}-${activeCategory}`}
                className="search-results-section animate-slide-fade"
              >
                {/* Result Meta Bar */}
                <div className="results-meta-bar">
                  <div className="meta-bar-left">
                    <span>
                      About <strong>{searchResponse.total_hits}</strong> results for{' '}
                      <em>"{searchResponse.query}"</em> (Algorithm:{' '}
                      <strong className="algo-tag">{searchResponse.algorithm.toUpperCase()}</strong>, Match:{' '}
                      <strong>{mode.toUpperCase()}</strong>, Category:{' '}
                      <strong className="category-tag">{activeCategory.toUpperCase()}</strong>)
                    </span>
                  </div>
                  <div className="meta-bar-right">
                    <span className="results-speed-tag">
                      <IconZap size={12} className="btn-inline-icon" /> 0.004s
                    </span>
                  </div>
                </div>

                {/* Sub-bar Category Switcher for Live Results */}
                <div className="results-category-tabs" role="tablist" aria-label="Search Result Categories">
                  {[
                    { id: 'web', label: 'All', icon: <IconGlobe size={14} /> },
                    { id: 'images', label: 'Images', icon: <IconImage size={14} /> },
                    { id: 'documents', label: 'Documents', icon: <IconFileText size={14} /> },
                    { id: 'news', label: 'News', icon: <IconNewspaper size={14} /> },
                    { id: 'scholar', label: 'Scholar', icon: <IconGraduationCap size={14} /> },
                  ].map((cat) => (
                    <button
                      key={cat.id}
                      type="button"
                      role="tab"
                      aria-selected={activeCategory === cat.id}
                      className={`result-category-tab ${activeCategory === cat.id ? 'active' : ''}`}
                      onClick={() => handleCategoryChange(cat.id)}
                    >
                      <span className="tab-svg">{cat.icon}</span>
                      <span>{cat.label}</span>
                    </button>
                  ))}
                </div>

                {/* Standard 2-Column Layout: Left Search Stream + Right Knowledge Card */}
                <div className="results-two-column-layout">
                  {/* Left Column: Results List + Pagination */}
                  <div className="results-main-column">
                    {searchResponse.total_hits === 0 ? (
                      <div className="zero-results-card">
                        <span className="zero-icon">
                          <IconSearch size={36} />
                        </span>
                        <h3>No matching documents found</h3>
                        <p>
                          Your search - <strong>{searchResponse.query}</strong> - did not match any documents in the index.
                        </p>
                        <ul className="search-tips">
                          <li>Make sure all words are spelled correctly.</li>
                          <li>Try different or more general keywords (e.g. <em>"machine learning"</em>, <em>"python"</em>, <em>"distributed"</em>).</li>
                          <li>Switch match mode from <strong>Match All (AND)</strong> to <strong>Match Any (OR)</strong>.</li>
                          <li>Add more crawl sources in the Admin Dashboard to index external websites.</li>
                        </ul>
                      </div>
                    ) : (
                      <>
                        {activeCategory === 'images' ? (
                          <div className="image-results-grid">
                            {searchResponse.results.map((item, idx) => {
                              const imgUrl = getDocumentImageUrl(item);
                              return (
                                <div
                                  key={item.document_id}
                                  className="image-result-card"
                                  style={{ '--card-index': idx }}
                                >
                                  <SmartImage
                                    src={imgUrl}
                                    alt={item.title}
                                    aspectRatio="16/10"
                                    category="schematic"
                                    onPreviewClick={() =>
                                      setSelectedImage({
                                        title: item.title,
                                        subtitle: item.snippet,
                                        imageUrl: imgUrl,
                                        badge: 'Search Result',
                                        dim: '1920×1080 FHD',
                                        url: item.url,
                                      })
                                    }
                                  />
                                  <div className="image-result-info">
                                    <h4
                                      className="image-result-title"
                                      onClick={() => setSelectedDocId(item.document_id)}
                                      title="Read full indexed document"
                                    >
                                      {item.title}
                                    </h4>
                                    <span className="image-result-domain font-mono">
                                      {item.url || 'Internal Document'}
                                    </span>
                                    <div className="image-result-footer">
                                      <span className="image-score-tag">
                                        Score: {item.score ? item.score.toFixed(3) : '1.00'}
                                      </span>
                                      <button
                                        type="button"
                                        className="btn-source-search"
                                        style={{ flex: 'none', padding: '0.2rem 0.55rem', fontSize: '0.72rem' }}
                                        onClick={() => setSelectedDocId(item.document_id)}
                                      >
                                        Read Spec &rarr;
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="results-list">
                            {searchResponse.results.map((item) => (
                              <SearchResultCard
                                key={item.document_id}
                                result={item}
                                onSelectDocument={setSelectedDocId}
                                queryTerms={queryTerms}
                              />
                            ))}
                          </div>
                        )}

                        <Pagination
                          currentPage={searchResponse.page}
                          totalHits={searchResponse.total_hits}
                          limit={pageSize}
                          onPageChange={handlePageChange}
                        />
                      </>
                    )}
                  </div>

                  {/* Right Column: SearchX Corpus Knowledge Card */}
                  <aside className="results-knowledge-column" aria-label="Index Knowledge Panel">
                    <div className="knowledge-panel-card">
                      <div className="knowledge-header">
                        <div className="knowledge-badge">Corpus Knowledge Panel</div>
                        <h3 className="knowledge-title">SearchX Index Engine</h3>
                        <p className="knowledge-subtitle">Production C++ Retrieval Core</p>
                      </div>

                      <div className="knowledge-stats-list">
                        <div className="knowledge-stat-item">
                          <span className="stat-name">Indexed Documents</span>
                          <span className="stat-number">{health?.total_documents ?? 13} docs</span>
                        </div>
                        <div className="knowledge-stat-item">
                          <span className="stat-name">Vocabulary Size</span>
                          <span className="stat-number">{health?.vocabulary_size ?? 334} terms</span>
                        </div>
                        <div className="knowledge-stat-item">
                          <span className="stat-name">Avg Doc Length</span>
                          <span className="stat-number">
                            {health?.average_document_length ? health.average_document_length.toFixed(1) : '41.8'} words
                          </span>
                        </div>
                        <div className="knowledge-stat-item">
                          <span className="stat-name">Active Ranking</span>
                          <span className="stat-badge">{algo === 'bm25' ? 'Okapi BM25' : 'Sublinear TF-IDF'}</span>
                        </div>
                        <div className="knowledge-stat-item">
                          <span className="stat-name">Cache Acceleration</span>
                          <span className="stat-badge-success">Redis L1 / In-Mem L2</span>
                        </div>
                      </div>

                      <div className="knowledge-divider"></div>

                      <div className="knowledge-action-box">
                        <p className="knowledge-action-desc">
                          Need to index more web content or inspect query telemetry?
                        </p>
                        <button
                          type="button"
                          className="btn-knowledge-action"
                          onClick={() => setActiveTab('admin')}
                        >
                          <IconSettings size={15} className="btn-inline-icon" /> Open Control Center
                        </button>
                      </div>
                    </div>
                  </aside>
                </div>
              </section>
            )}
          </div>
        )}
      </main>

      {/* Full Document Inspection Modal */}
      {selectedDocId && (
        <DocumentModal
          documentId={selectedDocId}
          onClose={() => setSelectedDocId(null)}
        />
      )}

      {/* Image Lightbox Preview Modal */}
      {selectedImage && (
        <ImageLightboxModal
          image={selectedImage}
          onClose={() => setSelectedImage(null)}
          onSearchRelated={(q) => executeSearch(q, 1)}
        />
      )}

      {/* Footer */}
      <footer className="app-footer">
        <p>
          SearchX &bull; C++ Core Retrieval Engine &bull; FastAPI Backend &bull; React Frontend
        </p>
      </footer>
    </div>
  );
}

export default App;
