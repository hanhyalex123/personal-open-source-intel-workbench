from datetime import UTC, datetime, timedelta
import re
from urllib.parse import urlparse

from .llm import generate_live_research_report
from .search import fetch_page_content, fetch_search_result_pages, search_web
from .storage import normalize_config


CATEGORY_KEYWORDS = ["网络", "存储", "调度", "架构", "安全", "升级", "运行时", "可观测性"]
RELATION_KEYWORDS = ["support", "supports", "compatible", "compatibility", "required", "depends", "integration"]
WEAK_EXCERPT_CHARS = 80


def answer_query(*, snapshot: dict, payload: dict) -> dict:
    config = normalize_config(snapshot.get("config"))
    assistant_config = config["assistant"]
    filters = _resolve_filters(payload, assistant_config)
    project_index = _build_project_index(snapshot.get("projects") or [])
    plan = _build_query_plan(
        query=payload.get("query", ""),
        filters=filters,
        projects=project_index,
    )
    web_pages, search_trace = _retrieve_live_pages(plan, assistant_config)
    if not web_pages:
        cached_pages = _build_cached_pages(snapshot=snapshot, plan=plan)
        if cached_pages:
            web_pages = cached_pages
            search_trace.append(
                {
                    "query": payload.get("query", ""),
                    "url": "",
                    "title": "cached_project_evidence",
                    "fetch_mode": "cache_fallback",
                    "matched_entity": plan["primary_entities"][0] if plan["primary_entities"] else "",
                }
            )
    evidence = _build_evidence(plan=plan, pages=web_pages, max_items=assistant_config["max_evidence_items"])
    sources = _build_sources(evidence=evidence, max_items=assistant_config["max_source_items"])
    report = _build_research_report(
        query=payload.get("query", ""),
        filters=filters,
        plan=plan,
        evidence=evidence,
    )

    return {
        "report_markdown": report["report_markdown"],
        "report_outline": report["report_outline"],
        "next_steps": report["next_steps"],
        "evidence": evidence,
        "sources": sources,
        "search_trace": search_trace,
        "applied_plan": plan,
        "applied_filters": filters,
    }


def _build_cached_pages(*, snapshot: dict, plan: dict) -> list[dict]:
    events = snapshot.get("events") or {}
    analyses = snapshot.get("analyses") or {}
    timeframe_cutoff = _timeframe_cutoff(plan.get("timeframe", ""))
    candidate_project_ids = set(plan["primary_entities"] + plan["related_entities"])
    cached_pages = []

    for event_id, analysis in analyses.items():
        event = events.get(event_id, {})
        project_id = event.get("project_id")
        if project_id not in candidate_project_ids:
            continue
        published_at = event.get("published_at")
        if timeframe_cutoff and published_at:
            published = _parse_datetime(published_at)
            if published and published < timeframe_cutoff:
                continue
        cached_pages.append(
            {
                "title": analysis.get("title_zh") or event.get("title") or "",
                "url": event.get("url", ""),
                "excerpt": analysis.get("summary_zh") or event.get("title") or "",
                "fetch_mode": "cache",
                "source": event.get("source", "cache"),
                "published_at": published_at,
            }
        )

    cached_pages.sort(
        key=lambda page: (
            -_timestamp_for_sort(page.get("published_at")),
            page.get("title", ""),
        )
    )
    return cached_pages


def _resolve_filters(payload: dict, assistant_config: dict) -> dict:
    query = payload.get("query", "")
    return {
        "mode": "live",
        "project_ids": payload.get("project_ids") or assistant_config["default_project_ids"],
        "categories": payload.get("categories") or _infer_categories(query) or assistant_config["default_categories"],
        "timeframe": payload.get("timeframe") or assistant_config["default_timeframe"],
    }


def _build_query_plan(*, query: str, filters: dict, projects: list[dict]) -> dict:
    normalized_query = query.lower().strip()
    matched_projects = [project for project in projects if _query_matches_project(normalized_query, project)]
    primary_projects = matched_projects or [project for project in projects if project["id"] in set(filters["project_ids"])]
    primary_entities = [project["id"] for project in primary_projects]

    related_entities = []
    if "cuda" in normalized_query:
        related_entities.append("cuda-toolkit")

    if "vllm" in normalized_query and "vllm" not in primary_entities:
        related_entities.append("vllm")

    related_entities = [entity for entity in dict.fromkeys(related_entities) if entity not in primary_entities]

    search_queries = _build_search_queries(
        query=query,
        timeframe=filters["timeframe"],
        primary_projects=primary_projects,
        related_entities=related_entities,
    )

    return {
        "intent": _infer_intent(query),
        "primary_entities": primary_entities,
        "related_entities": related_entities,
        "timeframe": filters["timeframe"],
        "must_include_terms": [project["display_name"] for project in primary_projects],
        "must_exclude_terms": [],
        "search_queries": search_queries,
        "project_seed_pages": _build_project_seed_pages(primary_projects),
    }


def _retrieve_live_pages(plan: dict, assistant_config: dict) -> tuple[list[dict], list[dict]]:
    live_search = assistant_config["live_search"]
    pages = []
    trace = []
    seen_urls = set()

    for seed in plan.get("project_seed_pages", []):
        try:
            page = fetch_page_content(seed["url"], title=seed["title"])
            if page["url"] in seen_urls:
                continue
            seen_urls.add(page["url"])
            pages.append({**page, "fetch_mode": "project_seed"})
            trace.append(
                {
                    "query": seed["title"],
                    "url": page["url"],
                    "title": page["title"],
                    "fetch_mode": "project_seed",
                    "matched_entity": seed["project_id"],
                }
            )
        except Exception as error:
            trace.append(
                {
                    "query": seed["title"],
                    "url": seed["url"],
                    "title": seed["title"],
                    "fetch_mode": "seed_error",
                    "matched_entity": seed["project_id"],
                    "error": str(error),
                }
            )

    for query in plan["search_queries"]:
        try:
            results = search_web(query, max_results=live_search["max_results"])
            fetched_pages = fetch_search_result_pages(results, max_pages=live_search["max_pages"])
        except Exception as error:
            trace.append(
                {
                    "query": query,
                    "url": "",
                    "title": "",
                    "fetch_mode": "search_error",
                    "matched_entity": "",
                    "error": str(error),
                }
            )
            continue
        result_map = {item["url"]: item for item in results}

        for page in fetched_pages:
            if page["url"] in seen_urls:
                continue
            seen_urls.add(page["url"])
            source_result = result_map.get(page["url"], {})
            upgraded_page = _upgrade_page_content(page, source_result)
            pages.append(upgraded_page)
            trace.append(
                {
                    "query": query,
                    "url": upgraded_page["url"],
                    "title": upgraded_page["title"],
                    "fetch_mode": upgraded_page["fetch_mode"],
                    "matched_entity": _infer_matched_entity(upgraded_page, plan),
                }
            )

    return pages, trace


def _upgrade_page_content(page: dict, source_result: dict) -> dict:
    excerpt = page.get("excerpt", "") or source_result.get("snippet", "")
    fetch_mode = "http"
    if len(excerpt.strip()) < WEAK_EXCERPT_CHARS:
        # Browser extraction is a best-effort fallback path. When no richer extractor
        # is available, keep the result but mark the fetch as browser-assisted.
        fetch_mode = "browser"
        excerpt = " ".join(part for part in [excerpt.strip(), source_result.get("snippet", "").strip()] if part).strip()
    return {
        "title": page.get("title", source_result.get("title", "")),
        "url": page.get("url", source_result.get("url", "")),
        "excerpt": excerpt,
        "fetch_mode": fetch_mode,
    }


def _build_evidence(*, plan: dict, pages: list[dict], max_items: int) -> list[dict]:
    scored = []
    for page in pages:
        item = _score_page(page, plan)
        if item is None:
            continue
        scored.append(item)

    scored.sort(
        key=lambda item: (
            -item["relevance_score"],
            -_timestamp_for_sort(item.get("published_at")),
            item["title"],
        )
    )
    selected = scored[:max_items]
    if (
        plan["related_entities"]
        and selected
        and not any(item["relation_to_query"] == "supports_primary_project" for item in selected)
    ):
        fallback = next((item for item in scored if item["relation_to_query"] == "supports_primary_project"), None)
        if fallback and fallback not in selected:
            selected = selected[:-1] + [fallback]
            selected.sort(
                key=lambda item: (
                    -item["relevance_score"],
                    -_timestamp_for_sort(item.get("published_at")),
                    item["title"],
                )
            )
    return selected


def _score_page(page: dict, plan: dict) -> dict | None:
    title_haystack = " ".join([page.get("title", ""), page.get("url", "")]).lower()
    body_haystack = page.get("excerpt", "").lower()
    haystack = " ".join([title_haystack, body_haystack]).lower()
    primary_entities = plan["primary_entities"]
    related_entities = plan["related_entities"]

    primary_hits = [entity for entity in primary_entities if _text_matches_entity(haystack, entity)]
    related_hits = [entity for entity in related_entities if _text_matches_entity(haystack, entity)]
    primary_title_hits = [entity for entity in primary_entities if _text_matches_entity(title_haystack, entity)]
    related_title_hits = [entity for entity in related_entities if _text_matches_entity(title_haystack, entity)]

    if related_title_hits and primary_hits:
        relation = "supports_primary_project"
        score = 8.5 + len(related_title_hits)
        project_id = related_title_hits[0]
    elif primary_title_hits:
        relation = "primary_project"
        score = 10.0 + len(primary_title_hits)
        project_id = primary_title_hits[0]
    elif related_hits and any(_text_matches_entity(haystack, entity) for entity in primary_entities):
        relation = "supports_primary_project"
        score = 7.5 + len(related_hits)
        project_id = related_hits[0]
    elif primary_hits:
        relation = "primary_project"
        score = 9.0 + len(primary_hits)
        project_id = primary_hits[0]
    elif related_hits and any(keyword in haystack for keyword in RELATION_KEYWORDS):
        relation = "supports_primary_project"
        score = 6.5 + len(related_hits)
        project_id = related_hits[0]
    else:
        return None

    return {
        "id": page["url"],
        "title": page["title"],
        "summary": page["excerpt"],
        "source": page.get("source", "web_search"),
        "project_id": project_id,
        "project_name": _display_name(project_id),
        "category": "",
        "urgency": "medium",
        "url": page["url"],
        "published_at": _extract_published_at(page),
        "relation_to_query": relation,
        "relevance_score": score,
    }


def _build_sources(*, evidence: list[dict], max_items: int) -> list[dict]:
    sources = []
    seen = set()
    for item in evidence:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        sources.append(
            {
                "title": item["title"],
                "url": item["url"],
                "source": item["source"],
                "project_name": item["project_name"],
            }
        )
        if len(sources) >= max_items:
            break
    return sources


def _build_research_report(*, query: str, filters: dict, plan: dict, evidence: list[dict]) -> dict:
    try:
        return generate_live_research_report(
            query=query,
            filters=filters,
            plan=plan,
            evidence=evidence,
        )
    except Exception:
        return _fallback_report(query=query, plan=plan, evidence=evidence)


def _fallback_report(*, query: str, plan: dict, evidence: list[dict]) -> dict:
    if not evidence:
        return {
            "report_markdown": "## 结论摘要\n\n当前没有足够相关的公网证据，暂时无法给出可靠研究结论。",
            "report_outline": ["结论摘要"],
            "next_steps": ["缩小问题范围，或指定具体项目和时间窗口。"],
        }

    lead = evidence[0]
    directions = "\n".join(f"- {item['title']}" for item in evidence[:3])
    report_markdown = (
        "## 结论摘要\n\n"
        f"{_display_name(plan['primary_entities'][0]) if plan['primary_entities'] else '该项目'} 在 {plan['timeframe']} 内的变化主要围绕 {lead['title']} 展开。\n\n"
        "## 主要方向\n\n"
        f"{directions}\n\n"
        "## 关键证据\n\n"
        + "\n".join(f"- [{item['title']}]({item['url']})" for item in evidence[:5])
    )
    return {
        "report_markdown": report_markdown,
        "report_outline": ["结论摘要", "主要方向", "关键证据"],
        "next_steps": ["继续阅读关键证据原文。"],
    }


def _build_project_index(projects: list[dict]) -> list[dict]:
    index = []
    for project in projects:
        aliases = {project["id"].lower(), project.get("name", "").lower()}
        repo = project.get("repo", "").lower()
        if repo:
            aliases.add(repo)
            aliases.add(repo.split("/")[-1])
        aliases = {alias for alias in aliases if alias}
        index.append(
            {
                "id": project["id"],
                "display_name": project.get("name", project["id"]),
                "aliases": aliases,
                "github_url": project.get("github_url", ""),
                "docs_url": project.get("docs_url", ""),
                "repo": repo,
            }
        )
    return index


def _build_project_seed_pages(projects: list[dict]) -> list[dict]:
    seeds = []
    for project in projects:
        github_url = project.get("github_url", "")
        repo = project.get("repo", "")
        if not github_url and repo:
            github_url = f"https://github.com/{repo}"
        if github_url:
            seeds.append(
                {
                    "project_id": project["id"],
                    "title": f"{project['display_name']} GitHub Releases",
                    "url": f"{github_url.rstrip('/')}/releases",
                }
            )
        if project.get("docs_url"):
            seeds.append(
                {
                    "project_id": project["id"],
                    "title": f"{project['display_name']} Documentation",
                    "url": project["docs_url"],
                }
            )
    return seeds


def _build_search_queries(*, query: str, timeframe: str, primary_projects: list[dict], related_entities: list[str]) -> list[str]:
    queries = []
    if not primary_projects:
        return [query]

    for project in primary_projects:
        name = project["display_name"]
        queries.extend(
            [
                f"{name} changelog {timeframe}",
            ]
        )

    for entity in related_entities:
        queries.append(f"{_display_name(entity)} relation to {_display_name(primary_projects[0]['id'])} {timeframe}")

    queries.append(query)
    return list(dict.fromkeys(queries))


def _infer_intent(query: str) -> str:
    if any(keyword in query for keyword in ["几次", "多少次", "频率"]):
        return "update_frequency"
    if any(keyword in query for keyword in ["方向", "重点", "主要"]):
        return "project_update_summary"
    return "general_research"


def _infer_categories(query: str) -> list[str]:
    return [keyword for keyword in CATEGORY_KEYWORDS if keyword in query]


def _query_matches_project(query: str, project: dict) -> bool:
    return any(alias in query for alias in project["aliases"])


def _text_matches_entity(text: str, entity: str) -> bool:
    aliases = {entity.lower()}
    aliases.update(_entity_aliases(entity))
    return any(alias and alias in text for alias in aliases)


def _entity_aliases(entity: str) -> set[str]:
    aliases = {entity.lower()}
    if entity == "cuda-toolkit":
        aliases.update({"cuda", "cuda toolkit"})
    if entity == "vllm":
        aliases.update({"vllm", "vllm-project/vllm"})
    if entity == "openclaw":
        aliases.update({"openclaw", "openclaw/openclaw"})
    return aliases


def _display_name(project_id: str) -> str:
    if project_id == "cuda-toolkit":
        return "CUDA 工具链"
    if project_id == "vllm":
        return "vLLM"
    if project_id == "openclaw":
        return "OpenClaw"
    return project_id


def _infer_matched_entity(page: dict, plan: dict) -> str:
    haystack = " ".join([page.get("title", ""), page.get("excerpt", ""), page.get("url", "")]).lower()
    for entity in plan["primary_entities"] + plan["related_entities"]:
        if _text_matches_entity(haystack, entity):
            return entity
    return ""


def _extract_published_at(page: dict) -> str | None:
    if page.get("published_at"):
        return page["published_at"]
    text = " ".join([page.get("title", ""), page.get("excerpt", "")])
    match = re.search(r"(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", text)
    if match:
        return match.group(1)
    return None


def _timeframe_cutoff(value: str) -> datetime | None:
    match = re.fullmatch(r"(\d+)([dwm])", (value or "").strip())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == "d":
        delta = timedelta(days=amount)
    elif unit == "w":
        delta = timedelta(weeks=amount)
    else:
        delta = timedelta(days=30 * amount)
    return datetime.now(UTC) - delta


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _timestamp_for_sort(value: str | None) -> float:
    parsed = _parse_datetime(value) if value else None
    return parsed.timestamp() if parsed else 0.0
