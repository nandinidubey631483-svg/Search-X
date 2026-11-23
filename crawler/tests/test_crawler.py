"""Unit tests for Crawler and SSRF protection (Module F)."""
import pytest
from crawler.app.crawler import (
    CrawlConfig,
    Crawler,
    SSRFValidationError,
    SSRFValidator,
)


def mock_public_dns(hostname: str):
    """Mock DNS resolver returning safe public IP."""
    return ["93.184.216.34"]


def mock_private_dns(hostname: str):
    """Mock DNS resolver returning an internal/private IP (simulating DNS rebinding)."""
    return ["192.168.1.100"]


def test_ssrf_validator_safe_ips():
    assert SSRFValidator.is_safe_ip("93.184.216.34")
    assert SSRFValidator.is_safe_ip("8.8.8.8")
    assert SSRFValidator.is_safe_ip("1.1.1.1")


def test_ssrf_validator_blocks_private_and_loopback_ips():
    blocked_ips = [
        "127.0.0.1",
        "127.0.0.2",
        "10.0.0.1",
        "10.255.255.255",
        "192.168.0.1",
        "192.168.1.50",
        "172.16.0.1",
        "172.31.255.255",
        "169.254.169.254",  # AWS/Cloud metadata service
        "::1",              # IPv6 loopback
        "fe80::1",          # IPv6 link-local
    ]
    for ip in blocked_ips:
        assert not SSRFValidator.is_safe_ip(ip), f"IP {ip} should be blocked"


def test_ssrf_validate_url_rejects_localhost_and_private_dns():
    with pytest.raises(SSRFValidationError, match="loopback"):
        SSRFValidator.validate_url("http://localhost:8080/admin", dns_resolver=mock_public_dns)

    with pytest.raises(SSRFValidationError, match="loopback"):
        SSRFValidator.validate_url("http://127.0.0.1/test", dns_resolver=mock_public_dns)

    with pytest.raises(SSRFValidationError, match="forbidden IP"):
        SSRFValidator.validate_url("http://internal-corp-service.com/data", dns_resolver=mock_private_dns)


def test_crawler_canonicalize_url():
    raw_url = "HTTP://Example.COM:80/path/to/page/?utm_source=twitter&q=search&fbclid=123#heading"
    canon = Crawler.canonicalize_url(raw_url)
    assert canon == "http://example.com:80/path/to/page?q=search"
    assert "utm_source" not in canon
    assert "fbclid" not in canon
    assert "#heading" not in canon


def test_crawler_link_extraction():
    html = """
    <html><body>
        <a href="/about">About Us</a>
        <a href="https://example.com/docs">Documentation</a>
        <a href="javascript:void(0)">Ignore JS</a>
        <a href="#section">Ignore Fragment</a>
        <a href="mailto:info@example.com">Ignore Mailto</a>
    </body></html>
    """
    config = CrawlConfig(seed_urls=["https://example.com/"])
    crawler = Crawler(config=config, dns_resolver=mock_public_dns)
    links = crawler.extract_links(html, "https://example.com/home")

    assert "https://example.com/about" in links
    assert "https://example.com/docs" in links
    assert len(links) == 2


def test_crawler_domain_restrictions():
    pages = {
        "https://allowed.com/": (
            200,
            b"<html><body><a href=\"https://allowed.com/page2\">Internal</a><a href=\"https://forbidden.com/bad\">External</a></body></html>",
            "https://allowed.com/",
            {"Content-Type": "text/html"},
        ),
        "https://allowed.com/page2": (
            200,
            b"<html><body><title>Page 2</title><p>Allowed content</p></body></html>",
            "https://allowed.com/page2",
            {"Content-Type": "text/html"},
        ),
        "https://forbidden.com/bad": (
            200,
            b"<html><body><title>Forbidden</title><p>Off limits</p></body></html>",
            "https://forbidden.com/bad",
            {"Content-Type": "text/html"},
        ),
    }

    def mock_fetch(url: str):
        return pages.get(url, (404, b"Not found", url, {}))

    config = CrawlConfig(
        seed_urls=["https://allowed.com/"],
        allowed_domains={"allowed.com"},
        max_depth=2,
        max_pages=10,
        respect_robots_txt=False,
    )
    crawler = Crawler(config=config, dns_resolver=mock_public_dns, http_fetcher=mock_fetch)
    result = crawler.run()

    crawled_urls = {d.source_url for d in result.documents}
    assert "https://allowed.com/" in crawled_urls
    assert "https://allowed.com/page2" in crawled_urls
    assert "https://forbidden.com/bad" not in crawled_urls


def test_crawler_depth_limit():
    # Chain: A -> B -> C -> D
    pages = {
        "https://example.com/a": (200, b"<a href=\"https://example.com/b\">B</a>", "https://example.com/a", {"Content-Type": "text/html"}),
        "https://example.com/b": (200, b"<a href=\"https://example.com/c\">C</a>", "https://example.com/b", {"Content-Type": "text/html"}),
        "https://example.com/c": (200, b"<a href=\"https://example.com/d\">D</a>", "https://example.com/c", {"Content-Type": "text/html"}),
        "https://example.com/d": (200, b"Deepest", "https://example.com/d", {"Content-Type": "text/html"}),
    }

    def mock_fetch(url: str):
        return pages.get(url, (404, b"Not found", url, {}))

    # max_depth = 1: should fetch a (depth 0) and b (depth 1), but NOT c (depth 2)
    config = CrawlConfig(
        seed_urls=["https://example.com/a"],
        allowed_domains={"example.com"},
        max_depth=1,
        max_pages=10,
        respect_robots_txt=False,
    )
    crawler = Crawler(config=config, dns_resolver=mock_public_dns, http_fetcher=mock_fetch)
    result = crawler.run()

    crawled_urls = {d.source_url for d in result.documents}
    assert "https://example.com/a" in crawled_urls
    assert "https://example.com/b" in crawled_urls
    assert "https://example.com/c" not in crawled_urls


def test_crawler_page_limit():
    pages = {
        "https://example.com/root": (
            200,
            b"<a href=\"/p1\">1</a><a href=\"/p2\">2</a><a href=\"/p3\">3</a><a href=\"/p4\">4</a>",
            "https://example.com/root",
            {"Content-Type": "text/html"},
        ),
        "https://example.com/p1": (200, b"P1 content", "https://example.com/p1", {"Content-Type": "text/html"}),
        "https://example.com/p2": (200, b"P2 content", "https://example.com/p2", {"Content-Type": "text/html"}),
        "https://example.com/p3": (200, b"P3 content", "https://example.com/p3", {"Content-Type": "text/html"}),
        "https://example.com/p4": (200, b"P4 content", "https://example.com/p4", {"Content-Type": "text/html"}),
    }

    def mock_fetch(url: str):
        return pages.get(url, (404, b"Not found", url, {}))

    # max_pages = 3: should stop after 3 pages even though more links are queued
    config = CrawlConfig(
        seed_urls=["https://example.com/root"],
        allowed_domains={"example.com"},
        max_depth=2,
        max_pages=3,
        respect_robots_txt=False,
    )
    crawler = Crawler(config=config, dns_resolver=mock_public_dns, http_fetcher=mock_fetch)
    result = crawler.run()

    assert result.pages_crawled == 3
    assert len(result.documents) == 3


def test_crawler_respects_robots_txt():
    pages = {
        "https://example.com/robots.txt": (
            200,
            b"User-agent: *\nDisallow: /admin/\nDisallow: /private\n",
            "https://example.com/robots.txt",
            {"Content-Type": "text/plain"},
        ),
        "https://example.com/": (
            200,
            b"<a href=\"/public\">Public</a><a href=\"/admin/dashboard\">Admin</a>",
            "https://example.com/",
            {"Content-Type": "text/html"},
        ),
        "https://example.com/public": (200, b"Public page content", "https://example.com/public", {"Content-Type": "text/html"}),
        "https://example.com/admin/dashboard": (200, b"Secret admin page", "https://example.com/admin/dashboard", {"Content-Type": "text/html"}),
    }

    def mock_fetch(url: str):
        return pages.get(url, (404, b"Not found", url, {}))

    config = CrawlConfig(
        seed_urls=["https://example.com/"],
        allowed_domains={"example.com"},
        max_depth=2,
        respect_robots_txt=True,
    )
    crawler = Crawler(config=config, dns_resolver=mock_public_dns, http_fetcher=mock_fetch)
    result = crawler.run()

    crawled_urls = {d.source_url for d in result.documents}
    assert "https://example.com/public" in crawled_urls
    assert "https://example.com/admin/dashboard" not in crawled_urls
    assert "https://example.com/admin/dashboard" in result.failed_urls


def test_crawler_resilience_to_errors():
    pages = {
        "https://example.com/": (
            200,
            b"<a href=\"/broken\">404</a><a href=\"/server_error\">500</a><a href=\"/ok\">OK</a>",
            "https://example.com/",
            {"Content-Type": "text/html"},
        ),
        "https://example.com/broken": (404, b"Not found", "https://example.com/broken", {}),
        "https://example.com/server_error": (500, b"Internal Error", "https://example.com/server_error", {}),
        "https://example.com/ok": (200, b"OK page", "https://example.com/ok", {"Content-Type": "text/html"}),
    }

    def mock_fetch(url: str):
        return pages.get(url, (404, b"Not found", url, {}))

    config = CrawlConfig(
        seed_urls=["https://example.com/"],
        allowed_domains={"example.com"},
        max_depth=2,
        respect_robots_txt=False,
    )
    crawler = Crawler(config=config, dns_resolver=mock_public_dns, http_fetcher=mock_fetch)
    result = crawler.run()

    crawled_urls = {d.source_url for d in result.documents}
    assert "https://example.com/ok" in crawled_urls
    assert "https://example.com/broken" in result.failed_urls
    assert "https://example.com/server_error" in result.failed_urls
