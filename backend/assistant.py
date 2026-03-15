from datetime import UTC, datetime, timedelta

from .llm import answer_question_with_context, normalize_analysis_record
from .search import fetch_search_result_pages, search_web
from .storage import normalize_config


CATEGORY_KEYWORDS = ["网络", "存储", "调度", "架构", "安全", "升级", "运行时", "可观测性"]


def answer_query(*, snapshot: dict, payload: dict) -> dict:
    config = normalize_config(snapshot.get("config"))
    assistant_config = config["assistant"]
    llm_config = config.get("llm")
    filters = _resolve_filters(payload, assistant_config)
    candidates = _build_candidates(snapshot)
    ranked = _rank_candidates(candidates, filters, assistant_config)
    evidence = ranked[: assistant_config["max_evidence_items"]]
    sources = _build_sources(evidence, assistant_config["max_source_items"])
    next_steps = _collect_next_steps(evidence)
    answer = _build_answer(evidence, filters)

    if filters["mode"] in {"hybrid", "live"} and assistant_config["live_search"]["enabled"]:
        try:
            web_results = search_web(payload.get("query", ""), max_results=assistant_config["live_search"]["max_results"])
            web_pages = fetch_search_result_pages(web_results, max_pages=assistant_config["live_search"]["max_pages"])
            live_answer = answer_with_context(
                query=payload.get("query", ""),
                filters=filters,
                local_evidence=evidence if filters["mode"] != "live" else [],
                web_results=web_pages,
                answer_prompt=assistant_config["prompts"]["answer"],
                llm_config=llm_config,
            )
            answer = live_answer["answer"]
            next_steps = live_answer.get("next_steps") or next_steps
            sources = _merge_web_sources(sources, web_pages, assistant_config["max_source_items"])
        except Exception:
            pass

    return {
        "answer": answer,
        "evidence": [
            {
                "id": item["id"],
                "title": item["title_zh"],
                "summary": item["summary_zh"],
                "source": item["source"],
                "project_id": item["project_id"],
                "project_name": item["project_name"],
                "category": item["category"],
                "urgency": item["urgency"],
                "url": item["url"],
            }
            for item in evidence
        ],
        "next_steps": next_steps,
        "sources": sources,
        "applied_filters": filters,
    }


def _resolve_filters(payload: dict, assistant_config: dict) -> dict:
    query = payload.get("query", "")
    return {
        "mode": payload.get("mode") or assistant_config["default_mode"],
        "project_ids": payload.get("project_ids") or assistant_config["default_project_ids"],
        "categories": payload.get("categories") or _infer_categories(query) or assistant_config["default_categories"],
        "timeframe": payload.get("timeframe") or assistant_config["default_timeframe"],
    }


def answer_with_context(
    *,
    query: str,
    filters: dict,
    local_evidence: list[dict],
    web_results: list[dict],
    answer_prompt: str = "",
    llm_config: dict | None = None,
) -> dict:
    return answer_question_with_context(
        query=query,
        filters=filters,
        local_evidence=local_evidence,
        web_results=web_results,
        answer_prompt=answer_prompt,
        llm_config=llm_config,
    )


def _infer_categories(query: str) -> list[str]:
    return [keyword for keyword in CATEGORY_KEYWORDS if keyword in query]


def _build_candidates(snapshot: dict) -> list[dict]:
    analyses = snapshot.get("analyses", {})
    events = snapshot.get("events", {})
    projects = {project["id"]: project for project in snapshot.get("projects", [])}
    candidates = []

    for event_id, analysis in analyses.items():
        event = events.get(event_id, {})
        project_id = event.get("project_id") or _infer_project_id(event, snapshot.get("projects", []))
        if not project_id:
            continue

        project = projects.get(project_id, {})
        normalized = normalize_analysis_record(analysis)
        category = event.get("category") or _infer_category_from_text(
            " ".join(
                [
                    normalized.get("title_zh", ""),
                    normalized.get("summary_zh", ""),
                    " ".join(normalized.get("tags", [])),
                ]
            )
        )
        candidates.append(
            {
                "id": event_id,
                "project_id": project_id,
                "project_name": project.get("name", project_id),
                "source": event.get("source", ""),
                "title_zh": normalized.get("title_zh", event.get("title", "")),
                "summary_zh": normalized.get("summary_zh", ""),
                "urgency": normalized.get("urgency", "low"),
                "tags": normalized.get("tags", []),
                "category": category,
                "url": event.get("url", ""),
                "published_at": event.get("published_at") or event.get("last_seen_at"),
                "action_items": normalized.get("action_items", []),
            }
        )

    return candidates


def _rank_candidates(candidates: list[dict], filters: dict, assistant_config: dict) -> list[dict]:
    cutoff = _parse_timeframe(filters["timeframe"])
    query_categories = set(filters["categories"])
    query_projects = set(filters["project_ids"])
    release_weight = assistant_config["retrieval"]["release_weight"]
    docs_weight = assistant_config["retrieval"]["docs_weight"]

    scored = []
    for item in candidates:
        if cutoff and item["published_at"]:
            parsed = _parse_datetime(item["published_at"])
            if parsed and parsed < cutoff:
                continue

        score = 0.0
        if query_projects:
            if item["project_id"] not in query_projects:
                continue
            score += 3.0

        if query_categories and item["category"] in query_categories:
            score += 4.0

        if item["source"] == "docs_feed":
            score *= docs_weight
        elif item["source"] == "github_release":
            score *= release_weight

        score += _urgency_bonus(item["urgency"])
        scored.append((score, item))

    ranked = [item for score, item in scored if score > 0]
    ranked.sort(
        key=lambda item: (
            -_score_for_sort(item, filters, assistant_config),
            -_timestamp_for_sort(item["published_at"]),
            item["title_zh"],
        )
    )
    return ranked


def _score_for_sort(item: dict, filters: dict, assistant_config: dict) -> float:
    score = 0.0
    if filters["project_ids"]:
        score += 3.0
    if filters["categories"] and item["category"] in filters["categories"]:
        score += 4.0
    if item["source"] == "docs_feed":
        score *= assistant_config["retrieval"]["docs_weight"]
    elif item["source"] == "github_release":
        score *= assistant_config["retrieval"]["release_weight"]
    score += _urgency_bonus(item["urgency"])
    return score


def _build_sources(evidence: list[dict], max_items: int) -> list[dict]:
    seen = set()
    sources = []
    for item in evidence:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        sources.append(
            {
                "title": item["title_zh"],
                "url": item["url"],
                "source": item["source"],
                "project_name": item["project_name"],
            }
        )
        if len(sources) >= max_items:
            break
    return sources


def _merge_web_sources(sources: list[dict], web_pages: list[dict], max_items: int) -> list[dict]:
    merged = list(sources)
    seen = {item["url"] for item in merged}
    for page in web_pages:
        if page["url"] in seen:
            continue
        seen.add(page["url"])
        merged.append(
            {
                "title": page["title"],
                "url": page["url"],
                "source": "web_search",
                "project_name": "web",
            }
        )
        if len(merged) >= max_items:
            break
    return merged


def _collect_next_steps(evidence: list[dict]) -> list[str]:
    seen = set()
    steps = []
    for item in evidence:
        for action in item["action_items"]:
            if action in seen:
                continue
            seen.add(action)
            steps.append(action)
    return steps


def _build_answer(evidence: list[dict], filters: dict) -> str:
    if not evidence:
        return "当前筛选范围内没有找到可用的项目知识结果。"

    project_names = "、".join(dict.fromkeys(item["project_name"] for item in evidence))
    category_text = f"围绕 {filters['categories'][0]} " if filters["categories"] else ""
    titles = "；".join(item["title_zh"] for item in evidence[:2])
    return f"{project_names} 在 {filters['timeframe']} 内 {category_text}主要变化包括：{titles}。"


def _urgency_bonus(level: str) -> float:
    if level == "high":
        return 3.0
    if level == "medium":
        return 2.0
    return 1.0


def _parse_timeframe(timeframe: str) -> datetime | None:
    if not timeframe:
        return None
    if timeframe.endswith("d") and timeframe[:-1].isdigit():
        return datetime.now(UTC) - timedelta(days=int(timeframe[:-1]))
    if timeframe.endswith("w") and timeframe[:-1].isdigit():
        return datetime.now(UTC) - timedelta(weeks=int(timeframe[:-1]))
    return None


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _timestamp_for_sort(value: str | None) -> float:
    parsed = _parse_datetime(value) if value else None
    return parsed.timestamp() if parsed else 0.0


def _infer_category_from_text(text: str) -> str:
    for keyword in CATEGORY_KEYWORDS:
        if keyword in text:
            return keyword
    return "其他"


def _infer_project_id(event: dict, projects: list[dict]) -> str:
    repo = event.get("repo")
    source_key = event.get("source_key")
    for project in projects:
        if repo and project.get("repo") == repo:
            return project["id"]
        if source_key and source_key == f'{project["id"]}:docs':
            return project["id"]
    return ""
