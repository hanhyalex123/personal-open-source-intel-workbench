import hashlib
import re
from collections import deque
from html import unescape
from urllib.parse import urljoin, urlparse

import requests

HREF_PATTERN = re.compile(r'href\s*=\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s>]+))', re.I)
TITLE_PATTERN = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
TAG_PATTERN = re.compile(r"<[^>]+>")
MAIN_PATTERN = re.compile(r"<main[^>]*>(.*?)</main>", re.I | re.S)
ARTICLE_PATTERN = re.compile(r"<article[^>]*>(.*?)</article>", re.I | re.S)


def crawl_docs_pages(*, project_id: str, docs_url: str, profile: dict) -> list[dict]:
    allowed_prefixes = profile.get("allowed_path_prefixes", ["/"])
    blocked_prefixes = profile.get("blocked_path_prefixes", [])
    max_depth = profile.get("max_depth", 2)
    max_pages = profile.get("max_pages", 40)
    entry_urls = profile.get("entry_urls") or [docs_url]

    queue = deque((url, 0) for url in entry_urls)
    seen = set()
    records = []

    while queue:
        if len(records) >= max_pages:
            break
        url, depth = queue.popleft()
        if url in seen:
            continue
        seen.add(url)

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        html = response.text

        records.append(
            {
                "project_id": project_id,
                "url": url,
                "title": _extract_title(html),
                "path": urlparse(url).path,
                "section": "",
                "body": _extract_primary_text(html),
                "content_hash": hashlib.sha256(_extract_primary_text(html).encode("utf-8")).hexdigest(),
                "last_seen_at": response.headers.get("Last-Modified"),
                "source_type": "docs_page",
                "extractor_hint": "html-main",
            }
        )

        if depth >= max_depth:
            continue

        for next_url in _extract_internal_links(url, html):
            parsed = urlparse(next_url)
            if any(parsed.path.startswith(prefix) for prefix in blocked_prefixes):
                continue
            if not any(parsed.path.startswith(prefix) for prefix in allowed_prefixes):
                continue
            if next_url not in seen:
                queue.append((next_url, depth + 1))

    return records


def _extract_internal_links(base_url: str, html: str) -> list[str]:
    base = urlparse(base_url)
    links = []
    seen = set()
    for match in HREF_PATTERN.findall(html):
        href = next((value for value in match if value), "")
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme in {"http", "https"} and parsed.netloc == base.netloc:
            if parsed.path.endswith("/_print"):
                continue
            normalized = absolute.rstrip("/")
            if normalized not in seen:
                seen.add(normalized)
                links.append(normalized)
    return sorted(links, key=lambda link: (urlparse(link).path.count("/"), link))


def _extract_title(html: str) -> str:
    match = TITLE_PATTERN.search(html)
    if match:
        return _html_to_text(match.group(1))
    return ""


def _html_to_text(html: str) -> str:
    cleaned = re.sub(r"<(script|style).*?>.*?</\1>", " ", html, flags=re.S | re.I)
    cleaned = TAG_PATTERN.sub(" ", cleaned)
    cleaned = unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _extract_primary_text(html: str) -> str:
    for pattern in (MAIN_PATTERN, ARTICLE_PATTERN):
        match = pattern.search(html)
        if match:
            return _html_to_text(match.group(1))
    return _html_to_text(html)
