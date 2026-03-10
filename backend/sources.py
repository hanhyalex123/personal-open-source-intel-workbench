import os
import re
from html import unescape

import feedparser
import requests

from .docs_crawl import crawl_docs_pages
from .docs_classify import group_docs_records
from .research import build_docs_group_research_bundle

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


def fetch_github_releases(repo: str) -> list[dict]:
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
    return [_expand_release_body(item) for item in releases]


def fetch_feed_entries(feed: dict) -> list[dict]:
    if feed.get("type") == "page":
        records = crawl_docs_pages(
            project_id=feed.get("project_id", ""),
            docs_url=feed["url"],
            profile=feed,
        )
        grouped = group_docs_records(records)
        return [
            {
                "id": f'{feed["url"]}#{group["category"]}',
                "title": f'{feed.get("name", feed["url"])} · {group["category"]}',
                "link": group["items"][0].get("url") or feed["url"],
                "published": group["items"][0].get("last_seen_at"),
                "summary": _summarize_docs_group(group["items"]),
                "category": group["category"],
                "research_bundle": build_docs_group_research_bundle(
                    category=group["category"],
                    items=group["items"],
                ),
            }
            for group in grouped
        ]

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
    for item in items[:5]:
        title = item.get("title") or item.get("url")
        body = item.get("body", "")[:500]
        snippets.append(f"{title}: {body}")
    return "\n\n".join(snippets)
