import hashlib
import re
from datetime import UTC, datetime
from difflib import SequenceMatcher


def page_id_for_url(url: str) -> str:
    return hashlib.sha1((url or "").encode("utf-8")).hexdigest()[:16]


def build_docs_snapshot(
    *,
    project_id: str,
    source_key: str,
    records: list[dict],
    crawl_complete: bool = True,
    incomplete_reasons: list[str] | None = None,
) -> dict:
    pages = {}
    for record in records:
        if not record.get("url"):
            continue
        snapshot = normalize_snapshot_page(record)
        pages[record["url"]] = snapshot

    inventory_hash = _hash_parts(*[f'{url}:{page.get("page_hash","")}' for url, page in sorted(pages.items())])
    category_stats = {}
    section_stats = {}
    for page in pages.values():
        category = page.get("category") or "其他"
        section = page.get("section_key") or page.get("parent_section") or page.get("section") or page.get("title") or "未分类"
        category_stats[category] = category_stats.get(category, 0) + 1
        section_stats[section] = section_stats.get(section, 0) + 1

    return {
        "project_id": project_id,
        "source_key": source_key,
        "updated_at": max((page.get("last_seen_at") or "" for page in pages.values()), default=_now_iso()),
        "inventory_hash": inventory_hash,
        "crawl_complete": crawl_complete,
        "incomplete_reasons": list(incomplete_reasons or []),
        "category_stats": category_stats,
        "section_stats": section_stats,
        "pages": pages,
    }


def normalize_snapshot_page(record: dict) -> dict:
    text_content = (record.get("text_content") or record.get("body") or "").strip()
    headings = [item for item in record.get("headings", []) if item]
    breadcrumbs = [item for item in record.get("breadcrumbs", []) if item]
    page_hash = record.get("page_hash") or record.get("content_hash") or _hash_parts(
        record.get("title", ""),
        text_content,
        *headings,
    )
    return {
        "id": record.get("id") or page_id_for_url(record.get("url", "")),
        "url": record.get("url", ""),
        "path": record.get("path", ""),
        "title": record.get("title", ""),
        "section": record.get("section", ""),
        "section_key": record.get("section_key", ""),
        "parent_section": record.get("parent_section", ""),
        "category": record.get("category", ""),
        "extractor_hint": record.get("extractor_hint", "html-main"),
        "nav_title": record.get("nav_title", ""),
        "nav_depth": record.get("nav_depth", 0),
        "nav_order": record.get("nav_order", 0),
        "is_index_page": record.get("is_index_page", False),
        "headings": headings,
        "breadcrumbs": breadcrumbs,
        "text_content": text_content,
        "summary": summarize_text(text_content, limit=320),
        "content_hash": record.get("content_hash") or _hash_parts(text_content),
        "page_hash": page_hash,
        "last_seen_at": record.get("last_seen_at"),
        "last_checked_at": record.get("last_checked_at") or record.get("last_seen_at"),
        "etag": record.get("etag", ""),
        "http_last_modified": record.get("http_last_modified") or "",
        "was_modified": record.get("was_modified", True),
        "discovered_links": _normalize_discovered_links(record.get("discovered_links") or []),
    }


def _normalize_discovered_links(links: list[dict]) -> list[dict]:
    normalized = []
    for link in links or []:
        if not isinstance(link, dict) or not link.get("url"):
            continue
        normalized.append(
            {
                "url": link.get("url", ""),
                "priority_source": link.get("priority_source", "generic"),
                "order_hint": link.get("order_hint", 0),
                "section_key": link.get("section_key", ""),
                "nav_title": link.get("nav_title", ""),
                "nav_depth": link.get("nav_depth", 0),
                "nav_order": link.get("nav_order", 0),
                "parent_section": link.get("parent_section", ""),
                "is_index_page": link.get("is_index_page"),
            }
        )
    return normalized


def build_page_changes(*, previous_pages: dict, current_pages: dict) -> list[dict]:
    changes = []

    for url, current in current_pages.items():
        previous = previous_pages.get(url)
        if previous is None:
            changes.append(_build_added_page(current))
            continue
        if previous.get("page_hash") == current.get("page_hash"):
            continue
        changes.append(_build_changed_page(previous, current))

    for url, previous in previous_pages.items():
        if url not in current_pages:
            changes.append(_build_removed_page(previous))

    return sorted(
        changes,
        key=lambda item: (
            item.get("category", ""),
            item.get("change_type", ""),
            item.get("path", ""),
            item.get("url", ""),
        ),
    )


def summarize_text(text: str, *, limit: int = 240) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit].rstrip()}..."


def diff_signature(*, category: str, pages: list[dict]) -> str:
    return _hash_parts(
        category,
        *[
            "||".join(
                [
                    page.get("url", ""),
                    page.get("change_type", ""),
                    page.get("before_hash", ""),
                    page.get("after_hash", ""),
                ]
            )
            for page in pages
        ],
    )[:16]


def _build_added_page(current: dict) -> dict:
    blocks = _split_blocks(current.get("text_content", ""))
    return {
        "page_id": current.get("id") or page_id_for_url(current.get("url", "")),
        "url": current.get("url", ""),
        "path": current.get("path", ""),
        "category": current.get("category", ""),
        "title_before": "",
        "title_after": current.get("title", ""),
        "change_type": "added",
        "before_hash": "",
        "after_hash": current.get("page_hash", ""),
        "headings_before": [],
        "headings_after": current.get("headings", []),
        "breadcrumbs_after": current.get("breadcrumbs", []),
        "added_blocks": blocks[:4],
        "removed_blocks": [],
        "before_summary": "",
        "after_summary": current.get("summary") or summarize_text(current.get("text_content", "")),
        "last_seen_at": current.get("last_seen_at"),
    }


def _build_removed_page(previous: dict) -> dict:
    blocks = _split_blocks(previous.get("text_content", ""))
    return {
        "page_id": previous.get("id") or page_id_for_url(previous.get("url", "")),
        "url": previous.get("url", ""),
        "path": previous.get("path", ""),
        "category": previous.get("category", ""),
        "title_before": previous.get("title", ""),
        "title_after": "",
        "change_type": "removed",
        "before_hash": previous.get("page_hash", ""),
        "after_hash": "",
        "headings_before": previous.get("headings", []),
        "headings_after": [],
        "breadcrumbs_before": previous.get("breadcrumbs", []),
        "added_blocks": [],
        "removed_blocks": blocks[:4],
        "before_summary": previous.get("summary") or summarize_text(previous.get("text_content", "")),
        "after_summary": "",
        "last_seen_at": previous.get("last_seen_at"),
    }


def _build_changed_page(previous: dict, current: dict) -> dict:
    added_blocks, removed_blocks = _diff_blocks(previous.get("text_content", ""), current.get("text_content", ""))
    return {
        "page_id": current.get("id") or previous.get("id") or page_id_for_url(current.get("url", "")),
        "url": current.get("url", ""),
        "path": current.get("path", ""),
        "category": current.get("category", "") or previous.get("category", ""),
        "title_before": previous.get("title", ""),
        "title_after": current.get("title", ""),
        "change_type": "changed",
        "before_hash": previous.get("page_hash", ""),
        "after_hash": current.get("page_hash", ""),
        "headings_before": previous.get("headings", []),
        "headings_after": current.get("headings", []),
        "breadcrumbs_before": previous.get("breadcrumbs", []),
        "breadcrumbs_after": current.get("breadcrumbs", []),
        "added_blocks": added_blocks[:4],
        "removed_blocks": removed_blocks[:4],
        "before_summary": previous.get("summary") or summarize_text(previous.get("text_content", "")),
        "after_summary": current.get("summary") or summarize_text(current.get("text_content", "")),
        "last_seen_at": current.get("last_seen_at") or previous.get("last_seen_at"),
    }


def _diff_blocks(before_text: str, after_text: str) -> tuple[list[str], list[str]]:
    before_blocks = _split_blocks(before_text)
    after_blocks = _split_blocks(after_text)
    matcher = SequenceMatcher(a=before_blocks, b=after_blocks)
    added = []
    removed = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in {"replace", "delete"}:
            removed.extend(before_blocks[i1:i2])
        if tag in {"replace", "insert"}:
            added.extend(after_blocks[j1:j2])

    return added, removed


def _split_blocks(text: str) -> list[str]:
    normalized = (text or "").replace("\r", "")
    parts = [part.strip() for part in re.split(r"\n{2,}", normalized) if part.strip()]
    if parts:
        return parts
    compact = normalized.strip()
    return [compact] if compact else []


def _hash_parts(*parts: str) -> str:
    return hashlib.sha256("||".join(part or "" for part in parts).encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
