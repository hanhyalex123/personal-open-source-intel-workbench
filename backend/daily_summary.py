from collections import defaultdict
from datetime import UTC, datetime

from .chinese_text import generic_event_title, has_usable_chinese_text, prefer_chinese_text
from .llm import normalize_analysis_record
from .daily_ranking import apply_read_decay, compute_base_score, rerank_with_mmr
from .storage import normalize_config


URGENCY_SCORES = {
    "high": 5.0,
    "medium": 3.0,
    "low": 1.0,
}

SOURCE_SCORES = {
    "github_release": 0.8,
    "docs_feed": 0.5,
}

IMPORTANCE_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
}


def resolve_summary_date(snapshot: dict, now_iso: str | None = None) -> str:
    if now_iso:
        return now_iso[:10]

    state = snapshot.get("state") or {}
    candidate_values = [
        state.get("last_daily_summary_at"),
        state.get("last_sync_at"),
    ]
    candidate_values.extend(
        event.get("published_at") or event.get("last_seen_at")
        for event in (snapshot.get("events") or {}).values()
    )
    candidate_dates = [value[:10] for value in candidate_values if value]
    if candidate_dates:
        return max(candidate_dates)

    return datetime.now(UTC).date().isoformat()


def build_daily_project_summaries(
    *,
    snapshot: dict,
    summary_date: str,
    now_iso: str,
    summarizer=None,
) -> list[dict]:
    projects = snapshot.get("projects") or []
    items_by_project = _collect_project_items(snapshot)
    config = normalize_config(snapshot.get("config"))
    daily_ranking = config.get("daily_ranking", {})
    read_events = snapshot.get("read_events") or []
    summaries = []

    for project in projects:
        project_id = project["id"]
        ranked_items = _sort_items(items_by_project.get(project_id, []))
        daily_items = [item for item in ranked_items if _item_date(item.get("published_at")) == summary_date]
        evidence_items = (daily_items or ranked_items)[:3]
        summary = _build_project_summary(
            project=project,
            summary_date=summary_date,
            now_iso=now_iso,
            daily_items=daily_items,
            ranked_items=ranked_items,
            evidence_items=evidence_items,
            summarizer=summarizer,
        )
        base_score = compute_base_score(
            summary,
            weights=daily_ranking.get("weights", {}),
            now_iso=now_iso,
            recency_half_life_days=daily_ranking.get("recency_half_life_days", 3),
        )
        summary["ranking_score"] = apply_read_decay(
            base_score,
            project_id=project_id,
            read_events=read_events,
            now_iso=now_iso,
            read_decay_days=daily_ranking.get("read_decay_days", 2),
            read_decay_factor=daily_ranking.get("read_decay_factor", 0.5),
        )
        summaries.append(summary)

    summaries.sort(key=_summary_sort_key)
    return rerank_with_mmr(
        summaries,
        lambda_param=daily_ranking.get("mmr_lambda", 0.7),
        diversity_keys=daily_ranking.get("mmr_diversity_keys", []),
    )


def merge_daily_project_summaries(existing: dict, summaries: list[dict]) -> dict:
    merged = dict(existing or {})
    for summary in summaries:
        merged[_summary_key(summary["date"], summary["project_id"])] = summary
    return merged


def load_daily_project_summaries_for_date(summary_index: dict, summary_date: str) -> list[dict]:
    summaries = [
        value
        for key, value in (summary_index or {}).items()
        if key.startswith(f"{summary_date}:")
    ]
    return sorted(summaries, key=_summary_sort_key)


def _collect_project_items(snapshot: dict) -> dict[str, list[dict]]:
    analyses = snapshot.get("analyses") or {}
    events = snapshot.get("events") or {}
    projects = snapshot.get("projects") or []
    grouped: dict[str, list[dict]] = defaultdict(list)

    for event_id, analysis in analyses.items():
        event = events.get(event_id, {})
        project_id = event.get("project_id") or _infer_project_id(event, projects)
        if not project_id:
            continue

        normalized = normalize_analysis_record(analysis)
        grouped[project_id].append(
            {
                "id": event_id,
                "project_id": project_id,
                "source": event.get("source", ""),
                "title_zh": _sanitize_daily_title(project_id, projects, event, normalized),
                "summary_zh": _sanitize_daily_summary(normalized),
                "urgency": normalized.get("urgency", "low"),
                "action_items": normalized.get("action_items", []),
                "detail_sections": normalized.get("detail_sections", []),
                "impact_points": normalized.get("impact_points", []),
                "tags": normalized.get("tags", []),
                "url": event.get("url", ""),
                "version": event.get("version", ""),
                "category": event.get("category", ""),
                "published_at": event.get("published_at") or event.get("last_seen_at"),
            }
        )

    return grouped


def _build_project_summary(*, project: dict, summary_date: str, now_iso: str, daily_items: list[dict], ranked_items: list[dict], evidence_items: list[dict], summarizer):
    project_name = project.get("name", project["id"])
    importance = _resolve_importance(daily_items or ranked_items)

    llm_summary = {}
    if summarizer and evidence_items:
        try:
            llm_summary = summarizer(project=project, evidence_items=evidence_items, summary_date=summary_date) or {}
        except Exception:
            llm_summary = {}

    if llm_summary:
        headline = prefer_chinese_text(llm_summary.get("headline"), fallback=_default_headline(project_name, evidence_items))
        summary_zh = prefer_chinese_text(
            llm_summary.get("summary_zh"),
            fallback=_default_summary_text(project_name, daily_items, evidence_items),
        )
        reason = prefer_chinese_text(
            llm_summary.get("reason"),
            fallback=_default_reason_text(project_name, daily_items, evidence_items),
        )
        importance = llm_summary.get("importance") or importance
    elif daily_items:
        headline = _default_headline(project_name, evidence_items)
        summary_zh = _default_summary_text(project_name, daily_items, evidence_items)
        reason = _default_reason_text(project_name, daily_items, evidence_items)
    elif ranked_items:
        headline = _fallback_recent_headline(project_name, evidence_items)
        summary_zh = "今日没有显著新增高影响变化，建议先关注最近仍值得跟进的项目结论。"
        reason = "当前日期没有新的高优先级项目事件，因此首页回退到最近仍需跟进的证据。"
    else:
        headline = f"{project_name} 今日暂无新情报"
        summary_zh = "当前还没有可用于生成项目摘要的结论。"
        reason = "该项目尚未积累足够的中文分析结果。"
        importance = "low"

    return {
        "id": _summary_key(summary_date, project["id"]),
        "date": summary_date,
        "project_id": project["id"],
        "project_name": project_name,
        "headline": headline,
        "summary_zh": summary_zh,
        "reason": reason,
        "importance": importance,
        "evidence_ids": [item["id"] for item in evidence_items],
        "evidence_items": [
            {
                "id": item["id"],
                "title_zh": item["title_zh"],
                "summary_zh": item["summary_zh"],
                "urgency": item["urgency"],
                "source": item["source"],
                "action_items": item.get("action_items", []),
                "impact_points": item.get("impact_points", []),
                "detail_sections": item.get("detail_sections", []),
                "tags": item.get("tags", []),
                "url": item["url"],
                "version": item.get("version", ""),
                "category": item.get("category", ""),
                "published_at": item.get("published_at"),
            }
            for item in evidence_items
        ],
        "updated_at": now_iso,
    }


def _default_summary_text(project_name: str, daily_items: list[dict], evidence_items: list[dict]) -> str:
    lead = evidence_items[0]["title_zh"]
    if not has_usable_chinese_text(lead) or _is_generic_summary_title(project_name, lead):
        return "今天检测到新的项目变化，建议查看最新中文解读。"
    if len(evidence_items) == 1:
        return f"{project_name} 今天最值得看的变化是 {lead}，它已经进入首页项目级摘要。"

    other_titles = "；".join(
        item["title_zh"] for item in evidence_items[1:] if has_usable_chinese_text(item.get("title_zh", ""))
    )
    if not other_titles:
        return f"{project_name} 今天最值得看的变化是 {lead}，建议结合详情继续判断后续动向。"
    return f"{project_name} 今天最值得看的变化是 {lead}，同时还需要结合 {other_titles} 一起判断最新动向。"


def _default_reason_text(project_name: str, daily_items: list[dict], evidence_items: list[dict]) -> str:
    if not has_usable_chinese_text(evidence_items[0].get("title_zh", "")) or not has_usable_chinese_text(
        evidence_items[0].get("summary_zh", "")
    ) or _is_generic_summary_title(project_name, evidence_items[0].get("title_zh", "")) or evidence_items[0].get(
        "summary_zh", ""
    ) == "该条证据的中文解读暂不可用，建议进入详情查看页面变化。":
        return "当前证据的中文摘要不足，已回退为中文提示。"
    top_urgency = evidence_items[0].get("urgency", "low")
    action_rich = sum(1 for item in evidence_items if item.get("action_items"))
    if top_urgency == "high" and action_rich:
        return "今天出现了高优先级变化，而且证据里包含明确行动项。"
    if len(daily_items) > 1:
        return "同一天出现了多条项目结论，已经值得合并成一张项目摘要卡。"
    return "该变化在今天的项目证据里最值得优先查看。"


def _resolve_importance(items: list[dict]) -> str:
    if not items:
        return "low"
    top = items[0].get("urgency", "low")
    if top == "high":
        return "high"
    if top == "medium":
        return "medium"
    return "low"


def _sort_items(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda item: (
            -_item_score(item),
            -_timestamp_for_sort(item.get("published_at")),
            item.get("title_zh", ""),
        ),
    )


def _item_score(item: dict) -> float:
    urgency_score = URGENCY_SCORES.get(item.get("urgency"), 1.0)
    action_bonus = min(len(item.get("action_items") or []), 2) * 0.7
    source_bonus = SOURCE_SCORES.get(item.get("source"), 0.0)
    return urgency_score + action_bonus + source_bonus


def _item_date(value: str | None) -> str:
    if not value:
        return ""
    return value[:10]


def _summary_key(summary_date: str, project_id: str) -> str:
    return f"{summary_date}:{project_id}"


def _summary_sort_key(item: dict) -> tuple:
    ranking_score = item.get("ranking_score")
    if ranking_score is None:
        ranking_score = 0.0
    return (
        -ranking_score,
        IMPORTANCE_ORDER.get(item.get("importance"), 2),
        -_timestamp_for_sort(item.get("updated_at")),
        item.get("project_name", ""),
    )


def _sanitize_daily_title(project_id: str, projects: list[dict], event: dict, normalized: dict) -> str:
    project = next((item for item in projects if item.get("id") == project_id), {})
    project_name = project.get("name") or project_id
    return prefer_chinese_text(
        normalized.get("title_zh"),
        fallback=generic_event_title(project_name, event.get("source", ""), event.get("event_kind", "")),
    )


def _sanitize_daily_summary(normalized: dict) -> str:
    return prefer_chinese_text(
        normalized.get("summary_zh"),
        fallback="该条证据的中文解读暂不可用，建议进入详情查看页面变化。",
    )


def _default_headline(project_name: str, evidence_items: list[dict]) -> str:
    lead = evidence_items[0].get("title_zh", "") if evidence_items else ""
    if has_usable_chinese_text(lead) and not _is_generic_summary_title(project_name, lead):
        return f"{project_name} 今日重点：{lead}"
    return f"{project_name} 今日重点"


def _fallback_recent_headline(project_name: str, evidence_items: list[dict]) -> str:
    lead = evidence_items[0].get("title_zh", "") if evidence_items else ""
    if has_usable_chinese_text(lead) and not _is_generic_summary_title(project_name, lead):
        return f"{project_name} 近期待关注：{lead}"
    return f"{project_name} 近期待关注"


def _is_generic_summary_title(project_name: str, title: str) -> bool:
    return title in {
        f"{project_name} 文档更新",
        f"{project_name} 文档首读",
        f"{project_name} 版本更新",
        f"{project_name} 项目更新",
    }
def _timestamp_for_sort(value: str | None) -> int:
    if not value:
        return 0
    try:
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0


def _infer_project_id(event: dict, projects: list[dict]) -> str:
    repo = event.get("repo")
    source_key = event.get("source_key")
    for project in projects:
        if repo and project.get("repo") == repo:
            return project["id"]
        if source_key and source_key == f'{project["id"]}:docs':
            return project["id"]
    return ""
