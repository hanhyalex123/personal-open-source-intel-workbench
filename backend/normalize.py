import hashlib
import json


ANALYSIS_INPUT_VERSION = "research-v2"


def normalize_release_event(repo: str, payload: dict) -> dict:
    version = payload.get("tag_name") or payload.get("name") or "unknown"
    research_bundle = payload.get("research_bundle") or {}
    event = {
        "id": f"github-release:{repo}:{version}",
        "source": "github_release",
        "repo": repo,
        "source_key": repo,
        "title": payload.get("name") or version,
        "version": version,
        "url": payload.get("html_url", ""),
        "published_at": payload.get("published_at"),
        "body": payload.get("body", ""),
        "research_bundle": research_bundle,
    }
    event["content_hash"] = _hash_parts(
        ANALYSIS_INPUT_VERSION,
        repo,
        version,
        event["title"],
        event["body"],
        event["url"],
        json.dumps(research_bundle, ensure_ascii=False, sort_keys=True),
    )
    return event


def normalize_feed_entry(source_key: str, payload: dict) -> dict:
    source_id = payload.get("id") or payload.get("link") or payload.get("title") or "unknown"
    research_bundle = payload.get("research_bundle") or {}
    event = {
        "id": f"docs-feed:{source_key}:{source_id}",
        "source": "docs_feed",
        "source_key": source_key,
        "project_id": payload.get("project_id"),
        "event_kind": payload.get("event_kind") or "docs_update",
        "title": payload.get("title") or "Untitled",
        "url": payload.get("link") or payload.get("id") or "",
        "published_at": payload.get("published") or payload.get("updated"),
        "body": payload.get("summary") or payload.get("description") or "",
        "category": payload.get("category", ""),
        "research_bundle": research_bundle,
    }
    event["content_hash"] = _hash_parts(
        ANALYSIS_INPUT_VERSION,
        source_key,
        source_id,
        event["event_kind"],
        event["title"],
        event["body"],
        event["url"],
        json.dumps(research_bundle, ensure_ascii=False, sort_keys=True),
    )
    return event


def should_analyze_event(event: dict, known_events: dict, analyses: dict) -> bool:
    known_event = known_events.get(event["id"])
    if known_event is None:
        return True
    if known_event.get("content_hash") != event.get("content_hash"):
        return True
    analysis = analyses.get(event["id"], {})
    if not analysis:
        return True
    return False


def _hash_parts(*parts: str) -> str:
    joined = "||".join(part or "" for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
