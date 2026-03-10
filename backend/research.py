import re
from urllib.parse import urlparse

import requests

from .docs_crawl import _extract_primary_text, _extract_title

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
    ordered_items = sorted(items, key=lambda item: item.get("last_seen_at") or "", reverse=True)
    pages = [
        {
            "title": item.get("title") or item.get("url"),
            "url": item.get("url", ""),
            "snippet": _clip_text(item.get("body", ""), 600),
            "last_seen_at": item.get("last_seen_at"),
        }
        for item in ordered_items[:8]
    ]
    return {
        "category": category,
        "page_count": len(items),
        "pages": pages,
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
