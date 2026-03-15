import json
import re
from urllib.parse import urljoin, urlparse

import requests


DEFAULT_CATEGORY_HINTS = ["网络", "存储", "调度", "架构", "安全", "升级", "运行时", "可观测性"]


def build_discovery_prompt(*, project: dict, homepage_excerpt: str) -> str:
    return f"""You are a documentation discovery agent.

Generate a crawl profile for the following project docs homepage.

Return JSON only with these fields:
- entry_urls
- allowed_path_prefixes
- blocked_path_prefixes
- max_depth
- max_pages
- max_pages_per_section
- expand_mode
- doc_system
- initial_read_enabled
- diff_mode
- link_strategy
- canonicalize_fragments
- follow_pagination
- category_hints
- discovery_prompt
- classification_prompt

Project: {project.get("name")}
Docs URL: {project.get("docs_url")}
Homepage excerpt:
{homepage_excerpt[:2500]}
"""


def parse_discovery_response(text: str) -> dict:
    parsed = json.loads(text)
    return {
        "entry_urls": parsed["entry_urls"],
        "allowed_path_prefixes": parsed["allowed_path_prefixes"],
        "blocked_path_prefixes": parsed["blocked_path_prefixes"],
        "max_depth": parsed["max_depth"],
        "max_pages": parsed["max_pages"],
        "max_pages_per_section": parsed.get("max_pages_per_section", 0),
        "expand_mode": parsed["expand_mode"],
        "doc_system": parsed.get("doc_system", "auto"),
        "initial_read_enabled": parsed.get("initial_read_enabled", True),
        "diff_mode": parsed.get("diff_mode", "page"),
        "link_strategy": parsed.get("link_strategy", "auto"),
        "canonicalize_fragments": parsed.get("canonicalize_fragments", True),
        "follow_pagination": parsed.get("follow_pagination", True),
        "category_hints": parsed["category_hints"],
        "discovery_prompt": parsed["discovery_prompt"],
        "classification_prompt": parsed["classification_prompt"],
    }


def build_profile_from_homepage(*, docs_url: str, homepage_excerpt: str) -> dict:
    parsed = urlparse(docs_url)
    path = parsed.path.rstrip("/") or "/"
    prefix = path
    if path.endswith("/home"):
        prefix = path[: -len("/home")] or "/"
    lowered_excerpt = (homepage_excerpt or "").lower()
    is_furo = any(token in lowered_excerpt for token in ("furo", "sphinx", "pydata-sphinx-theme"))
    blocked = [f"{prefix}/_print"] if prefix != "/" else ["/_print"]
    for suffix in ("/_sources", "/_static", "/genindex", "/search", "/search.html", "/objects.inv"):
        candidate = f"{prefix}{suffix}" if prefix != "/" else suffix
        if candidate not in blocked:
            blocked.append(candidate)
    hints = [hint for hint in DEFAULT_CATEGORY_HINTS if hint in homepage_excerpt]
    entry_urls = _build_furo_entry_urls(docs_url, homepage_excerpt) if is_furo else [docs_url]
    return {
        "entry_urls": entry_urls,
        "allowed_path_prefixes": [prefix],
        "blocked_path_prefixes": blocked,
        "max_depth": 2 if is_furo else 3,
        "max_pages": 80 if is_furo else 40,
        "max_pages_per_section": 12 if is_furo else 0,
        "expand_mode": "auto",
        "doc_system": "furo" if is_furo else "auto",
        "initial_read_enabled": True,
        "diff_mode": "page",
        "link_strategy": "furo_nav_first" if is_furo else "auto",
        "canonicalize_fragments": True,
        "follow_pagination": True,
        "category_hints": hints or DEFAULT_CATEGORY_HINTS[:4],
        "discovery_prompt": "",
        "classification_prompt": "",
    }


def generate_crawl_profile(project: dict) -> dict:
    docs_url = project.get("docs_url", "")
    if not docs_url:
        return build_profile_from_homepage(docs_url="", homepage_excerpt="")

    response = requests.get(docs_url, timeout=30)
    response.raise_for_status()
    excerpt = response.text[:12000]
    return build_profile_from_homepage(docs_url=docs_url, homepage_excerpt=excerpt)


def _build_furo_entry_urls(docs_url: str, homepage_excerpt: str) -> list[str]:
    entries = [docs_url]
    seen = {docs_url.rstrip("/")}

    next_match = re.search(r'<link[^>]+rel="next"[^>]+href="([^"]+)"', homepage_excerpt, re.I)
    if next_match:
        candidate = _join_docs_url(docs_url, next_match.group(1))
        if candidate and candidate.rstrip("/") not in seen:
            seen.add(candidate.rstrip("/"))
            entries.append(candidate)

    for href in re.findall(r'<a[^>]+class="[^"]*reference internal[^"]*"[^>]+href="([^"]+)"', homepage_excerpt, re.I):
        candidate = _join_docs_url(docs_url, href)
        if not candidate or candidate.rstrip("/") in seen:
            continue
        seen.add(candidate.rstrip("/"))
        entries.append(candidate)
        if len(entries) >= 8:
            break

    return entries


def _join_docs_url(base_url: str, href: str) -> str:
    if not href or href.startswith("#"):
        return ""
    return urljoin(base_url, href)
