import hashlib
import os
import re
from collections import defaultdict
from datetime import UTC, datetime
from html import unescape

import feedparser
import requests

from .docs_crawl import crawl_docs_pages
from .docs_classify import group_docs_records
from .docs_diff import build_docs_snapshot, build_page_changes, diff_signature
from .research import (
    build_docs_diff_research_bundle,
    build_docs_group_research_bundle,
    build_docs_initial_research_bundle,
)

DEFAULT_REPOS = [
    "openclaw/openclaw",
]

DEFAULT_FEEDS = [
    {
        "id": "k8s-zh-docs-home",
        "name": "Kubernetes 中文文档首页",
        "url": "https://kubernetes.io/zh-cn/docs/home/",
        "type": "page",
    },
]

GITHUB_BLOB_LINK_PATTERN = re.compile(r"https://github\.com/([^/]+/[^/]+)/blob/([^)\s]+)")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


class FetchedFeedPayloads(list):
    def __init__(self, entries: list[dict] | None = None, *, snapshot_payload: dict | None = None):
        super().__init__(entries or [])
        self.docs_snapshot_payload = snapshot_payload


def fetch_github_releases(repo: str, progress_callback=None) -> list[dict]:
    if progress_callback is not None:
        progress_callback(stage="requesting")
    response = requests.get(
        f"https://api.github.com/repos/{repo}/releases?per_page=6",
        headers={
            "Accept": "application/vnd.github+json",
            **(
                {"Authorization": f'Bearer {os.getenv("GITHUB_TOKEN", "")}'}
                if os.getenv("GITHUB_TOKEN")
                else {}
            ),
        },
        timeout=30,
    )
    response.raise_for_status()
    releases = response.json()
    expanded = []
    total_items = len(releases)
    for index, item in enumerate(releases, start=1):
        expanded.append(_expand_release_body(item))
        if progress_callback is not None:
            progress_callback(
                stage="processing",
                processed_items=index,
                total_items=total_items,
            )
    return expanded


def fetch_feed_entries(feed: dict, progress_callback=None, store=None) -> list[dict]:
    if feed.get("type") == "page":
        previous_snapshot = {}
        if store is not None:
            previous_snapshot = store.load_docs_snapshots().get(feed.get("project_id", ""), {})
        crawl_result = crawl_docs_pages(
            project_id=feed.get("project_id", ""),
            docs_url=feed["url"],
            profile=feed,
            progress_callback=progress_callback,
            previous_pages=(previous_snapshot or {}).get("pages", {}),
        )
        return _build_page_source_entries(
            feed=feed,
            crawl_result=crawl_result,
            previous_snapshot=previous_snapshot,
        )

    response = requests.get(feed["url"], timeout=30)
    response.raise_for_status()
    parsed = feedparser.parse(response.text)
    entries = [
        {
            "id": entry.get("id") or entry.get("link"),
            "title": entry.get("title", "Untitled"),
            "link": entry.get("link", ""),
            "published": entry.get("published") or entry.get("updated"),
            "summary": _html_to_text(entry.get("summary", "")),
        }
        for entry in parsed.get("entries", [])
    ]
    if feed.get("expand_links"):
        return [_expand_feed_entry(entry) for entry in entries]
    return entries


def _expand_release_body(release: dict) -> dict:
    body = release.get("body", "")
    link = _extract_github_blob_link(body)
    if not link:
        return release

    try:
        changelog = requests.get(link, timeout=30)
        changelog.raise_for_status()
        enriched = dict(release)
        enriched["body"] = f"{body}\n\nExpanded changelog excerpt:\n{changelog.text[:12000]}"
        return enriched
    except Exception:
        return release


def _extract_github_blob_link(body: str) -> str:
    match = GITHUB_BLOB_LINK_PATTERN.search(body or "")
    if not match:
        return ""
    repo, path = match.groups()
    branch, file_path = path.split("/", 1)
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"


def _expand_feed_entry(entry: dict) -> dict:
    link = entry.get("link")
    if not link:
        return entry

    try:
        response = requests.get(link, timeout=30)
        response.raise_for_status()
        enriched = dict(entry)
        page_text = _html_to_text(response.text)[:12000]
        base_summary = entry.get("summary", "")
        enriched["summary"] = f"{base_summary}\n\n{page_text}".strip()
        return enriched
    except Exception:
        return entry

def _html_to_text(text: str) -> str:
    cleaned = re.sub(r"<(script|style).*?>.*?</\1>", " ", text, flags=re.S | re.I)
    cleaned = HTML_TAG_PATTERN.sub(" ", cleaned)
    cleaned = unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _summarize_docs_group(items: list[dict]) -> str:
    snippets = []
    ordered = sorted(
        items,
        key=lambda item: (
            item.get("nav_depth", 99),
            0 if item.get("is_index_page") else 1,
            item.get("nav_order", 999999),
            item.get("title") or item.get("url") or "",
        ),
    )
    for item in ordered[:3]:
        title = item.get("title") or item.get("url")
        body = _single_line(item.get("text_content") or item.get("body", ""))[:260]
        snippets.append(f"{title}: {body}")
    return "\n\n".join(snippets)


def _build_page_source_entries(*, feed: dict, crawl_result: dict, previous_snapshot: dict | None = None) -> list[dict]:
    records = crawl_result.get("records", [])
    if not records:
        return FetchedFeedPayloads()

    grouped_records = group_docs_records(records)
    project_id = feed.get("project_id") or feed.get("id", "")
    source_key = feed.get("id", "")
    previous_snapshot = previous_snapshot or {}
    current_snapshot = build_docs_snapshot(
        project_id=project_id,
        source_key=source_key,
        records=records,
        crawl_complete=crawl_result.get("crawl_complete", True),
        incomplete_reasons=crawl_result.get("incomplete_reasons", []),
    )
    current_pages = current_snapshot.get("pages", {})
    previous_pages = (previous_snapshot or {}).get("pages", {})
    is_initial_read = feed.get("initial_read_enabled", True) and not previous_pages
    crawl_complete = current_snapshot.get("crawl_complete", True)

    if is_initial_read:
        if not crawl_complete:
            return FetchedFeedPayloads(snapshot_payload=current_snapshot)
        return FetchedFeedPayloads(
            [
                {
                    "id": f'{group["category"]}:initial:{_category_signature(group["items"])}',
                    "project_id": project_id,
                    "event_kind": "docs_initial_read",
                    "title": f'{feed.get("name", feed["url"])} · {group["category"]} 首次解读',
                    "link": group["items"][0].get("url") or feed["url"],
                    "published": _resolve_published_at(group["items"]),
                    "summary": _summarize_docs_group(group["items"]),
                    "category": group["category"],
                    "_docs_snapshot_payload": current_snapshot,
                    "research_bundle": build_docs_initial_research_bundle(
                        category=group["category"],
                        items=group["items"],
                        current_snapshot=current_snapshot,
                    ),
                }
                for group in grouped_records
            ],
            snapshot_payload=current_snapshot,
        )

    if not crawl_complete:
        return FetchedFeedPayloads(snapshot_payload=current_snapshot)

    if not previous_pages:
        return FetchedFeedPayloads(snapshot_payload=current_snapshot)

    page_changes = build_page_changes(previous_pages=previous_pages, current_pages=current_pages)
    if not page_changes:
        return FetchedFeedPayloads(snapshot_payload=current_snapshot)

    current_by_category = {group["category"]: group["items"] for group in grouped_records}
    previous_by_category: dict[str, list[dict]] = defaultdict(list)
    for page in previous_pages.values():
        previous_by_category[page.get("category") or "其他"].append(page)

    changed_by_category: dict[str, list[dict]] = defaultdict(list)
    for page in page_changes:
        changed_by_category[page.get("category") or "其他"].append(page)

    entries = []
    for category, changed_pages in changed_by_category.items():
        current_items = current_by_category.get(category, [])
        previous_items = previous_by_category.get(category, [])
        entries.append(
            {
                "id": f'{category}:diff:{diff_signature(category=category, pages=changed_pages)}',
                "project_id": project_id,
                "event_kind": "docs_diff_update",
                "title": f'{feed.get("name", feed["url"])} · {category} 文档更新解读',
                "link": changed_pages[0].get("url") or feed["url"],
                "published": _resolve_published_at(current_items or previous_items, fallback=_now_iso()),
                "summary": _summarize_page_changes(category, changed_pages),
                "category": category,
                "_docs_snapshot_payload": current_snapshot,
                "research_bundle": build_docs_diff_research_bundle(
                    category=category,
                    changed_pages=changed_pages,
                    current_pages=current_items,
                    previous_pages=previous_items,
                ),
            }
        )
    return FetchedFeedPayloads(entries, snapshot_payload=current_snapshot)


def _summarize_page_changes(category: str, pages: list[dict]) -> str:
    snippets = []
    for page in pages[:4]:
        title = page.get("title_after") or page.get("title_before") or page.get("url")
        if page.get("change_type") == "added":
            snippets.append(f"新增页面 {title}: {page.get('after_summary', '')}")
        elif page.get("change_type") == "removed":
            snippets.append(f"移除页面 {title}: {page.get('before_summary', '')}")
        else:
            added = _single_line(" ".join(page.get("added_blocks", [])[:2]))
            removed = _single_line(" ".join(page.get("removed_blocks", [])[:2]))
            snippets.append(f"改写页面 {title}: 新增 {added or '无'}；移除 {removed or '无'}")
    summary = "；".join(item for item in snippets if item)
    return f"{category} 文档本次主要变化：{summary}" if summary else f"{category} 文档存在结构或内容更新。"


def _category_signature(items: list[dict]) -> str:
    raw = "|".join(
        f'{item.get("url", "")}:{item.get("page_hash") or item.get("content_hash") or ""}'
        for item in items
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16] if raw else "snapshot"


def _resolve_published_at(items: list[dict], fallback: str = "") -> str:
    return max((item.get("last_seen_at") or "" for item in items), default=fallback) or fallback


def _single_line(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
