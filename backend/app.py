from collections import defaultdict
from datetime import UTC, datetime
import re
from urllib.parse import unquote

from flask import Flask, request

from .assistant import answer_query
from .config import DATA_DIR
from .sync_status import SyncCoordinator
from .sync_runs import load_runs, save_runs
from .digest_history import build_daily_digest_history, build_recent_project_updates, sort_daily_digest_projects
from .daily_summary import (
    IMPORTANCE_ORDER,
    build_daily_digest_buckets,
    build_daily_project_summaries,
    load_daily_project_summaries_for_date,
    resolve_summary_date,
)
from .chinese_text import docs_event_title, has_usable_chinese_text, prefer_chinese_text, sanitize_chinese_list
from .discovery import generate_crawl_profile
from .docs_classify import group_docs_records
from .llm import build_llm_config_view, normalize_analysis_record
from .projects import build_default_crawl_profile, build_project_record, normalize_project_record
from .storage import JsonStore, normalize_config


def create_app(*, store: JsonStore | None = None, sync_runner=None, daily_digest_runner=None) -> Flask:
    app = Flask(__name__)
    app.config["STORE"] = store or JsonStore(DATA_DIR)
    app.config["SYNC_RUNNER"] = sync_runner or (lambda **_kwargs: {"status": "noop"})
    app.config["DAILY_DIGEST_RUNNER"] = daily_digest_runner or (lambda **_kwargs: {"status": "noop"})
    app.config["SYNC_COORDINATOR"] = SyncCoordinator(
        incremental_runner=app.config["SYNC_RUNNER"],
        daily_digest_runner=app.config["DAILY_DIGEST_RUNNER"],
        store=app.config["STORE"],
    )

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
        digest_now_iso = (
            snapshot.get("state", {}).get("last_daily_summary_at")
            or snapshot.get("state", {}).get("last_sync_at")
            or f"{digest_date}T00:00:00Z"
        )
        digest_buckets = build_daily_digest_buckets(
            snapshot=snapshot,
            summary_date=digest_date,
            now_iso=digest_now_iso,
        )
        homepage_projects = digest_buckets["must_watch_projects"] + digest_buckets["emerging_projects"]
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
            "homepage_projects": homepage_projects,
            "must_watch_projects": digest_buckets["must_watch_projects"],
            "emerging_projects": digest_buckets["emerging_projects"],
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
        return _build_config_response(snapshot["config"])

    @app.get("/api/read-events")
    def read_events():
        snapshot = app.config["STORE"].load_all()
        return snapshot.get("read_events", [])

    @app.post("/api/read-events")
    def create_read_event():
        payload = request.get_json(force=True) or {}
        store = app.config["STORE"]
        snapshot = store.load_all()
        now_iso = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        record = {
            "project_id": payload.get("project_id"),
            "event_id": payload.get("event_id"),
            "read_at": payload.get("read_at") or now_iso,
        }
        events = list(snapshot.get("read_events", []))
        events.append(record)
        store.save_read_events(events)
        return record, 201

    @app.put("/api/config")
    def update_config():
        payload = request.get_json(force=True)
        store = app.config["STORE"]
        current = normalize_config(store.load_all()["config"])
        merged = _merge_dicts(current, payload)
        normalized = normalize_config(merged)
        store.save_config(normalized)
        return _build_config_response(normalized)

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

    @app.put("/api/projects/<project_id>")
    def update_project(project_id: str):
        payload = request.get_json(force=True)
        store = app.config["STORE"]
        projects = store.load_all()["projects"]
        existing = next((item for item in projects if item["id"] == project_id), None)
        if existing is None:
            return {"error": "project not found"}, 404
        updated = normalize_project_record(_merge_dicts(existing, payload))
        store.save_project(updated)
        return updated

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
        started, status = app.config["SYNC_COORDINATOR"].start_manual_sync()
        return status, 202 if started else 409

    @app.get("/api/sync/status")
    def sync_status():
        return app.config["SYNC_COORDINATOR"].get_status()

    @app.get("/api/sync/runs")
    def sync_runs():
        limit = request.args.get("limit", type=int)
        runs = load_runs(app.config["STORE"]).get("runs", [])
        if limit is not None and limit >= 0:
            runs = runs[:limit]
        summaries = [{key: value for key, value in run.items() if key != "sources"} for run in runs]
        return summaries

    @app.get("/api/sync/runs/<run_id>")
    def sync_run_detail(run_id: str):
        runs = load_runs(app.config["STORE"]).get("runs", [])
        for run in runs:
            if run.get("id") == run_id:
                return run
        return {"error": "run not found"}, 404

    @app.delete("/api/sync/runs")
    def clear_sync_runs():
        payload = {"runs": []}
        save_runs(app.config["STORE"], payload)
        return payload

    @app.post("/api/assistant/query")
    def assistant_query():
        snapshot = app.config["STORE"].load_all()
        if not normalize_config(snapshot["config"])["assistant"]["enabled"]:
            return {"error": "assistant is disabled"}, 403
        payload = request.get_json(force=True)
        return answer_query(snapshot=snapshot, payload=payload)

    @app.get("/api/docs/projects")
    def docs_projects():
        snapshot = app.config["STORE"].load_all()
        return _build_docs_project_index(snapshot)

    @app.get("/api/docs/projects/<project_id>")
    def docs_project_detail(project_id: str):
        snapshot = app.config["STORE"].load_all()
        detail = _build_docs_project_detail(snapshot, project_id)
        if detail is None:
            return {"error": "project not found"}, 404
        return detail

    @app.get("/api/docs/projects/<project_id>/events")
    def docs_project_events(project_id: str):
        snapshot = app.config["STORE"].load_all()
        if not _get_project_by_id(snapshot.get("projects") or [], project_id):
            return {"error": "project not found"}, 404
        mode = request.args.get("mode", "")
        return _collect_docs_events(snapshot, project_id, mode=mode)

    @app.get("/api/docs/projects/<project_id>/pages")
    def docs_project_pages(project_id: str):
        snapshot = app.config["STORE"].load_all()
        if not _get_project_by_id(snapshot.get("projects") or [], project_id):
            return {"error": "project not found"}, 404
        return _build_docs_pages(snapshot, project_id)

    @app.get("/api/docs/projects/<project_id>/pages/<page_id>/diff")
    def docs_project_page_diff(project_id: str, page_id: str):
        snapshot = app.config["STORE"].load_all()
        if not _get_project_by_id(snapshot.get("projects") or [], project_id):
            return {"error": "project not found"}, 404
        detail = _build_docs_page_diff(snapshot, project_id, unquote(page_id))
        if detail is None:
            return {"error": "page not found"}, 404
        return detail

    return app


def _build_dashboard_items(events: dict, analyses: dict, projects: list[dict]) -> list[dict]:
    items = []
    for event_id, analysis in analyses.items():
        event = events.get(event_id, {})
        project_id = event.get("project_id") or _infer_project_id(event, projects)
        if not project_id:
            continue
        normalized = normalize_analysis_record(analysis)
        items.append(
            {
                "id": event_id,
                "project_id": project_id,
                "group_key": event.get("repo") or event.get("source_key") or "other",
                "source": event.get("source"),
                "event_kind": event.get("event_kind", ""),
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
                "tech_categories": project.get("tech_categories", []),
                "focus_topics": project.get("focus_topics", []),
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
    event = cleaned.get("_event") or {}
    if event.get("published_at") and not cleaned.get("published_at"):
        cleaned["published_at"] = event.get("published_at")
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
    published_at = item.get("_event", {}).get("published_at") or item.get("published_at") or ""
    version = item.get("version") or item.get("title") or ""
    match = SEMVER_PATTERN.match(version)
    stability_rank = 1
    version_key = (0, 0, 0)
    if match:
        prerelease = match.group("prerelease") or ""
        stability_rank = 1 if not prerelease else 0
        version_key = (
            int(match.group("major")),
            int(match.group("minor")),
            int(match.group("patch")),
        )
    return (
        stability_rank,
        published_at,
        *version_key,
    )


def _merge_dicts(base: dict, update: dict) -> dict:
    merged = dict(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _build_config_response(config: dict) -> dict:
    normalized = normalize_config(config)
    return {
        **normalized,
        "llm": build_llm_config_view(normalized.get("llm")),
    }


def _build_docs_project_index(snapshot: dict) -> list[dict]:
    projects = [project for project in snapshot.get("projects") or [] if project.get("docs_url")]
    docs_snapshots = snapshot.get("docs_snapshots") or {}
    items = []
    for project in projects:
        project_id = project["id"]
        docs_events = _collect_docs_events(snapshot, project_id)
        latest_initial = next((event for event in docs_events if event.get("event_kind") == "docs_initial_read"), None)
        latest_diff = next((event for event in docs_events if event.get("event_kind") == "docs_diff_update"), None)
        snapshot_pages = list((docs_snapshots.get(project_id) or {}).get("pages", {}).values())
        items.append(
            {
                "project_id": project_id,
                "project_name": project.get("name", project_id),
                "docs_url": project.get("docs_url", ""),
                "page_count": len(snapshot_pages),
                "last_synced_at": (docs_snapshots.get(project_id) or {}).get("updated_at"),
                "categories": _build_docs_category_counts(snapshot_pages),
                "latest_initial_read": _summarize_docs_event(latest_initial),
                "latest_diff_update": _summarize_docs_event(latest_diff),
            }
        )
    return sorted(items, key=lambda item: -_timestamp_for_sort(item.get("last_synced_at")))


def _build_docs_project_detail(snapshot: dict, project_id: str) -> dict | None:
    project = _get_project_by_id(snapshot.get("projects") or [], project_id)
    if project is None:
        return None
    docs_events = _collect_docs_events(snapshot, project_id)
    docs_snapshots = snapshot.get("docs_snapshots") or {}
    snapshot_payload = docs_snapshots.get(project_id) or {}
    pages = list(snapshot_payload.get("pages", {}).values())
    latest_initial = next((event for event in docs_events if event.get("event_kind") == "docs_initial_read"), None)
    latest_diff = next((event for event in docs_events if event.get("event_kind") == "docs_diff_update"), None)
    return {
        "project_id": project_id,
        "project_name": project.get("name", project_id),
        "docs_url": project.get("docs_url", ""),
        "page_count": len(pages),
        "last_synced_at": snapshot_payload.get("updated_at"),
        "categories": _build_docs_category_counts(pages),
        "initial_read": latest_initial,
        "latest_update": latest_diff,
        "recent_events": docs_events[:8],
        "page_stats": {
            "total_pages": len(pages),
            "changed_pages": len((latest_diff or {}).get("changed_pages") or []),
            "last_synced_at": snapshot_payload.get("updated_at"),
        },
    }


def _merge_docs_changed_pages(normalized_pages: list[dict], source_pages: list[dict]) -> list[dict]:
    analysis_pages = [page for page in (normalized_pages or []) if isinstance(page, dict)]
    bundle_pages = [page for page in (source_pages or []) if isinstance(page, dict)]

    if not analysis_pages:
        return bundle_pages
    if not bundle_pages:
        return analysis_pages

    source_by_page_id: dict[str, list[int]] = defaultdict(list)
    source_by_url: dict[str, list[int]] = defaultdict(list)
    for index, page in enumerate(bundle_pages):
        page_id = page.get("page_id")
        url = page.get("url")
        if page_id:
            source_by_page_id[page_id].append(index)
        if url:
            source_by_url[url].append(index)

    used_indices: set[int] = set()
    merged_pages = []
    for index, page in enumerate(analysis_pages):
        source_index = _match_docs_changed_page(
            page=page,
            source_pages=bundle_pages,
            source_by_page_id=source_by_page_id,
            source_by_url=source_by_url,
            used_indices=used_indices,
            fallback_index=index,
        )
        source_page = {}
        if source_index is not None:
            used_indices.add(source_index)
            source_page = bundle_pages[source_index]
        merged_page = dict(source_page)
        merged_page.update(page)
        merged_pages.append(merged_page)

    return merged_pages


def _match_docs_changed_page(
    *,
    page: dict,
    source_pages: list[dict],
    source_by_page_id: dict[str, list[int]],
    source_by_url: dict[str, list[int]],
    used_indices: set[int],
    fallback_index: int,
) -> int | None:
    page_id = page.get("page_id")
    if page_id:
        for index in source_by_page_id.get(page_id, []):
            if index not in used_indices:
                return index

    url = page.get("url")
    if url:
        for index in source_by_url.get(url, []):
            if index not in used_indices:
                return index

    if fallback_index < len(source_pages) and fallback_index not in used_indices:
        return fallback_index

    return None


def _collect_docs_events(snapshot: dict, project_id: str, mode: str = "") -> list[dict]:
    analyses = snapshot.get("analyses") or {}
    events = snapshot.get("events") or {}
    projects = snapshot.get("projects") or []
    docs_events = []

    for event_id, analysis in analyses.items():
        event = events.get(event_id, {})
        if event.get("source") != "docs_feed":
            continue
        candidate_project_id = event.get("project_id") or _infer_project_id(event, projects)
        if candidate_project_id != project_id:
            continue
        event_kind = event.get("event_kind") or "docs_update"
        if mode and event_kind != mode:
            continue
        normalized = normalize_analysis_record(analysis)
        research_bundle = event.get("research_bundle") or {}
        changed_pages = _merge_docs_changed_pages(
            normalized.get("changed_pages"),
            research_bundle.get("changed_pages", []),
        )
        project = _get_project_by_id(projects, project_id) or {}
        normalized = _with_docs_analysis_fallback(
            normalized=normalized,
            event=event,
            changed_pages=changed_pages,
            project_name=project.get("name") or project_id or "该项目",
        )
        docs_events.append(
            {
                "id": event_id,
                "project_id": project_id,
                "event_kind": event_kind,
                "title": event.get("title", ""),
                "title_zh": normalized.get("title_zh", event.get("title", "")),
                "summary_zh": normalized.get("summary_zh", ""),
                "details_zh": normalized.get("details_zh", ""),
                "analysis_mode": normalized.get("analysis_mode") or (
                    "initial_read" if event_kind == "docs_initial_read" else "diff_update"
                ),
                "category": event.get("category", ""),
                "url": event.get("url", ""),
                "published_at": event.get("published_at"),
                "urgency": normalized.get("urgency", "low"),
                "detail_sections": normalized.get("detail_sections", []),
                "impact_points": normalized.get("impact_points", []),
                "action_items": normalized.get("action_items", []),
                "doc_summary": normalized.get("doc_summary", ""),
                "doc_key_points": normalized.get("doc_key_points", []),
                "changed_pages": changed_pages,
                "diff_highlights": normalized.get("diff_highlights", []),
                "reading_guide": normalized.get("reading_guide", []),
                "research_bundle": research_bundle,
            }
        )

    docs_events.sort(
        key=lambda item: (
            -_timestamp_for_sort(item.get("published_at")),
            _urgency_rank(item.get("urgency")),
            item.get("title_zh", ""),
        )
    )
    return docs_events


def _looks_like_empty_analysis(normalized: dict) -> bool:
    return not has_usable_chinese_text(normalized.get("summary_zh"))


def _with_docs_analysis_fallback(*, normalized: dict, event: dict, changed_pages: list[dict], project_name: str) -> dict:
    fallback = dict(normalized)
    page_titles = [page.get("title_after") or page.get("title") or page.get("page_id") for page in changed_pages]
    page_titles = [title for title in page_titles if title]
    primary_page = page_titles[0] if page_titles else "相关页面"
    event_kind = event.get("event_kind") or "docs_update"
    fallback_title = prefer_chinese_text(
        event.get("title"),
        fallback=docs_event_title(project_name, event_kind),
    )
    fallback["title_zh"] = prefer_chinese_text(
        fallback.get("title_zh"),
        fallback=fallback_title,
    )
    if not has_usable_chinese_text(fallback.get("summary_zh")):
        fallback["summary_zh"] = f"{primary_page} 页面有新变化，请先看页面摘要与 diff。"
    if not has_usable_chinese_text(fallback.get("doc_summary")):
        fallback["doc_summary"] = "这次文档变更的中文解读暂不可用，请先看页面摘要与 diff。"
    if not has_usable_chinese_text(fallback.get("details_zh")):
        fallback["details_zh"] = "当前证据不足以生成详细中文解读，建议先看页面摘要、页面 diff 和关联变更。"
    fallback["diff_highlights"] = sanitize_chinese_list(
        fallback.get("diff_highlights"),
        fallback=f"先看 {primary_page} 的页面变化。",
    )
    fallback["reading_guide"] = sanitize_chinese_list(
        fallback.get("reading_guide"),
        fallback=f"先看 {primary_page}",
    )
    fallback["impact_points"] = sanitize_chinese_list(
        fallback.get("impact_points"),
        fallback="影响点待补充，建议先结合页面变化判断。",
    )
    fallback["action_items"] = sanitize_chinese_list(
        fallback.get("action_items"),
        fallback="建议先核对相关页面变化，再决定是否继续研究。",
    )
    return fallback


def _build_docs_pages(snapshot: dict, project_id: str) -> list[dict]:
    docs_snapshots = snapshot.get("docs_snapshots") or {}
    snapshot_payload = docs_snapshots.get(project_id) or {}
    pages = list(snapshot_payload.get("pages", {}).values())
    latest_change_by_page = _latest_docs_change_by_page(_collect_docs_events(snapshot, project_id))

    result = []
    for page in pages:
        latest_change = latest_change_by_page.get(page.get("id"))
        result.append(
            {
                "id": page.get("id"),
                "url": page.get("url", ""),
                "path": page.get("path", ""),
                "title": page.get("title", ""),
                "section": page.get("section", ""),
                "category": page.get("category", ""),
                "extractor_hint": page.get("extractor_hint", "html-main"),
                "headings": page.get("headings", []),
                "breadcrumbs": page.get("breadcrumbs", []),
                "summary": page.get("summary", ""),
                "last_seen_at": page.get("last_seen_at"),
                "latest_change": latest_change,
                "is_recently_changed": latest_change is not None,
            }
        )

    return sorted(
        result,
        key=lambda item: (
            0 if item.get("is_recently_changed") else 1,
            item.get("category", ""),
            item.get("title", ""),
        )
    )


def _build_docs_page_diff(snapshot: dict, project_id: str, page_id: str) -> dict | None:
    pages = _build_docs_pages(snapshot, project_id)
    page = next((item for item in pages if item.get("id") == page_id), None)
    if page is None:
        return None

    events = _collect_docs_events(snapshot, project_id)
    relevant = []
    latest_page_diff = None
    for event in events:
        for changed_page in (event.get("research_bundle") or {}).get("changed_pages", []):
            if changed_page.get("page_id") == page_id:
                item = {
                    "event_id": event.get("id"),
                    "event_kind": event.get("event_kind"),
                    "title_zh": event.get("title_zh"),
                    "published_at": event.get("published_at"),
                    "change_type": changed_page.get("change_type"),
                    "before_summary": changed_page.get("before_summary", ""),
                    "after_summary": changed_page.get("after_summary", ""),
                    "added_blocks": changed_page.get("added_blocks", []),
                    "removed_blocks": changed_page.get("removed_blocks", []),
                    "headings_before": changed_page.get("headings_before", []),
                    "headings_after": changed_page.get("headings_after", []),
                    "url": changed_page.get("url", page.get("url")),
                }
                relevant.append(item)
                if latest_page_diff is None:
                    latest_page_diff = item
                break

    return {
        "page": page,
        "latest_diff": latest_page_diff,
        "history": relevant[:6],
    }


def _latest_docs_change_by_page(events: list[dict]) -> dict[str, dict]:
    latest = {}
    for event in events:
        if event.get("event_kind") != "docs_diff_update":
            continue
        for page in (event.get("research_bundle") or {}).get("changed_pages", []):
            page_id = page.get("page_id")
            if not page_id or page_id in latest:
                continue
            latest[page_id] = {
                "event_id": event.get("id"),
                "event_kind": event.get("event_kind"),
                "title_zh": event.get("title_zh"),
                "published_at": event.get("published_at"),
                "change_type": page.get("change_type"),
            }
    return latest


def _build_docs_category_counts(pages: list[dict]) -> list[dict]:
    grouped: dict[str, int] = defaultdict(int)
    for page in pages:
        grouped[page.get("category") or "其他"] += 1
    return [
        {"category": category, "page_count": count}
        for category, count in sorted(grouped.items(), key=lambda item: (-item[1], item[0]))
    ]


def _summarize_docs_event(event: dict | None) -> dict | None:
    if event is None:
        return None
    return {
        "id": event.get("id"),
        "event_kind": event.get("event_kind"),
        "title_zh": event.get("title_zh"),
        "summary_zh": event.get("summary_zh"),
        "published_at": event.get("published_at"),
        "changed_page_count": len(event.get("changed_pages") or []),
    }


def _get_project_by_id(projects: list[dict], project_id: str) -> dict | None:
    return next((project for project in projects if project.get("id") == project_id), None)


def _timestamp_for_sort(value: str | None) -> int:
    if not value:
        return 0
    try:
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0
