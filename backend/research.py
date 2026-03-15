import re
from urllib.parse import urlparse

import requests

from .docs_crawl import _extract_primary_text, _extract_title
from .docs_diff import summarize_text

RAW_GITHUB_HOST = "raw.githubusercontent.com"
GITHUB_HOST = "github.com"
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
URL_PATTERN = re.compile(r"https?://[^\s)]+")
TOP_LEVEL_HEADING_PATTERN = re.compile(r"(?m)^#\s+")
SUBSECTION_PATTERN = re.compile(r"(?ms)^###\s+(.+?)\n(.*?)(?=^###\s+|^##\s+|^#\s+|\Z)")


def build_release_research_bundle(repo: str, release: dict) -> dict:
    version = release.get("tag_name") or release.get("name") or "unknown"
    body = release.get("body", "")
    changelog_url = _pick_changelog_url(repo, body, version)
    version_section = ""
    sections = []

    if changelog_url:
        try:
            changelog_text = requests.get(changelog_url, timeout=30).text
            version_section = _extract_version_section(changelog_text, version)
            version_section = _focus_version_section(version_section)
            sections = _extract_subsections(version_section)
        except Exception:
            changelog_url = ""

    doc_urls = _extract_doc_urls(body, version_section)
    doc_refs = []
    for url in doc_urls[:3]:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            doc_refs.append(
                {
                    "title": _extract_title(response.text) or url,
                    "url": url,
                    "snippet": _clip_text(_extract_primary_text(response.text), 900),
                }
            )
        except Exception:
            continue

    return {
        "release": {
            "repo": repo,
            "version": version,
            "url": release.get("html_url", ""),
            "published_at": release.get("published_at"),
            "body_excerpt": _clip_text(body, 2400),
        },
        "changelog": {
            "url": changelog_url,
            "version_section": _clip_text(version_section, 8000),
            "sections": sections[:8],
        },
        "doc_refs": doc_refs,
        "code_refs": [],
        "config_refs": [],
    }


def build_docs_group_research_bundle(*, category: str, items: list[dict]) -> dict:
    ordered_items = _sort_docs_pages(items)
    selected_items = _select_summary_pages(ordered_items, limit=8)
    pages = [
        {
            "page_id": item.get("id"),
            "title": item.get("title") or item.get("url"),
            "url": item.get("url", ""),
            "snippet": _clip_text(item.get("body", ""), 320),
            "last_seen_at": item.get("last_seen_at"),
            "headings": item.get("headings", [])[:6],
            "breadcrumbs": item.get("breadcrumbs", [])[:6],
            "extractor_hint": item.get("extractor_hint", "html-main"),
            "nav_depth": item.get("nav_depth", 0),
            "parent_section": item.get("parent_section", ""),
        }
        for item in selected_items[:6]
    ]
    return {
        "category": category,
        "page_count": len(items),
        "section_stats": _build_section_stats(items),
        "pages": pages,
    }


def build_docs_initial_research_bundle(*, category: str, items: list[dict], current_snapshot: dict) -> dict:
    base = build_docs_group_research_bundle(category=category, items=items)
    selected_items = _select_summary_pages(_sort_docs_pages(items), limit=10)
    return {
        **base,
        "analysis_mode": "initial_read",
        "snapshot_before": None,
        "snapshot_after": {
            "page_count": len(items),
            "section_stats": _build_section_stats(items),
            "pages": [
                {
                    "page_id": item.get("id"),
                    "title": item.get("title") or item.get("url"),
                    "url": item.get("url", ""),
                    "section": item.get("section", ""),
                    "parent_section": item.get("parent_section", ""),
                    "nav_depth": item.get("nav_depth", 0),
                    "summary": summarize_text(item.get("text_content") or item.get("body", ""), limit=180),
                }
                for item in selected_items[:8]
            ],
        },
        "changed_pages": [
            {
                "page_id": item.get("id"),
                "url": item.get("url", ""),
                "path": item.get("path", ""),
                "title_after": item.get("title") or item.get("url"),
                "change_type": "added",
                "parent_section": item.get("parent_section", ""),
                "nav_depth": item.get("nav_depth", 0),
                "after_summary": summarize_text(item.get("text_content") or item.get("body", ""), limit=180),
                "headings_after": item.get("headings", [])[:8],
            }
            for item in selected_items[:8]
        ],
        "diff_summary": {
            "changed_pages": len(items),
            "added_pages": len(items),
            "removed_pages": 0,
            "unchanged_page_count": max(len(current_snapshot.get("pages", {})) - len(items), 0),
        },
    }


def build_docs_diff_research_bundle(*, category: str, changed_pages: list[dict], current_pages: list[dict], previous_pages: list[dict]) -> dict:
    sorted_current = _sort_docs_pages(current_pages)
    sorted_previous = _sort_docs_pages(previous_pages)
    selected_current = _select_summary_pages(sorted_current, limit=8)
    selected_previous = _select_summary_pages(sorted_previous, limit=6)
    return {
        "category": category,
        "analysis_mode": "diff_update",
        "page_count": len(current_pages),
        "section_stats": _build_section_stats(current_pages),
        "pages": [
            {
                "page_id": page.get("id"),
                "title": page.get("title") or page.get("url"),
                "url": page.get("url", ""),
                "snippet": summarize_text(page.get("text_content") or page.get("summary", ""), limit=220),
                "last_seen_at": page.get("last_seen_at"),
                "headings": page.get("headings", [])[:6],
                "extractor_hint": page.get("extractor_hint", "html-main"),
                "nav_depth": page.get("nav_depth", 0),
                "parent_section": page.get("parent_section", ""),
            }
            for page in selected_current[:6]
        ],
        "snapshot_before": {
            "page_count": len(previous_pages),
            "pages": [
                {
                    "page_id": page.get("id"),
                    "title": page.get("title") or page.get("url"),
                    "url": page.get("url", ""),
                    "summary": page.get("summary") or summarize_text(page.get("text_content", ""), limit=180),
                    "parent_section": page.get("parent_section", ""),
                    "nav_depth": page.get("nav_depth", 0),
                }
                for page in selected_previous[:4]
            ],
        },
        "snapshot_after": {
            "page_count": len(current_pages),
            "pages": [
                {
                    "page_id": page.get("id"),
                    "title": page.get("title") or page.get("url"),
                    "url": page.get("url", ""),
                    "summary": page.get("summary") or summarize_text(page.get("text_content", ""), limit=180),
                    "parent_section": page.get("parent_section", ""),
                    "nav_depth": page.get("nav_depth", 0),
                }
                for page in selected_current[:4]
            ],
        },
        "changed_pages": changed_pages[:5],
        "diff_summary": {
            "changed_pages": len(changed_pages),
            "added_pages": sum(1 for page in changed_pages if page.get("change_type") == "added"),
            "removed_pages": sum(1 for page in changed_pages if page.get("change_type") == "removed"),
            "unchanged_page_count": max(len(current_pages) - len(changed_pages), 0),
        },
    }


def enrich_event_for_analysis(event: dict) -> dict:
    if event.get("source") == "github_release" and not event.get("research_bundle"):
        return {
            **event,
            "research_bundle": build_release_research_bundle(
                event.get("repo", ""),
                {
                    "tag_name": event.get("version"),
                    "name": event.get("title"),
                    "body": event.get("body", ""),
                    "html_url": event.get("url", ""),
                    "published_at": event.get("published_at"),
                },
            ),
        }
    return event


def _pick_changelog_url(repo: str, body: str, version: str) -> str:
    for url in _extract_urls(body):
        if "CHANGELOG" in url.upper():
            return _to_raw_github_url(url)
    version_match = re.search(r"v?(\d+)\.(\d+)", version)
    if not version_match:
        return ""
    major, minor = version_match.groups()
    return f"https://raw.githubusercontent.com/{repo}/master/CHANGELOG/CHANGELOG-{major}.{minor}.md"


def _extract_version_section(markdown: str, version: str) -> str:
    heading = f"# {version}"
    start = markdown.find(heading)
    if start == -1 and version.startswith("v"):
        start = markdown.find(f"# {version[1:]}")
    if start == -1:
        return ""

    rest = markdown[start:]
    match = TOP_LEVEL_HEADING_PATTERN.search(rest[len(heading):])
    if not match:
        return rest.strip()
    end = len(heading) + match.start()
    return rest[:end].strip()


def _extract_subsections(markdown: str) -> list[dict]:
    sections = []
    for title, content in SUBSECTION_PATTERN.findall(markdown or ""):
        cleaned_content = _clip_text(_normalize_markdown_whitespace(content), 1800)
        if not cleaned_content:
            continue
        sections.append({"title": title.strip(), "content": cleaned_content})
    return sections


def _extract_doc_urls(*parts: str) -> list[str]:
    urls = []
    seen = set()
    for part in parts:
        for url in _extract_urls(part):
            parsed = urlparse(url)
            if not _is_candidate_doc_url(parsed):
                continue
            normalized = url.rstrip(").,")
            if normalized not in seen:
                seen.add(normalized)
                urls.append(normalized)
    return urls


def _extract_urls(text: str) -> list[str]:
    urls = [url for _label, url in MARKDOWN_LINK_PATTERN.findall(text or "")]
    urls.extend(URL_PATTERN.findall(text or ""))
    deduped = []
    seen = set()
    for url in urls:
        normalized = url.rstrip(").,")
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def _to_raw_github_url(url: str) -> str:
    if RAW_GITHUB_HOST in url:
        return url
    parsed = urlparse(url)
    if parsed.netloc != GITHUB_HOST:
        return url
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 5 and parts[2] == "blob":
        owner, repo, _blob, branch = parts[:4]
        file_path = "/".join(parts[4:])
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
    return url


def _focus_version_section(markdown: str) -> str:
    if not markdown:
        return ""

    first_line = markdown.splitlines()[0].strip()
    interesting_headings = ["## Urgent Upgrade Notes", "## Changes by Kind", "## Dependencies", "## Deprecation", "## API Change"]
    focused_sections = []
    for heading in interesting_headings:
        section = _extract_heading_block(markdown, heading)
        if section:
            focused_sections.append(section)

    if focused_sections:
        prefix = f"{first_line}\n\n" if first_line.startswith("# ") else ""
        return prefix + "\n\n".join(focused_sections)
    return markdown


def _extract_heading_block(markdown: str, heading: str) -> str:
    start = markdown.find(heading)
    if start == -1:
        return ""
    rest = markdown[start:]
    next_match = re.search(r"(?m)^##\s+", rest[len(heading):])
    if not next_match:
        return rest.strip()
    end = len(heading) + next_match.start()
    return rest[:end].strip()


def _normalize_markdown_whitespace(text: str) -> str:
    compact = re.sub(r"\n{3,}", "\n\n", text or "")
    compact = re.sub(r"[ \t]+", " ", compact)
    return compact.strip()


def _clip_text(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def _is_candidate_doc_url(parsed_url) -> bool:
    if parsed_url.netloc in {GITHUB_HOST, RAW_GITHUB_HOST, "groups.google.com", "dl.k8s.io"}:
        return False
    lowered_path = parsed_url.path.lower()
    if lowered_path.endswith((".tar.gz", ".tgz", ".zip", ".gz", ".xz", ".bz2", ".sha256", ".sha512", ".exe")):
        return False
    return parsed_url.scheme in {"http", "https"}


def _sort_docs_pages(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda item: (
            item.get("nav_depth", 99),
            0 if item.get("is_index_page") else 1,
            item.get("nav_order", 999999),
            item.get("title") or item.get("url") or "",
        ),
    )


def _select_summary_pages(items: list[dict], *, limit: int) -> list[dict]:
    if len(items) <= limit:
        return items

    selected = []
    selected_ids = set()
    section_counts = {}

    for item in items:
        section_key = item.get("section_key") or item.get("parent_section") or item.get("section") or item.get("title") or ""
        if item.get("is_index_page") and section_key and section_key not in section_counts:
            selected.append(item)
            selected_ids.add(item.get("id"))
            section_counts[section_key] = 1
            if len(selected) >= limit:
                return selected

    for item in items:
        if item.get("id") in selected_ids:
            continue
        section_key = item.get("section_key") or item.get("parent_section") or item.get("section") or ""
        if section_key and section_counts.get(section_key, 0) >= 2:
            continue
        selected.append(item)
        selected_ids.add(item.get("id"))
        if section_key:
            section_counts[section_key] = section_counts.get(section_key, 0) + 1
        if len(selected) >= limit:
            return selected

    return selected[:limit]


def _build_section_stats(items: list[dict]) -> list[dict]:
    grouped = {}
    for item in items:
        key = item.get("section_key") or item.get("parent_section") or item.get("section") or item.get("title") or "未分类"
        bucket = grouped.setdefault(key, {"section": key, "page_count": 0, "sample_titles": []})
        bucket["page_count"] += 1
        title = item.get("title") or item.get("url")
        if title and title not in bucket["sample_titles"] and len(bucket["sample_titles"]) < 3:
            bucket["sample_titles"].append(title)
    return sorted(grouped.values(), key=lambda item: (-item["page_count"], item["section"]))[:10]
