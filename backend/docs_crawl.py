import hashlib
import heapq
import itertools
import os
import re
from collections import defaultdict
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlunparse

import requests

HREF_PATTERN = re.compile(r'href\s*=\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s>]+))', re.I)
TITLE_PATTERN = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
TAG_PATTERN = re.compile(r"<[^>]+>")
MAIN_PATTERN = re.compile(r"<main[^>]*>(.*?)</main>", re.I | re.S)
ARTICLE_PATTERN = re.compile(r"<article[^>]*>(.*?)</article>", re.I | re.S)
BODY_PATTERN = re.compile(r"<body[^>]*>(.*?)</body>", re.I | re.S)
BREADCRUMB_PATTERN = re.compile(r'<(?:nav|div)[^>]+(?:breadcrumb|breadcrumbs)[^>]*>(.*?)</(?:nav|div)>', re.I | re.S)
HEADING_PATTERN = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.I | re.S)
BLOCK_TAG_PATTERN = re.compile(r"</(p|div|section|article|main|li|ul|ol|h[1-6]|table|tr|td|pre|code|blockquote)>", re.I)
BREAK_PATTERN = re.compile(r"<br\s*/?>", re.I)
HEAD_LINK_PATTERN = re.compile(
    r"<link[^>]+rel\s*=\s*(?:\"([^\"]+)\"|'([^']+)')[^>]+href\s*=\s*(?:\"([^\"]+)\"|'([^']+)')",
    re.I,
)
NEXT_PREV_ANCHOR_PATTERN = re.compile(
    r"<a[^>]+class\s*=\s*(?:\"([^\"]*)\"|'([^']*)')[^>]+href\s*=\s*(?:\"([^\"]+)\"|'([^']+)')",
    re.I,
)
NOISE_BLOCK_PATTERNS = [
    re.compile(r"<(script|style|noscript).*?>.*?</\1>", re.I | re.S),
    re.compile(r"<nav[^>]*>.*?</nav>", re.I | re.S),
    re.compile(r"<aside[^>]*>.*?</aside>", re.I | re.S),
    re.compile(r"<footer[^>]*>.*?</footer>", re.I | re.S),
    re.compile(r"<header[^>]*>.*?</header>", re.I | re.S),
    re.compile(r'<div[^>]+class="[^"]*(?:sidebar|toc-drawer|navigation|related-pages|prev-next|search|toctree-wrapper)[^"]*"[^>]*>.*?</div>', re.I | re.S),
]
NON_DOC_SUFFIXES = {
    ".css",
    ".js",
    ".mjs",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".webm",
    ".mp3",
    ".ogg",
    ".pdf",
    ".zip",
    ".gz",
    ".tar",
    ".tgz",
    ".xz",
    ".bz2",
}
PRIORITY_RANK = {
    "entry": 0,
    "nav_tree": 1,
    "next_prev": 2,
    "content": 3,
    "generic": 4,
}


def crawl_docs_pages(*, project_id: str, docs_url: str, profile: dict, progress_callback=None, previous_pages: dict | None = None) -> dict:
    allowed_prefixes = profile.get("allowed_path_prefixes", ["/"])
    blocked_prefixes = profile.get("blocked_path_prefixes", [])
    max_depth = profile.get("max_depth", 2)
    max_pages = profile.get("max_pages", 40)
    max_pages_per_section = profile.get("max_pages_per_section")
    strip_fragments = profile.get("canonicalize_fragments", True)
    entry_urls = profile.get("entry_urls") or [docs_url]
    previous_pages = previous_pages or {}
    session = requests.Session()

    queue = []
    seen = set()
    queued = set()
    sequence = itertools.count()
    section_rounds: dict[str, int] = defaultdict(int)
    section_budget: dict[str, int] = defaultdict(int)
    records = []
    incomplete_reasons: list[str] = []

    def mark_incomplete(reason: str) -> None:
        if reason and reason not in incomplete_reasons:
            incomplete_reasons.append(reason)

    def enqueue(
        *,
        url: str,
        crawl_depth: int,
        priority_source: str,
        order_hint: int = 0,
        section_key: str = "",
        nav_title: str = "",
        nav_depth: int = 0,
        nav_order: int = 0,
        parent_section: str = "",
        is_index_page: bool | None = None,
    ) -> None:
        normalized = _canonicalize_url(url, strip_fragment=strip_fragments)
        if not normalized:
            return
        if not _is_allowed_crawl_target(
            candidate_url=normalized,
            docs_url=docs_url,
            allowed_prefixes=allowed_prefixes,
            blocked_prefixes=blocked_prefixes,
        ):
            return
        if normalized in seen or normalized in queued:
            return
        if max_pages_per_section and section_key and priority_source != "entry":
            if section_budget[section_key] >= max_pages_per_section:
                return
            section_budget[section_key] += 1

        queue_round = section_rounds[section_key] if section_key and priority_source != "entry" else 0
        if section_key and priority_source != "entry":
            section_rounds[section_key] += 1

        queue_item = {
            "url": normalized,
            "crawl_depth": crawl_depth,
            "priority_source": priority_source,
            "section_key": section_key,
            "order_hint": order_hint,
            "nav_title": nav_title,
            "nav_depth": nav_depth,
            "nav_order": nav_order,
            "parent_section": parent_section,
            "is_index_page": _is_index_like_path(urlparse(normalized).path)
            if is_index_page is None
            else is_index_page,
        }
        heapq.heappush(
            queue,
            (
                PRIORITY_RANK.get(priority_source, PRIORITY_RANK["generic"]),
                queue_round,
                order_hint,
                crawl_depth,
                next(sequence),
                queue_item,
            ),
        )
        queued.add(normalized)

    def enqueue_discovered_links(*, links: list[dict], crawl_depth: int) -> None:
        for candidate in links:
            if not isinstance(candidate, dict):
                continue
            enqueue(
                url=candidate.get("url", ""),
                crawl_depth=crawl_depth,
                priority_source=candidate.get("priority_source", "generic"),
                order_hint=candidate.get("order_hint", 0),
                section_key=candidate.get("section_key", ""),
                nav_title=candidate.get("nav_title", ""),
                nav_depth=candidate.get("nav_depth", 0),
                nav_order=candidate.get("nav_order", 0),
                parent_section=candidate.get("parent_section", ""),
                is_index_page=candidate.get("is_index_page"),
            )

    for index, url in enumerate(entry_urls):
        enqueue(url=url, crawl_depth=0, priority_source="entry", order_hint=index)

    while queue:
        if len(records) >= max_pages:
            mark_incomplete("max_pages_reached")
            break

        _priority, _queue_round, _order_hint, _depth, _seq, queue_item = heapq.heappop(queue)
        url = queue_item["url"]
        queued.discard(url)
        if url in seen:
            continue
        seen.add(url)

        previous_page = previous_pages.get(url)
        request_headers = {}
        was_modified = True
        if previous_page:
            if previous_page.get("etag"):
                request_headers["If-None-Match"] = previous_page["etag"]
            if previous_page.get("http_last_modified"):
                request_headers["If-Modified-Since"] = previous_page["http_last_modified"]

        try:
            if request_headers:
                response = session.get(url, timeout=30, headers=request_headers)
            else:
                response = requests.get(url, timeout=30)
            if getattr(response, "status_code", 200) == 304 and previous_page:
                was_modified = False
                html = None
                if queue_item["crawl_depth"] < max_depth:
                    cached_links = previous_page.get("discovered_links")
                    if isinstance(cached_links, list):
                        enqueue_discovered_links(
                            links=cached_links,
                            crawl_depth=queue_item["crawl_depth"] + 1,
                        )
                    else:
                        try:
                            refreshed = requests.get(url, timeout=30)
                            refreshed.raise_for_status()
                            response = refreshed
                            html = response.text
                        except requests.RequestException:
                            mark_incomplete(f"missing_cached_links:{url}")

                if html is None:
                    records.append(_build_record_from_cached_page(project_id=project_id, page=previous_page))
                    if progress_callback is not None:
                        progress_callback(
                            current_url=url,
                            processed_pages=len(records),
                            max_pages=max_pages,
                        )
                    continue

            response.raise_for_status()
            html = response.text
        except requests.RequestException:
            mark_incomplete(f"request_failed:{url}")
            continue

        extractor_hint = _detect_extractor_hint(html, profile=profile)
        primary_html = _extract_primary_html(html)
        body_text = _extract_primary_text(primary_html)
        headings = _extract_headings(primary_html)
        breadcrumbs = _extract_breadcrumbs(html)
        title = _extract_title(html)
        nav_title = queue_item.get("nav_title") or title or (headings[0] if headings else "")
        record_url = _canonicalize_url(url, strip_fragment=strip_fragments)

        candidates = []
        if queue_item["crawl_depth"] < max_depth:
            candidates = _extract_link_candidates(
                base_url=record_url,
                html=html,
                primary_html=primary_html,
                extractor_hint=extractor_hint,
                profile=profile,
            )

        records.append(
            {
                "project_id": project_id,
                "id": _page_id(record_url),
                "url": record_url,
                "title": title,
                "path": urlparse(record_url).path,
                "section": headings[0] if headings else (queue_item.get("parent_section") or breadcrumbs[-1] if breadcrumbs else ""),
                "body": body_text,
                "text_content": body_text,
                "headings": headings,
                "breadcrumbs": breadcrumbs,
                "content_hash": hashlib.sha256(body_text.encode("utf-8")).hexdigest(),
                "page_hash": hashlib.sha256(f"{title}||{body_text}||{'||'.join(headings)}".encode("utf-8")).hexdigest(),
                "last_seen_at": _normalize_http_timestamp(response.headers.get("Last-Modified"))
                or (previous_page.get("last_seen_at") if not was_modified and previous_page else None),
                "last_checked_at": _now_iso(),
                "source_type": "docs_page",
                "extractor_hint": extractor_hint,
                "nav_title": nav_title,
                "nav_depth": queue_item.get("nav_depth", 0),
                "nav_order": queue_item.get("nav_order", 0),
                "parent_section": queue_item.get("parent_section", ""),
                "section_key": queue_item.get("section_key", ""),
                "is_index_page": queue_item.get("is_index_page", _is_index_like_path(urlparse(record_url).path)),
                "etag": response.headers.get("ETag", "") or (previous_page.get("etag", "") if not was_modified and previous_page else ""),
                "http_last_modified": response.headers.get("Last-Modified", "")
                or (previous_page.get("http_last_modified", "") if not was_modified and previous_page else ""),
                "was_modified": was_modified,
                "discovered_links": _serialize_discovered_links(candidates),
            }
        )

        if progress_callback is not None:
            progress_callback(
                current_url=record_url,
                processed_pages=len(records),
                max_pages=max_pages,
            )

        if queue_item["crawl_depth"] >= max_depth:
            continue

        for candidate in candidates:
            enqueue(
                url=candidate["url"],
                crawl_depth=queue_item["crawl_depth"] + 1,
                priority_source=candidate["priority_source"],
                order_hint=candidate.get("order_hint", 0),
                section_key=candidate.get("section_key") or queue_item.get("section_key", ""),
                nav_title=candidate.get("nav_title", ""),
                nav_depth=candidate.get("nav_depth", 0),
                nav_order=candidate.get("nav_order", 0),
                parent_section=candidate.get("parent_section") or queue_item.get("parent_section", ""),
                is_index_page=candidate.get("is_index_page"),
            )

    return {
        "records": records,
        "crawl_complete": not incomplete_reasons,
        "incomplete_reasons": incomplete_reasons,
    }


def _extract_link_candidates(*, base_url: str, html: str, primary_html: str, extractor_hint: str, profile: dict) -> list[dict]:
    link_strategy = _resolve_link_strategy(profile=profile, extractor_hint=extractor_hint)
    strip_fragments = profile.get("canonicalize_fragments", True)
    candidates: list[dict] = []

    if link_strategy == "furo_nav_first":
        candidates.extend(_extract_nav_tree_links(base_url, html, strip_fragments=strip_fragments))
        if profile.get("follow_pagination", True):
            candidates.extend(_extract_related_page_links(base_url, html, strip_fragments=strip_fragments))
        candidates.extend(_extract_content_doc_links(base_url, primary_html, strip_fragments=strip_fragments))
    else:
        for index, link in enumerate(_extract_internal_links(base_url, html, strip_fragments=strip_fragments)):
            candidates.append(
                {
                    "url": link,
                    "priority_source": "generic",
                    "order_hint": index,
                }
            )

    deduped = []
    seen = set()
    for candidate in candidates:
        normalized = _canonicalize_url(candidate.get("url", ""), strip_fragment=strip_fragments)
        if not normalized or normalized in seen or normalized == _canonicalize_url(base_url, strip_fragment=strip_fragments):
            continue
        seen.add(normalized)
        deduped.append({**candidate, "url": normalized})
    return deduped


def _extract_internal_links(base_url: str, html: str, *, strip_fragments: bool = True) -> list[str]:
    base = urlparse(base_url)
    links = []
    seen = set()
    for match in HREF_PATTERN.findall(html):
        href = next((value for value in match if value), "")
        normalized = _normalize_href_to_url(base_url, href, strip_fragments=strip_fragments)
        if not normalized:
            continue
        parsed = urlparse(normalized)
        if parsed.netloc != base.netloc or not _looks_like_doc_page(parsed.path):
            continue
        if normalized == _canonicalize_url(base_url, strip_fragment=strip_fragments):
            continue
        if normalized not in seen:
            seen.add(normalized)
            links.append(normalized)
    return sorted(links, key=lambda link: (urlparse(link).path.count("/"), link))


def _extract_nav_tree_links(base_url: str, html: str, *, strip_fragments: bool = True) -> list[dict]:
    parser = _NavigationLinkParser()
    parser.feed(html)
    return parser.links_for_queue(base_url, strip_fragments=strip_fragments)


def _extract_related_page_links(base_url: str, html: str, *, strip_fragments: bool = True) -> list[dict]:
    candidates = []
    order = 0

    for rel_match in HEAD_LINK_PATTERN.findall(html):
        rel_value = next((value for value in rel_match[:2] if value), "")
        href = next((value for value in rel_match[2:] if value), "")
        rel_tokens = {token.strip().lower() for token in rel_value.split()}
        if "next" not in rel_tokens and "prev" not in rel_tokens:
            continue
        normalized = _normalize_href_to_url(base_url, href, strip_fragments=strip_fragments)
        if not normalized:
            continue
        candidates.append(
            {
                "url": normalized,
                "priority_source": "next_prev",
                "order_hint": order,
                "section_key": "",
            }
        )
        order += 1

    for anchor_match in NEXT_PREV_ANCHOR_PATTERN.findall(html):
        classes = next((value for value in anchor_match[:2] if value), "")
        href = next((value for value in anchor_match[2:] if value), "")
        class_tokens = {token.strip() for token in classes.split()}
        if "next-page" not in class_tokens and "prev-page" not in class_tokens:
            continue
        normalized = _normalize_href_to_url(base_url, href, strip_fragments=strip_fragments)
        if not normalized:
            continue
        candidates.append(
            {
                "url": normalized,
                "priority_source": "next_prev",
                "order_hint": order,
                "section_key": "",
            }
        )
        order += 1

    return candidates


def _extract_content_doc_links(base_url: str, primary_html: str, *, strip_fragments: bool = True) -> list[dict]:
    candidates = []
    seen = set()
    for index, match in enumerate(HREF_PATTERN.findall(primary_html)):
        href = next((value for value in match if value), "")
        normalized = _normalize_href_to_url(base_url, href, strip_fragments=strip_fragments)
        if not normalized or normalized in seen or normalized == _canonicalize_url(base_url, strip_fragment=strip_fragments):
            continue
        seen.add(normalized)
        candidates.append(
            {
                "url": normalized,
                "priority_source": "content",
                "order_hint": index,
            }
        )
    return candidates


def _resolve_link_strategy(*, profile: dict, extractor_hint: str) -> str:
    explicit = (profile.get("link_strategy") or "").strip().lower()
    if explicit and explicit != "auto":
        return explicit
    if extractor_hint in {"furo", "sphinx-html"}:
        return "furo_nav_first"
    return "generic"


def _normalize_href_to_url(base_url: str, href: str, *, strip_fragments: bool = True) -> str:
    href = (href or "").strip()
    if not href or href.startswith("#"):
        return ""
    lowered = href.lower()
    if lowered.startswith(("javascript:", "mailto:", "tel:", "data:")):
        return ""
    return _canonicalize_url(_resolve_relative_url(base_url, href), strip_fragment=strip_fragments)


def _canonicalize_url(url: str, *, strip_fragment: bool = True) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return ""

    path = parsed.path or "/"
    if path.endswith("/index.html"):
        path = path[: -len("/index.html")] or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    if not path:
        path = "/"

    fragment = "" if strip_fragment else parsed.fragment
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", fragment))


def _resolve_relative_url(base_url: str, href: str) -> str:
    parsed = urlparse(base_url)
    if href.startswith(("http://", "https://", "/")):
        return urljoin(base_url, href)

    base_path = parsed.path or "/"
    if not base_path.endswith("/") and not os.path.splitext(base_path)[1]:
        base_path = f"{base_path}/"
        base_url = urlunparse((parsed.scheme, parsed.netloc, base_path, "", "", ""))
    return urljoin(base_url, href)


def _is_allowed_crawl_target(*, candidate_url: str, docs_url: str, allowed_prefixes: list[str], blocked_prefixes: list[str]) -> bool:
    candidate = urlparse(candidate_url)
    docs_root = urlparse(docs_url)
    if candidate.netloc != docs_root.netloc:
        return False
    if not _looks_like_doc_page(candidate.path):
        return False
    if any(candidate.path.startswith(prefix) for prefix in blocked_prefixes):
        return False
    return any(candidate.path.startswith(prefix) for prefix in allowed_prefixes)


def _looks_like_doc_page(path: str) -> bool:
    lower_path = (path or "").lower()
    if lower_path.endswith("/_print"):
        return False
    _, extension = os.path.splitext(lower_path)
    if extension and extension not in {".html", ".htm"} and extension in NON_DOC_SUFFIXES:
        return False
    return True


def _extract_title(html: str) -> str:
    match = TITLE_PATTERN.search(html)
    if match:
        return _html_to_text(match.group(1))
    return ""


def _html_to_text(html: str, *, preserve_blocks: bool = False) -> str:
    cleaned = re.sub(r"<(script|style).*?>.*?</\1>", " ", html, flags=re.S | re.I)
    if preserve_blocks:
        cleaned = BREAK_PATTERN.sub("\n", cleaned)
        cleaned = BLOCK_TAG_PATTERN.sub("\n", cleaned)
    cleaned = TAG_PATTERN.sub(" ", cleaned)
    cleaned = unescape(cleaned)
    cleaned = cleaned.replace("Â¶", " ").replace("¶", " ")
    if preserve_blocks:
        cleaned = cleaned.replace("\r", "")
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r" *\n *", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _extract_primary_text(html: str) -> str:
    return _html_to_text(_strip_noise_blocks(html), preserve_blocks=True)


def _extract_primary_html(html: str) -> str:
    for pattern in (MAIN_PATTERN, ARTICLE_PATTERN):
        match = pattern.search(html)
        if match:
            return match.group(1)
    match = BODY_PATTERN.search(html)
    if match:
        return match.group(1)
    return html


def _extract_breadcrumbs(html: str) -> list[str]:
    match = BREADCRUMB_PATTERN.search(html)
    if not match:
        return []
    items = [item for item in _html_to_text(match.group(1), preserve_blocks=True).splitlines() if item.strip()]
    deduped = []
    seen = set()
    for item in items:
        cleaned = item.strip()
        if cleaned not in seen:
            seen.add(cleaned)
            deduped.append(cleaned)
    return deduped[:8]


def _extract_headings(html: str) -> list[str]:
    headings = []
    seen = set()
    for _level, value in HEADING_PATTERN.findall(html or ""):
        cleaned = _html_to_text(value)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            headings.append(cleaned)
    return headings[:12]


def _strip_noise_blocks(html: str) -> str:
    cleaned = html or ""
    for pattern in NOISE_BLOCK_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)
    return cleaned


def _detect_extractor_hint(html: str, *, profile: dict) -> str:
    explicit = (profile.get("doc_system") or "").strip().lower()
    if explicit and explicit != "auto":
        return explicit

    lowered = (html or "").lower()
    if any(token in lowered for token in ("furo", "pydata-sphinx-theme", "sidebar-drawer", "toc-drawer")):
        return "furo"
    if any(token in lowered for token in ("sphinx", "genindex", "_sources", "search.html")):
        return "sphinx-html"
    return "html-main"


def _page_id(url: str) -> str:
    return hashlib.sha1((url or "").encode("utf-8")).hexdigest()[:16]


def _normalize_http_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(UTC).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, IndexError):
        return value


def _build_record_from_cached_page(*, project_id: str, page: dict) -> dict:
    return {
        "project_id": project_id,
        "id": page.get("id") or _page_id(page.get("url", "")),
        "url": page.get("url", ""),
        "title": page.get("title", ""),
        "path": page.get("path", ""),
        "section": page.get("section", ""),
        "body": page.get("text_content", ""),
        "text_content": page.get("text_content", ""),
        "headings": page.get("headings", []),
        "breadcrumbs": page.get("breadcrumbs", []),
        "content_hash": page.get("content_hash", ""),
        "page_hash": page.get("page_hash", ""),
        "last_seen_at": page.get("last_seen_at"),
        "last_checked_at": _now_iso(),
        "source_type": "docs_page",
        "extractor_hint": page.get("extractor_hint", "html-main"),
        "nav_title": page.get("nav_title", ""),
        "nav_depth": page.get("nav_depth", 0),
        "nav_order": page.get("nav_order", 0),
        "parent_section": page.get("parent_section", ""),
        "section_key": page.get("section_key", ""),
        "is_index_page": page.get("is_index_page", False),
        "etag": page.get("etag", ""),
        "http_last_modified": page.get("http_last_modified", ""),
        "was_modified": False,
        "discovered_links": _serialize_discovered_links(page.get("discovered_links") or []),
    }


def _serialize_discovered_links(candidates: list[dict]) -> list[dict]:
    serialized = []
    for candidate in candidates or []:
        if not isinstance(candidate, dict) or not candidate.get("url"):
            continue
        serialized.append(
            {
                "url": candidate["url"],
                "priority_source": candidate.get("priority_source", "generic"),
                "order_hint": candidate.get("order_hint", 0),
                "section_key": candidate.get("section_key", ""),
                "nav_title": candidate.get("nav_title", ""),
                "nav_depth": candidate.get("nav_depth", 0),
                "nav_order": candidate.get("nav_order", 0),
                "parent_section": candidate.get("parent_section", ""),
                "is_index_page": candidate.get("is_index_page"),
            }
        )
    return serialized


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_index_like_path(path: str) -> bool:
    path = path or "/"
    normalized = path.rstrip("/")
    basename = normalized.rsplit("/", 1)[-1] if normalized else ""
    if path == "/":
        return True
    return basename in {"", "index", "index.html"}


class _NavigationLinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tag_stack: list[str] = []
        self.sidebar_region_depth: int | None = None
        self.toctree_region_depth: int | None = None
        self.nav_ul_depth = 0
        self.current_anchor: dict | None = None
        self.raw_links: list[dict] = []
        self.order = 0

    def handle_starttag(self, tag: str, attrs):
        attributes = {key: value or "" for key, value in attrs}
        self.tag_stack.append(tag)
        classes = set(attributes.get("class", "").split())
        if self.sidebar_region_depth is None and tag == "div" and "sidebar-tree" in classes:
            self.sidebar_region_depth = len(self.tag_stack)
        if self.toctree_region_depth is None and tag == "div" and "toctree-wrapper" in classes:
            self.toctree_region_depth = len(self.tag_stack)

        if self._in_navigation_region() and tag == "ul":
            self.nav_ul_depth += 1

        if self._in_navigation_region() and tag == "a":
            self.current_anchor = {
                "href": attributes.get("href", ""),
                "text_parts": [],
                "nav_depth": max(0, self.nav_ul_depth - 1),
                "nav_order": self.order,
            }

    def handle_data(self, data: str):
        if self.current_anchor is not None and data:
            self.current_anchor["text_parts"].append(data)

    def handle_endtag(self, tag: str):
        if tag == "a" and self.current_anchor is not None:
            title = re.sub(r"\s+", " ", "".join(self.current_anchor["text_parts"])).strip()
            if self.current_anchor.get("href") and title:
                self.raw_links.append(
                    {
                        "url": self.current_anchor["href"],
                        "nav_title": title,
                        "nav_depth": self.current_anchor["nav_depth"],
                        "nav_order": self.current_anchor["nav_order"],
                    }
                )
                self.order += 1
            self.current_anchor = None

        if self._in_navigation_region() and tag == "ul":
            self.nav_ul_depth = max(0, self.nav_ul_depth - 1)

        if self.tag_stack:
            current_depth = len(self.tag_stack)
            if self.sidebar_region_depth == current_depth:
                self.sidebar_region_depth = None
                self.nav_ul_depth = 0
            if self.toctree_region_depth == current_depth:
                self.toctree_region_depth = None
                self.nav_ul_depth = 0
            self.tag_stack.pop()

    def links_for_queue(self, base_url: str, *, strip_fragments: bool = True) -> list[dict]:
        if not self.raw_links:
            return []

        links = []
        title_stack: dict[int, str] = {}
        for link in self.raw_links:
            depth = link["nav_depth"]
            parent_section = title_stack.get(depth - 1, "") if depth > 0 else ""
            section_key = title_stack.get(0, "") if depth > 0 else link["nav_title"]
            title_stack[depth] = link["nav_title"]
            for child_depth in [value for value in title_stack if value > depth]:
                title_stack.pop(child_depth, None)
            links.append(
                {
                    "url": _normalize_href_to_url(base_url, link["url"], strip_fragments=strip_fragments),
                    "priority_source": "nav_tree",
                    "order_hint": link["nav_order"],
                    "nav_title": link["nav_title"],
                    "nav_depth": depth,
                    "nav_order": link["nav_order"],
                    "parent_section": parent_section,
                    "section_key": section_key,
                    "is_index_page": _is_index_like_path(
                        urlparse(_normalize_href_to_url(base_url, link["url"], strip_fragments=strip_fragments)).path
                    )
                    if _normalize_href_to_url(base_url, link["url"], strip_fragments=strip_fragments)
                    else None,
                }
            )
        return links

    def _in_navigation_region(self) -> bool:
        return self.sidebar_region_depth is not None or self.toctree_region_depth is not None
