"""
Controlled Web Crawler for SearchX.
Implements domain allowlisting, SSRF protection with DNS-resolved IP validation,
redirect destination validation, robots.txt politeness, and depth/page limits.
Complies with PROJECT_CONTEXT.md Module F.
"""
from __future__ import annotations

import collections
import ipaddress
import logging
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Deque, Dict, List, Optional, Set, Tuple

from .models import Document, DocumentStatus
from .text_processor import TextProcessor

logger = logging.getLogger("searchx.crawler")


class SSRFValidationError(ValueError):
    """Raised when a URL resolves to a forbidden, private, or internal IP address."""
    pass


@dataclass
class CrawlConfig:
    """Configuration governing crawler safety, politeness, and boundaries."""
    seed_urls: List[str]
    allowed_domains: Set[str] = field(default_factory=set)
    max_depth: int = 2
    max_pages: int = 50
    delay_seconds: float = 0.5
    timeout_seconds: float = 10.0
    max_response_bytes: int = 2 * 1024 * 1024  # 2 MB limit
    user_agent: str = "SearchXBot/1.0 (+http://localhost/searchx-bot)"
    respect_robots_txt: bool = True


@dataclass
class CrawlResult:
    """Summary of a completed or stopped crawl job."""
    documents: List[Document] = field(default_factory=list)
    visited_urls: Set[str] = field(default_factory=set)
    failed_urls: Dict[str, str] = field(default_factory=dict)
    pages_crawled: int = 0
    start_time: str = ""
    end_time: str = ""


class SSRFValidator:
    """Validates hostnames and resolved IP addresses to protect against SSRF vulnerabilities."""

    @staticmethod
    def is_safe_ip(ip_str: str) -> bool:
        """Check if an IP address is a safe, publicly routable address."""
        try:
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return False
            # Check IPv4 mapped or translated
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
                return SSRFValidator.is_safe_ip(str(ip.ipv4_mapped))
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_url(url: str, dns_resolver: Optional[Callable[[str], List[str]]] = None) -> None:
        """
        Validate URL scheme, structure, and ensure resolved IPs are public and safe.
        Raises SSRFValidationError on violation.
        """
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise SSRFValidationError(f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed.")

        hostname = parsed.hostname
        if not hostname:
            raise SSRFValidationError("URL lacks a valid hostname.")

        # Disallow explicit localhost names
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            raise SSRFValidationError(f"Host '{hostname}' resolves to loopback/localhost.")

        # Resolve hostname via DNS
        if dns_resolver is not None:
            resolved_ips = dns_resolver(hostname)
        else:
            try:
                addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
                resolved_ips = [info[4][0] for info in addr_info]
            except socket.gaierror as e:
                raise SSRFValidationError(f"DNS resolution failed for host '{hostname}': {e}")

        if not resolved_ips:
            raise SSRFValidationError(f"No IP addresses resolved for host '{hostname}'.")

        for ip in resolved_ips:
            if not SSRFValidator.is_safe_ip(ip):
                raise SSRFValidationError(
                    f"Security violation: host '{hostname}' resolved to forbidden IP '{ip}'."
                )


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Custom HTTP redirect handler enforcing SSRF validation on all redirect targets."""

    def __init__(self, allowed_domains: Set[str], ssrf_validator: Callable[[str], None]) -> None:
        super().__init__()
        self.allowed_domains = allowed_domains
        self.ssrf_validator = ssrf_validator

    def redirect_request(self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Optional[urllib.request.Request]:
        # Validate target redirect URL
        try:
            self.ssrf_validator(newurl)
        except SSRFValidationError as e:
            logger.warning(f"Blocked redirect to forbidden address '{newurl}': {e}")
            raise urllib.error.HTTPError(newurl, 403, f"Blocked unsafe redirect: {e}", headers, fp)

        # Ensure redirect stays within allowed domains
        parsed = urllib.parse.urlparse(newurl)
        if self.allowed_domains:
            dest_host = (parsed.hostname or "").lower()
            if not any(dest_host == d.lower() or dest_host.endswith("." + d.lower()) for d in self.allowed_domains):
                logger.warning(f"Blocked redirect to unapproved domain '{dest_host}'")
                raise urllib.error.HTTPError(newurl, 403, f"Redirect to unapproved domain '{dest_host}'", headers, fp)

        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Crawler:
    """Controlled, polite web crawler with robust safety checks and duplicate handling."""

    def __init__(
        self,
        config: CrawlConfig,
        text_processor: Optional[TextProcessor] = None,
        dns_resolver: Optional[Callable[[str], List[str]]] = None,
        http_fetcher: Optional[Callable[[str], Tuple[int, bytes, str, Dict[str, str]]]] = None,
    ) -> None:
        self.config = config
        self.text_processor = text_processor or TextProcessor()
        self.dns_resolver = dns_resolver
        self.http_fetcher = http_fetcher
        self._robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

    def _validate_url_safety(self, url: str) -> None:
        """Validate URL safety and SSRF protections."""
        SSRFValidator.validate_url(url, dns_resolver=self.dns_resolver)

    def _is_domain_allowed(self, url: str) -> bool:
        """Check whether the domain of url matches config.allowed_domains."""
        if not self.config.allowed_domains:
            return True
        parsed = urllib.parse.urlparse(url)
        hostname = (parsed.hostname or "").lower()
        return any(hostname == d.lower() or hostname.endswith("." + d.lower()) for d in self.config.allowed_domains)

    @staticmethod
    def canonicalize_url(url: str) -> str:
        """Canonicalize URL: lowercase scheme & host, strip fragments and tracking params."""
        parsed = urllib.parse.urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"

        # Normalize trailing slashes for non-root paths
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        # Strip query parameters that are standard analytics trackers
        query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        cleaned_params = [
            (k, v) for k, v in query_params
            if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid", "ref")
        ]
        query = urllib.parse.urlencode(cleaned_params)

        return urllib.parse.urlunparse((scheme, netloc, path, "", query, ""))

    def _is_robots_allowed(self, url: str) -> bool:
        """Check robots.txt compliance for the URL."""
        if not self.config.respect_robots_txt:
            return True

        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        if base not in self._robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = f"{base}/robots.txt"
            try:
                # If custom fetcher is provided, try reading robots.txt content
                if self.http_fetcher:
                    status, content, _, _ = self.http_fetcher(robots_url)
                    if status == 200:
                        lines = content.decode("utf-8", errors="replace").splitlines()
                        rp.parse(lines)
                    else:
                        rp.allow_all = True
                else:
                    self._validate_url_safety(robots_url)
                    rp.set_url(robots_url)
                    rp.read()
            except Exception:
                # Default to permissive if robots.txt unreachable
                rp.allow_all = True
            self._robots_cache[base] = rp

        return self._robots_cache[base].can_fetch(self.config.user_agent, url)

    def _fetch_page(self, url: str) -> Tuple[int, bytes, str, Dict[str, str]]:
        """
        Fetch web page content safely.
        Returns (status_code, content_bytes, final_url, headers).
        """
        if self.http_fetcher:
            return self.http_fetcher(url)

        # Standard network fetch with safe redirect handling
        handler = SafeRedirectHandler(
            allowed_domains=self.config.allowed_domains,
            ssrf_validator=self._validate_url_safety,
        )
        opener = urllib.request.build_opener(handler)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9",
            },
        )

        with opener.open(req, timeout=self.config.timeout_seconds) as resp:
            content = resp.read(self.config.max_response_bytes + 1)
            if len(content) > self.config.max_response_bytes:
                raise ValueError(f"Response size exceeded limit of {self.config.max_response_bytes} bytes")
            final_url = resp.geturl()
            status = resp.status if hasattr(resp, "status") else 200
            headers = dict(resp.headers)
            return status, content, final_url, headers

    def extract_links(self, html_text: str, base_url: str) -> List[str]:
        """Extract and resolve relative URLs from href attributes."""
        links: List[str] = []
        # Match <a ... href="...">
        pattern = re.compile(r"""<a\s+(?:[^>]*?\s+)?href=(["'])(.*?)\1""", re.IGNORECASE)
        for match in pattern.finditer(html_text):
            raw_href = match.group(2).strip()
            if not raw_href or raw_href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            resolved = urllib.parse.urljoin(base_url, raw_href)
            canon = self.canonicalize_url(resolved)
            links.append(canon)
        return links

    def run(self) -> CrawlResult:
        """Execute the crawl job according to configuration."""
        result = CrawlResult(start_time=datetime.now(timezone.utc).isoformat())
        queue: Deque[Tuple[str, int]] = collections.deque()
        seen_content_hashes: Set[str] = set()

        # Initialize queue with seed URLs
        for seed in self.config.seed_urls:
            canon_seed = self.canonicalize_url(seed)
            if self._is_domain_allowed(canon_seed):
                queue.append((canon_seed, 0))
            else:
                result.failed_urls[canon_seed] = "Seed domain not allowed by configuration."

        while queue and result.pages_crawled < self.config.max_pages:
            current_url, depth = queue.popleft()

            if current_url in result.visited_urls:
                continue

            result.visited_urls.add(current_url)

            # Safety and politeness checks
            try:
                self._validate_url_safety(current_url)
            except SSRFValidationError as e:
                result.failed_urls[current_url] = f"SSRF Blocked: {e}"
                continue

            if not self._is_robots_allowed(current_url):
                result.failed_urls[current_url] = "Disallowed by robots.txt."
                continue

            # Fetch page
            try:
                status, content_bytes, final_url, headers = self._fetch_page(current_url)
                if status != 200:
                    result.failed_urls[current_url] = f"HTTP {status}"
                    continue

                content_type = headers.get("Content-Type", headers.get("content-type", ""))
                # Only process text/html or text/plain
                if content_type and not any(t in content_type.lower() for t in ("text/html", "text/plain", "xhtml")):
                    result.failed_urls[current_url] = f"Unsupported content-type: {content_type}"
                    continue

                html_text = content_bytes.decode("utf-8", errors="replace")
                clean_text = self.text_processor.clean_html(html_text)

                if not clean_text.strip():
                    result.failed_urls[current_url] = "Empty content"
                    continue

                # Title extraction
                title = current_url
                title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
                if title_match and title_match.group(1).strip():
                    title = title_match.group(1).strip()

                doc = Document.create(
                    document_id=f"crawl_{hash(final_url) & 0xffffffff:08x}",
                    title=title,
                    content=clean_text,
                    source_url=final_url,
                    description=f"Crawled from {current_url}",
                    language="en",
                )

                if doc.content_hash not in seen_content_hashes:
                    seen_content_hashes.add(doc.content_hash)
                    result.documents.append(doc)
                    result.pages_crawled += 1

                # Discovered links if depth limit allows
                if depth < self.config.max_depth:
                    links = self.extract_links(html_text, final_url)
                    for link in links:
                        if link not in result.visited_urls and self._is_domain_allowed(link):
                            queue.append((link, depth + 1))

            except Exception as e:
                result.failed_urls[current_url] = f"Fetch error: {e}"

            # Polite crawl delay (if real network requests)
            if self.config.delay_seconds > 0 and not self.http_fetcher:
                time.sleep(self.config.delay_seconds)

        result.end_time = datetime.now(timezone.utc).isoformat()
        return result
