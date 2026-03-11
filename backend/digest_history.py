from collections import defaultdict
from datetime import datetime

from .daily_summary import IMPORTANCE_ORDER
from .llm import normalize_analysis_record


def build_daily_digest_history(summary_index: dict) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for _key, summary in (summary_index or {}).items():
        if summary.get("date"):
            grouped[summary["date"]].append(summary)

    history = []
    for date, summaries in grouped.items():
        history.append(
            {
                "date": date,
                "project_count": len(summaries),
                "high_importance_count": sum(1 for item in summaries if item.get("importance") == "high"),
                "updated_at": max((item.get("updated_at") or "" for item in summaries), default=""),
            }
        )

    return sorted(history, key=lambda item: (item["date"], item["updated_at"]), reverse=True)


def build_recent_project_updates(*, snapshot: dict, since_iso: str | None, max_projects: int = 8) -> list[dict]:
    if not since_iso:
        return []

    since_ts = _timestamp_for_sort(since_iso)
    analyses = snapshot.get("analyses") or {}
    events = snapshot.get("events") or {}
    projects = {project["id"]: project for project in snapshot.get("projects") or []}
    grouped: dict[str, list[dict]] = defaultdict(list)

    for event_id, analysis in analyses.items():
        event = events.get(event_id, {})
        project_id = event.get("project_id")
        if not project_id or project_id not in projects:
            continue

        published_at = event.get("published_at") or event.get("last_seen_at")
        if _timestamp_for_sort(published_at) <= since_ts:
            continue

        normalized = normalize_analysis_record(analysis)
        grouped[project_id].append(
            {
                "id": event_id,
                "title_zh": normalized.get("title_zh", event.get("title", "")),
                "summary_zh": normalized.get("summary_zh", ""),
                "urgency": normalized.get("urgency", "low"),
                "source": event.get("source", ""),
                "url": event.get("url", ""),
                "version": event.get("version", ""),
                "category": event.get("category", ""),
                "published_at": published_at,
            }
        )

    updates = []
    for project_id, items in grouped.items():
        items.sort(key=lambda item: (_urgency_rank(item.get("urgency")), -_timestamp_for_sort(item.get("published_at"))))
        project = projects[project_id]
        updates.append(
            {
                "project_id": project_id,
                "project_name": project.get("name", project_id),
                "latest_published_at": items[0].get("published_at"),
                "highest_urgency": items[0].get("urgency", "low"),
                "items": items[:3],
            }
        )

    updates.sort(key=lambda item: (_urgency_rank(item.get("highest_urgency")), -_timestamp_for_sort(item.get("latest_published_at"))))
    return updates[:max_projects]


def sort_daily_digest_projects(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda item: (
            IMPORTANCE_ORDER.get(item.get("importance"), 2),
            -_timestamp_for_sort(item.get("updated_at")),
            item.get("project_name", ""),
        ),
    )


def _urgency_rank(level: str | None) -> int:
    if level == "high":
        return 0
    if level == "medium":
        return 1
    return 2


def _timestamp_for_sort(value: str | None) -> int:
    if not value:
        return 0
    try:
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0
