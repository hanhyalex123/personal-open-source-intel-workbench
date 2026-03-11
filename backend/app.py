from collections import defaultdict
from datetime import UTC, datetime
import re

from flask import Flask, request

from .assistant import answer_query
from .config import DATA_DIR
from .digest_history import build_daily_digest_history, build_recent_project_updates, sort_daily_digest_projects
from .daily_summary import (
    IMPORTANCE_ORDER,
    build_daily_project_summaries,
    load_daily_project_summaries_for_date,
    resolve_summary_date,
)
from .discovery import generate_crawl_profile
from .docs_classify import group_docs_records
from .llm import normalize_analysis_record
from .projects import build_default_crawl_profile, build_project_record
from .storage import JsonStore, normalize_config


def create_app(*, store: JsonStore | None = None, sync_runner=None) -> Flask:
    app = Flask(__name__)
    app.config["STORE"] = store or JsonStore(DATA_DIR)
    app.config["SYNC_RUNNER"] = sync_runner or (lambda: {"status": "noop"})

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/dashboard")
    def dashboard():
        snapshot = app.config["STORE"].load_all()
        items = _build_dashboard_items(snapshot["events"], snapshot["analyses"], snapshot["projects"])
        groups = _group_items(items, snapshot["projects"], snapshot["crawl_profiles"])
        digest_history = build_daily_digest_history(snapshot.get("daily_project_summaries"))
        digest_date = digest_history[0]["date"] if digest_history else resolve_summary_date(snapshot)
        return {
            "overview": {
                "total_items": len(items),
                "stable_items": sum(1 for item in items if item.get("is_stable")),
                "last_sync_at": snapshot["state"].get("last_sync_at"),
                "last_analysis_at": snapshot["state"].get("last_analysis_at"),
                "last_daily_summary_at": snapshot["state"].get("last_daily_summary_at"),
                "last_fetch_success_at": snapshot["state"].get("last_fetch_success_at"),
                "last_incremental_analysis_at": snapshot["state"].get("last_incremental_analysis_at"),
                "last_daily_digest_at": snapshot["state"].get("last_daily_digest_at"),
                "last_heartbeat_at": snapshot["state"].get("last_heartbeat_at"),
                "scheduler": snapshot["state"].get("scheduler", {}),
            },
            "homepage_projects": _build_homepage_projects(snapshot, digest_date),
            "recent_project_updates": build_recent_project_updates(
                snapshot=snapshot,
                since_iso=snapshot["state"].get("last_daily_digest_at"),
            ),
            "daily_digest_history": digest_history,
            "projects": _build_project_sections(snapshot["projects"], snapshot["events"], items),
            "sources": _build_source_summaries(groups),
            "groups": groups,
        }

    @app.get("/api/projects")
    def list_projects():
        return app.config["STORE"].load_all()["projects"]

    @app.get("/api/config")
    def get_config():
        snapshot = app.config["STORE"].load_all()
        return normalize_config(snapshot["config"])

    @app.put("/api/config")
    def update_config():
        payload = request.get_json(force=True)
        store = app.config["STORE"]
        current = normalize_config(store.load_all()["config"])
        merged = _merge_dicts(current, payload)
        normalized = normalize_config(merged)
        store.save_config(normalized)
        return normalized

    @app.post("/api/projects")
    def create_project():
        payload = request.get_json(force=True)
        now_iso = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        project = build_project_record(
            name=payload["name"],
            github_url=payload["github_url"],
            docs_url=payload.get("docs_url", ""),
            now_iso=now_iso,
        )
        store = app.config["STORE"]
        store.save_project(project)
        try:
            profile = generate_crawl_profile(project)
        except Exception:
            profile = build_default_crawl_profile(project)
        store.save_crawl_profile(project["id"], profile)
        return project, 201

    @app.get("/api/projects/<project_id>/crawl-profile")
    def get_crawl_profile(project_id: str):
        profiles = app.config["STORE"].load_all()["crawl_profiles"]
        return profiles.get(project_id, {})

    @app.put("/api/projects/<project_id>/crawl-profile")
    def update_crawl_profile(project_id: str):
        payload = request.get_json(force=True)
        app.config["STORE"].save_crawl_profile(project_id, payload)
        return payload

    @app.post("/api/sync")
    def sync():
        return app.config["SYNC_RUNNER"]()

    @app.post("/api/assistant/query")
    def assistant_query():
        snapshot = app.config["STORE"].load_all()
        if not normalize_config(snapshot["config"])["assistant"]["enabled"]:
            return {"error": "assistant is disabled"}, 403
        payload = request.get_json(force=True)
        return answer_query(snapshot=snapshot, payload=payload)

    return app


def _build_dashboard_items(events: dict, analyses: dict, projects: list[dict]) -> list[dict]:
    items = []
    for event_id, analysis in analyses.items():
        event = events.get(event_id, {})
        project_id = event.get("project_id") or _infer_project_id(event, projects)
        if not project_id:
            continue
        if event.get("source") == "docs_feed" and event.get("category") == "其他":
            continue
        normalized = normalize_analysis_record(analysis)
        items.append(
            {
                "id": event_id,
                "project_id": project_id,
                "group_key": event.get("repo") or event.get("source_key") or "other",
                "source": event.get("source"),
                "title": event.get("title"),
                "version": event.get("version"),
                "url": event.get("url"),
                **normalized,
            }
        )
    return sorted(items, key=lambda item: (_urgency_rank(item.get("urgency")), item.get("id")))


def _group_items(items: list[dict], projects: list[dict], crawl_profiles: dict) -> list[dict]:
    source_meta = _build_source_meta(projects, crawl_profiles)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        grouped[item["group_key"]].append(item)
    groups = [
        {
            "id": key,
            "title": source_meta.get(key, {}).get("title", key),
            "kind": source_meta.get(key, {}).get("kind", "repo"),
            "items": sorted(value, key=lambda item: _urgency_rank(item.get("urgency"))),
        }
        for key, value in grouped.items()
    ]
    return sorted(groups, key=lambda group: (_urgency_rank(group["items"][0].get("urgency")), group["title"]))


def _build_source_meta(projects: list[dict], crawl_profiles: dict) -> dict:
    meta = {}
    for project in projects:
        repo = project.get("repo")
        if repo:
            meta[repo] = {"title": repo, "kind": "repo"}
        if project.get("docs_url"):
            meta[f'{project["id"]}:docs'] = {"title": project.get("name", project["id"]), "kind": "docs"}
    return meta


def _build_source_summaries(groups: list[dict]) -> list[dict]:
    summaries = []
    for group in groups:
        items = group["items"]
        summaries.append(
            {
                "id": group["id"],
                "title": group["title"],
                "kind": group.get("kind", "repo"),
                "total_items": len(items),
                "stable_items": sum(1 for item in items if item.get("is_stable")),
                "highest_urgency": items[0].get("urgency", "low") if items else "low",
            }
        )
    return summaries


def _build_project_sections(projects: list[dict], events: dict, items: list[dict]) -> list[dict]:
    items_by_project = defaultdict(list)
    for item in items:
        event = events.get(item["id"], {})
        project_id = event.get("project_id") or _infer_project_id(event, projects)
        if project_id:
            items_by_project[project_id].append({**item, "_event": event})

    sections = []
    for project in projects:
        project_items = items_by_project.get(project["id"], [])
        release_items = sorted(
            [item for item in project_items if item.get("source") == "github_release"],
            key=_release_sort_key,
            reverse=True,
        )
        docs_items = [item for item in project_items if item.get("source") == "docs_feed"]
        docs_records = [
            {
                "project_id": project["id"],
                "url": item.get("url"),
                "title": item.get("title_zh") or item.get("title"),
                "body": item.get("summary_zh", ""),
                "last_seen_at": item.get("_event", {}).get("published_at"),
                **({"category": item.get("_event", {}).get("category")} if item.get("_event", {}).get("category") else {}),
                **item,
            }
            for item in docs_items
        ]

        docs_categories = []
        for category_group in group_docs_records(docs_records):
            docs_categories.append(
                {
                    "category": category_group["category"],
                    "items": [
                        _strip_internal_fields(item)
                        for item in category_group["items"]
                    ],
                }
            )

        sections.append(
            {
                "id": project["id"],
                "name": project["name"],
                "github_url": project["github_url"],
                "docs_url": project.get("docs_url", ""),
                "release_area": {
                    "enabled": project.get("release_area_enabled", True),
                    "items": [_strip_internal_fields(item) for item in release_items],
                },
                "docs_area": {
                    "enabled": project.get("docs_area_enabled", True) and bool(project.get("docs_url")),
                    "categories": docs_categories,
                },
            }
        )

    return sections


def _build_homepage_projects(snapshot: dict, summary_date: str) -> list[dict]:
    stored = load_daily_project_summaries_for_date(snapshot.get("daily_project_summaries"), summary_date)
    current_summary_date = resolve_summary_date(snapshot)
    if stored and summary_date != current_summary_date:
        return stored

    if stored and len(stored) >= len(snapshot.get("projects") or []):
        return stored

    generated = build_daily_project_summaries(
        snapshot=snapshot,
        summary_date=summary_date,
        now_iso=snapshot.get("state", {}).get("last_daily_summary_at")
        or snapshot.get("state", {}).get("last_sync_at")
        or f"{summary_date}T00:00:00Z",
    )

    if not stored:
        return generated

    existing_by_project = {item["project_id"]: item for item in stored}
    for item in generated:
        existing_by_project.setdefault(item["project_id"], item)
    merged = list(existing_by_project.values())
    return sort_daily_digest_projects(merged)


def _infer_project_id(event: dict, projects: list[dict]) -> str:
    repo = event.get("repo")
    source_key = event.get("source_key")
    for project in projects:
        if repo and project.get("repo") == repo:
            return project["id"]
        if source_key and source_key == f'{project["id"]}:docs':
            return project["id"]
    return ""


def _strip_internal_fields(item: dict) -> dict:
    cleaned = dict(item)
    cleaned.pop("_event", None)
    return cleaned


def _urgency_rank(level: str | None) -> int:
    if level == "high":
        return 0
    if level == "medium":
        return 1
    return 2


SEMVER_PATTERN = re.compile(r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<prerelease>.+))?$")


def _release_sort_key(item: dict):
    version = item.get("version") or item.get("title") or ""
    match = SEMVER_PATTERN.match(version)
    published_at = item.get("_event", {}).get("published_at") or ""
    if not match:
        return (0, 0, 0, 0, published_at)

    prerelease = match.group("prerelease") or ""
    # Stable releases first, then prerelease builds.
    stability_rank = 1 if not prerelease else 0
    return (
        stability_rank,
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        published_at,
    )


def _merge_dicts(base: dict, update: dict) -> dict:
    merged = dict(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged
