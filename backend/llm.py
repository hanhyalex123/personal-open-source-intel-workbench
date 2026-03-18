import json
import os
import re
import time
from typing import Any

import requests

from .prompts import (
    build_analysis_prompt,
    build_assistant_answer_prompt,
    build_live_research_report_prompt,
    build_project_daily_summary_prompt,
)


DEFAULT_API_URL = "https://www.packyapi.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_PRIMARY_PROVIDER = "primary-gateway"
DEFAULT_OPENAI_PROVIDER = "OpenAI"


class LLMRequestError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        error_kind: str = "llm_gateway",
        provider: str = "",
        model: str = "",
        api_url: str = "",
        route_alias: str = "",
        status_code: int | str | None = None,
        used_fallback: bool = False,
        fallback_provider: str = "",
        fallback_model: str = "",
        fallback_route_alias: str = "",
    ):
        super().__init__(message)
        self.error_kind = error_kind
        self.provider = provider
        self.model = model
        self.api_url = api_url
        self.route_alias = route_alias
        self.status_code = status_code
        self.used_fallback = used_fallback
        self.fallback_provider = fallback_provider
        self.fallback_model = fallback_model
        self.fallback_route_alias = fallback_route_alias


def get_llm_settings(llm_config: dict | None = None) -> dict:
    active_provider = _resolve_active_provider(llm_config)
    if not active_provider:
        raise RuntimeError("No LLM provider enabled")

    primary_settings = _empty_provider_settings()
    fallback_settings = _empty_provider_settings()
    targets: list[dict] = []

    if active_provider == "openai":
        openai_routes = [route for route in _resolve_openai_routes(llm_config) if route.get("enabled")]
        if openai_routes:
            primary_settings = dict(openai_routes[0])
            targets.append(dict(primary_settings))
            if len(openai_routes) > 1:
                fallback_settings = dict(openai_routes[1])
                targets.append(dict(fallback_settings))
            elif _is_provider_enabled(llm_config, "packy"):
                fallback_settings = _resolve_provider_settings("packy", llm_config)
                targets.append(dict(fallback_settings))
        else:
            primary_settings = _resolve_provider_settings(active_provider, llm_config)
            targets.append(dict(primary_settings))
            if _is_provider_enabled(llm_config, "packy"):
                fallback_settings = _resolve_provider_settings("packy", llm_config)
                targets.append(dict(fallback_settings))
    else:
        primary_settings = _resolve_provider_settings(active_provider, llm_config)
        targets.append(dict(primary_settings))
        if _is_provider_enabled(llm_config, "openai"):
            openai_routes = [route for route in _resolve_openai_routes(llm_config) if route.get("enabled")]
            if openai_routes:
                fallback_settings = dict(openai_routes[0])
            else:
                fallback_settings = _resolve_provider_settings("openai", llm_config)
            if fallback_settings.get("api_key") or fallback_settings.get("model") or fallback_settings.get("api_url"):
                targets.append(dict(fallback_settings))

    fallback_api_url = fallback_settings.get("api_url") or primary_settings.get("api_url", "")
    if len(targets) == 1 and not fallback_settings.get("api_key"):
        fallback_api_url = ""

    return {
        "api_key": primary_settings.get("api_key", ""),
        "api_url": primary_settings.get("api_url", ""),
        "model": primary_settings.get("model", ""),
        "provider": primary_settings.get("provider", ""),
        "protocol": primary_settings.get("protocol", ""),
        "route_alias": primary_settings.get("route_alias", ""),
        "reasoning_effort": _resolve_shared_reasoning_effort(llm_config),
        "disable_response_storage": _resolve_shared_disable_response_storage(llm_config),
        "fallback_api_key": fallback_settings.get("api_key", ""),
        "fallback_api_url": fallback_api_url,
        "fallback_model": fallback_settings.get("model", ""),
        "fallback_provider": fallback_settings.get("provider", ""),
        "fallback_protocol": fallback_settings.get("protocol", "") or (
            primary_settings.get("protocol", "") if fallback_api_url == primary_settings.get("api_url", "") else ""
        ),
        "fallback_route_alias": fallback_settings.get("route_alias", ""),
        "targets": targets,
    }


def build_llm_config_view(llm_config: dict | None = None) -> dict:
    llm_config = llm_config or {}
    packy_enabled = _is_provider_enabled(llm_config, "packy")
    openai_enabled = _is_provider_enabled(llm_config, "openai")
    packy_effective = _resolve_provider_settings("packy", llm_config)
    openai_effective = _resolve_provider_settings("openai", llm_config)
    packy_settings = (
        _resolve_provider_settings("packy", llm_config, use_env_api_key=False, allow_openai_url_fallback=False)
        if packy_enabled
        else _empty_provider_settings()
    )
    openai_settings = (
        _resolve_provider_settings("openai", llm_config, use_env_api_key=False, allow_openai_url_fallback=False)
        if openai_enabled
        else _empty_provider_settings()
    )
    packy_api_key_configured = packy_enabled and bool(_resolve_provider_settings("packy", llm_config)["api_key"])
    openai_api_key_configured = openai_enabled and bool(
        _resolve_provider_settings("openai", llm_config)["api_key"] or any(route.get("api_key") for route in _resolve_openai_routes(llm_config))
    )
    raw_packy = (llm_config.get("packy") or {})
    raw_openai = (llm_config.get("openai") or {})
    packy_env_key = os.getenv("PACKY_API_KEY", "")
    openai_env_key = os.getenv("OPENAI_API_KEY", "")
    packy_key_source = _resolve_api_key_source(raw_packy.get("api_key", ""), packy_env_key)
    openai_key_source = _resolve_api_key_source(raw_openai.get("api_key", ""), openai_env_key)
    packy_key_masked = _mask_api_key(raw_packy.get("api_key") or packy_env_key)
    openai_key_masked = _mask_api_key(raw_openai.get("api_key") or openai_env_key)
    openai_routes = []
    for route in _resolve_openai_routes(llm_config):
        route_api_key = route.get("api_key", "")
        route_source = _resolve_api_key_source(route_api_key, openai_env_key if not route_api_key else "")
        openai_routes.append(
            {
                "alias": route.get("route_alias", ""),
                "enabled": route.get("enabled", True),
                "api_key": route_api_key,
                "api_key_masked": _mask_api_key(route_api_key or openai_env_key),
                "api_key_source": route_source,
                "api_url": route.get("api_url", ""),
                "model": route.get("model", ""),
                "protocol": route.get("protocol", ""),
                "priority": route.get("priority", 0),
                "provider": route.get("provider", ""),
            }
        )
    return {
        "active_provider": _resolve_active_provider(llm_config),
        "reasoning_effort": _resolve_shared_reasoning_effort(llm_config),
        "disable_response_storage": _resolve_shared_disable_response_storage(llm_config),
        "packy": {
            "enabled": packy_enabled,
            "api_key": raw_packy.get("api_key", "") if packy_enabled else "",
            "provider": packy_settings["provider"],
            "api_url": packy_settings["api_url"],
            "model": packy_settings["model"],
            "protocol": packy_settings["protocol"],
            "api_key_configured": packy_api_key_configured,
            "api_key_masked": packy_key_masked,
            "api_key_source": packy_key_source,
            "effective_api_url": packy_effective["api_url"],
            "effective_model": packy_effective["model"],
            "effective_protocol": packy_effective["protocol"],
            "effective_provider": packy_effective["provider"],
        },
        "openai": {
            "enabled": openai_enabled,
            "api_key": raw_openai.get("api_key", "") if openai_enabled else "",
            "provider": openai_settings["provider"],
            "api_url": openai_settings["api_url"],
            "model": openai_settings["model"],
            "protocol": openai_settings["protocol"],
            "routes": openai_routes,
            "api_key_configured": openai_api_key_configured,
            "api_key_masked": openai_key_masked,
            "api_key_source": openai_key_source,
            "effective_api_url": openai_effective["api_url"],
            "effective_model": openai_effective["model"],
            "effective_protocol": openai_effective["protocol"],
            "effective_provider": openai_effective["provider"],
        },
    }


def analyze_event(event: dict, llm_config: dict | None = None) -> dict:
    settings = get_llm_settings(llm_config)
    if not settings["api_key"]:
        raise RuntimeError(f"{_missing_api_key_name(llm_config)} is not configured")

    response, llm_meta = _request_with_fallback(settings=settings, prompt=build_analysis_prompt(event), max_tokens=1200)
    payload = _safe_response_payload(response, settings=llm_meta)
    analysis = parse_analysis_response(payload)
    analysis["_llm"] = llm_meta
    return analysis


def answer_question_with_context(
    *,
    query: str,
    filters: dict,
    local_evidence: list[dict],
    web_results: list[dict],
    answer_prompt: str = "",
    llm_config: dict | None = None,
) -> dict:
    settings = get_llm_settings(llm_config)
    if not settings["api_key"]:
        raise RuntimeError(f"{_missing_api_key_name(llm_config)} is not configured")

    response, llm_meta = _request_with_fallback(
        settings=settings,
        prompt=build_assistant_answer_prompt(
            query=query,
            filters=filters,
            local_evidence=local_evidence,
            web_results=web_results,
            answer_prompt=answer_prompt,
        ),
        max_tokens=1400,
    )
    payload = _safe_response_payload(response, settings=llm_meta)
    parsed = parse_assistant_response(payload)
    parsed["_llm"] = llm_meta
    return parsed


def summarize_project_daily_intel(
    *,
    project: dict,
    evidence_items: list[dict],
    summary_date: str,
    llm_config: dict | None = None,
) -> dict:
    settings = get_llm_settings(llm_config)
    if not settings["api_key"]:
        raise RuntimeError(f"{_missing_api_key_name(llm_config)} is not configured")

    response, llm_meta = _request_with_fallback(
        settings=settings,
        prompt=build_project_daily_summary_prompt(
            project=project,
            evidence_items=evidence_items,
            summary_date=summary_date,
        ),
        max_tokens=700,
    )
    payload = _safe_response_payload(response, settings=llm_meta)
    parsed = parse_project_daily_summary_response(payload)
    parsed["_llm"] = llm_meta
    return parsed


def generate_live_research_report(
    *,
    query: str,
    filters: dict,
    plan: dict,
    evidence: list[dict],
    answer_prompt: str = "",
    llm_config: dict | None = None,
) -> dict:
    settings = get_llm_settings(llm_config)
    if not settings["api_key"]:
        raise RuntimeError(f"{_missing_api_key_name(llm_config)} is not configured")

    response, llm_meta = _request_with_fallback(
        settings=settings,
        prompt=build_live_research_report_prompt(
            query=query,
            filters=filters,
            plan=plan,
            evidence=evidence,
            answer_prompt=answer_prompt,
        ),
        max_tokens=1800,
    )
    payload = _safe_response_payload(response, settings=llm_meta)
    parsed = parse_live_research_report_response(payload)
    parsed["_llm"] = llm_meta
    return parsed


def has_configured_llm(llm_config: dict | None = None) -> bool:
    try:
        settings = get_llm_settings(llm_config)
    except RuntimeError:
        return False
    return any(target.get("api_key") for target in settings.get("targets") or []) or bool(settings.get("api_key"))


def ensure_llm_availability(llm_config: dict | None = None) -> dict:
    settings = get_llm_settings(llm_config)
    if not settings["api_key"]:
        raise RuntimeError(f"{_missing_api_key_name(llm_config)} is not configured")

    response, llm_meta = _request_with_fallback(
        settings=settings,
        prompt="reply only with ok",
        max_tokens=16,
    )
    payload = _safe_response_payload(response, settings=llm_meta)
    text = _extract_text(payload).strip()
    if not text:
        raise LLMRequestError(
            f"主模型 {llm_meta.get('model') or 'unknown'} 可达但返回空响应。",
            error_kind="llm_empty_response",
            provider=llm_meta.get("provider", ""),
            model=llm_meta.get("model", ""),
            api_url=llm_meta.get("api_url", ""),
            route_alias=llm_meta.get("route_alias", ""),
        )
    return llm_meta


def _resolve_active_provider(llm_config: dict | None) -> str:
    provider = ((llm_config or {}).get("active_provider") or "").lower()
    if provider in {"packy", "openai"} and _is_provider_enabled(llm_config, provider):
        return provider
    if _is_provider_enabled(llm_config, "packy") and _resolve_provider_settings("packy", llm_config)["api_key"]:
        return "packy"
    if _is_provider_enabled(llm_config, "openai"):
        openai_settings = _resolve_provider_settings("openai", llm_config)
        if openai_settings["api_key"]:
            return "openai"
        if any(route.get("enabled") and route.get("api_key") for route in _resolve_openai_routes(llm_config)):
            return "openai"
    if _is_provider_enabled(llm_config, "packy"):
        return "packy"
    if _is_provider_enabled(llm_config, "openai"):
        return "openai"
    return ""


def _is_provider_enabled(llm_config: dict | None, provider_key: str) -> bool:
    if provider_key not in {"packy", "openai"}:
        return True
    provider_config = (llm_config or {}).get(provider_key) or {}
    enabled = provider_config.get("enabled")
    if enabled is None:
        return True
    if isinstance(enabled, bool):
        return enabled
    if isinstance(enabled, str):
        return enabled.strip().lower() in {"1", "true", "yes", "on"}
    return bool(enabled)


def _empty_provider_settings() -> dict:
    return {
        "api_key": "",
        "api_url": "",
        "model": "",
        "provider": "",
        "protocol": "",
        "route_alias": "",
        "priority": 0,
        "enabled": True,
    }


def _resolve_api_key_source(config_key: str, env_key: str) -> str:
    if config_key:
        return "config"
    if env_key:
        return "env"
    return "missing"


def _mask_api_key(value: str) -> str:
    if not value:
        return ""
    trimmed = value.strip()
    if len(trimmed) <= 8:
        return f"{trimmed[:2]}****{trimmed[-2:]}"
    return f"{trimmed[:4]}****{trimmed[-4:]}"


def _is_openai_chat_protocol(protocol: str) -> bool:
    return (protocol or "").strip().lower() in {"openai", "openai-chat", "chat"}


def _is_openai_responses_protocol(protocol: str) -> bool:
    return (protocol or "").strip().lower() in {"responses", "openai-responses", "codex"}


def _normalize_openai_settings(api_url: str, protocol: str) -> tuple[str, str]:
    if not isinstance(api_url, str) or not api_url.strip():
        return api_url, protocol
    trimmed = api_url.strip()
    lower = trimmed.lower()
    if "/v1/" in lower:
        return trimmed, protocol
    normalized_protocol = protocol
    if _is_openai_chat_protocol(protocol):
        return f"{trimmed.rstrip('/')}/v1/chat/completions", normalized_protocol
    if _is_openai_responses_protocol(protocol):
        return f"{trimmed.rstrip('/')}/v1/responses", normalized_protocol
    if not protocol:
        return f"{trimmed.rstrip('/')}/v1/responses", "openai-responses"
    return trimmed, normalized_protocol


def _resolve_provider_settings(
    provider_key: str,
    llm_config: dict | None,
    *,
    use_env_api_key: bool = True,
    allow_openai_url_fallback: bool = True,
) -> dict:
    provider_config = ((llm_config or {}).get(provider_key) or {})
    packy_config = ((llm_config or {}).get("packy") or {})
    packy_api_url = _first_non_empty(packy_config.get("api_url"), os.getenv("PACKY_API_URL", DEFAULT_API_URL))
    packy_protocol = _first_non_empty(packy_config.get("protocol"), os.getenv("PACKY_PROTOCOL", ""))
    if provider_key == "openai":
        openai_api_url = _first_non_empty(provider_config.get("api_url"), os.getenv("OPENAI_API_URL", ""))
        if allow_openai_url_fallback:
            openai_api_url = _first_non_empty(openai_api_url, packy_api_url)
        openai_protocol = _first_non_empty(provider_config.get("protocol"), os.getenv("OPENAI_PROTOCOL", ""))
        if not openai_protocol and allow_openai_url_fallback and openai_api_url == packy_api_url:
            openai_protocol = packy_protocol
        openai_api_url, openai_protocol = _normalize_openai_settings(openai_api_url, openai_protocol)
        return {
            "api_key": _first_non_empty(provider_config.get("api_key"), os.getenv("OPENAI_API_KEY", ""))
            if use_env_api_key
            else provider_config.get("api_key", ""),
            "api_url": openai_api_url,
            "model": _first_non_empty(provider_config.get("model"), os.getenv("OPENAI_MODEL", "")),
            "provider": _first_non_empty(
                provider_config.get("provider"),
                os.getenv("OPENAI_PROVIDER", DEFAULT_OPENAI_PROVIDER),
            ),
            "protocol": openai_protocol,
        }

    return {
        "api_key": _first_non_empty(provider_config.get("api_key"), os.getenv("PACKY_API_KEY", ""))
        if use_env_api_key
        else provider_config.get("api_key", ""),
        "api_url": _first_non_empty(provider_config.get("api_url"), os.getenv("PACKY_API_URL", DEFAULT_API_URL)),
        "model": _first_non_empty(provider_config.get("model"), os.getenv("PACKY_MODEL", DEFAULT_MODEL)),
        "provider": _first_non_empty(
            provider_config.get("provider"),
            os.getenv("PACKY_PROVIDER", DEFAULT_PRIMARY_PROVIDER),
        ),
        "protocol": _first_non_empty(provider_config.get("protocol"), os.getenv("PACKY_PROTOCOL", "")),
    }


def _coerce_priority(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _resolve_openai_routes(
    llm_config: dict | None,
    *,
    use_env_api_key: bool = True,
    allow_openai_url_fallback: bool = True,
) -> list[dict]:
    provider_config = ((llm_config or {}).get("openai") or {})
    base_settings = _resolve_provider_settings(
        "openai",
        llm_config,
        use_env_api_key=use_env_api_key,
        allow_openai_url_fallback=allow_openai_url_fallback,
    )
    raw_routes = provider_config.get("routes")
    if not isinstance(raw_routes, list) or not raw_routes:
        if any(base_settings.get(key) for key in ("api_key", "api_url", "model", "protocol")):
            raw_routes = [
                {
                    "alias": provider_config.get("model") or base_settings.get("model") or "openai-primary",
                    "enabled": provider_config.get("enabled", True),
                    "api_key": provider_config.get("api_key", ""),
                    "api_url": provider_config.get("api_url", "") or base_settings.get("api_url", ""),
                    "model": provider_config.get("model", "") or base_settings.get("model", ""),
                    "protocol": provider_config.get("protocol", "") or base_settings.get("protocol", ""),
                    "priority": 1,
                }
            ]
        else:
            raw_routes = []

    routes = []
    for index, raw_route in enumerate(raw_routes):
        route = raw_route or {}
        api_key = _first_non_empty(route.get("api_key"), base_settings.get("api_key", ""))
        api_url = _first_non_empty(route.get("api_url"), base_settings.get("api_url", ""))
        protocol = _first_non_empty(route.get("protocol"), base_settings.get("protocol", ""))
        api_url, protocol = _normalize_openai_settings(api_url, protocol)
        routes.append(
            {
                "api_key": api_key,
                "api_url": api_url,
                "model": _first_non_empty(route.get("model"), base_settings.get("model", "")),
                "provider": _first_non_empty(route.get("provider"), base_settings.get("provider", DEFAULT_OPENAI_PROVIDER)),
                "protocol": protocol,
                "route_alias": _first_non_empty(route.get("alias"), route.get("model"), f"openai-route-{index + 1}"),
                "priority": _coerce_priority(route.get("priority"), index + 1),
                "enabled": _normalize_provider_flag(route.get("enabled"), True),
            }
        )
    routes.sort(key=lambda item: (item.get("priority", 0), item.get("route_alias", "")))
    return routes


def _normalize_provider_flag(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _resolve_shared_reasoning_effort(llm_config: dict | None) -> str:
    return _first_non_empty((llm_config or {}).get("reasoning_effort"), os.getenv("PACKY_REASONING_EFFORT", ""))


def _resolve_shared_disable_response_storage(llm_config: dict | None) -> bool:
    override = (llm_config or {}).get("disable_response_storage")
    if isinstance(override, bool):
        return override
    if isinstance(override, str) and override.strip():
        return override.strip().lower() in {"1", "true", "yes", "on"}
    return _env_flag("PACKY_DISABLE_RESPONSE_STORAGE")


def _missing_api_key_name(llm_config: dict | None) -> str:
    return "OPENAI_API_KEY" if _resolve_active_provider(llm_config) == "openai" else "PACKY_API_KEY"


def _first_non_empty(*values):
    for value in values:
        if isinstance(value, str):
            if value.strip():
                return value.strip()
            continue
        if value is not None:
            return value
    return ""


def _safe_response_payload(response, *, settings: dict) -> dict:
    try:
        return response.json()
    except ValueError as exc:
        text = getattr(response, "text", "") or ""
        status_code = getattr(response, "status_code", None)
        if not text.strip():
            raise LLMRequestError(
                f"LLM gateway returned empty response body: url={settings.get('api_url', '')} model={settings.get('model', '')} status={status_code}",
                error_kind="llm_empty_response",
                provider=settings.get("provider", ""),
                model=settings.get("model", ""),
                status_code=status_code,
            ) from exc
        try:
            return _parse_json_with_repair(text)
        except ValueError:
            return {"output_text": text}


def _fallback_text(text: str, fallback_message: str, *, limit: int = 600) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        cleaned = fallback_message
    if len(cleaned) > limit:
        cleaned = f"{cleaned[:limit]}..."
    return cleaned


def _fallback_analysis_from_text(text: str) -> dict:
    summary = _fallback_text(text, "模型返回空响应，未能生成结构化分析。")
    return {
        "title_zh": "",
        "summary_zh": summary,
        "details_zh": "",
        "detail_sections": [],
        "what_changed": [],
        "new_technology": [],
        "behavior_changes": [],
        "config_changes": [],
        "code_change_focus": [],
        "docs_updates": [],
        "upgrade_risks": [],
        "future_direction": [],
        "evidence": [],
        "impact_scope": "",
        "impact_points": [],
        "suggested_action": "",
        "action_items": [],
        "urgency": "low",
        "tags": [],
        "is_stable": False,
        "analysis_mode": "fallback",
        "doc_summary": "",
        "doc_key_points": [],
        "changed_pages": [],
        "diff_highlights": [],
        "reading_guide": [],
    }


def parse_analysis_response(payload: dict[str, Any]) -> dict:
    text = _extract_text(payload)
    try:
        parsed = _parse_json_with_repair(text)
    except ValueError:
        return _fallback_analysis_from_text(text)
    title_zh = parsed.get("title_zh") or parsed.get("title") or ""
    summary_zh = parsed.get("summary_zh") or parsed.get("summary") or ""
    impact_scope = parsed.get("impact_scope") or ""
    suggested_action = parsed.get("suggested_action") or ""
    urgency = parsed.get("urgency") or "low"
    tags = parsed.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    doc_key_points = parsed.get("doc_key_points") or []
    if isinstance(doc_key_points, str):
        doc_key_points = [doc_key_points]
    diff_highlights = parsed.get("diff_highlights") or []
    if isinstance(diff_highlights, str):
        diff_highlights = [diff_highlights]
    reading_guide = parsed.get("reading_guide") or []
    if isinstance(reading_guide, str):
        reading_guide = [reading_guide]
    is_stable = parsed.get("is_stable")
    if is_stable is None:
        is_stable = True
    detail_sections = parsed.get("detail_sections") or _derive_detail_sections(parsed.get("details_zh", ""))
    impact_points = parsed.get("impact_points") or _split_inline_points(impact_scope)
    action_items = parsed.get("action_items") or _split_action_items(suggested_action)
    return {
        "title_zh": title_zh,
        "summary_zh": summary_zh,
        "details_zh": parsed.get("details_zh", ""),
        "detail_sections": detail_sections,
        "what_changed": parsed.get("what_changed", []),
        "new_technology": parsed.get("new_technology", []),
        "behavior_changes": parsed.get("behavior_changes", []),
        "config_changes": parsed.get("config_changes", []),
        "code_change_focus": parsed.get("code_change_focus", []),
        "docs_updates": parsed.get("docs_updates", []),
        "upgrade_risks": parsed.get("upgrade_risks", []),
        "future_direction": parsed.get("future_direction", []),
        "evidence": parsed.get("evidence", []),
        "impact_scope": impact_scope,
        "impact_points": impact_points,
        "suggested_action": suggested_action,
        "action_items": action_items,
        "urgency": urgency,
        "tags": tags,
        "is_stable": is_stable,
        "analysis_mode": parsed.get("analysis_mode") or "",
        "doc_summary": parsed.get("doc_summary") or "",
        "doc_key_points": doc_key_points,
        "changed_pages": parsed.get("changed_pages") or [],
        "diff_highlights": diff_highlights,
        "reading_guide": reading_guide,
    }


def parse_assistant_response(payload: dict[str, Any]) -> dict:
    text = _extract_text(payload)
    try:
        parsed = _parse_json_with_repair(text)
        return {
            "answer": parsed["answer"],
            "next_steps": parsed.get("next_steps", []),
        }
    except ValueError:
        return {
            "answer": _fallback_text(text, "模型返回空响应，无法生成回答。"),
            "next_steps": [],
        }


def parse_project_daily_summary_response(payload: dict[str, Any]) -> dict:
    text = _extract_text(payload)
    try:
        parsed = _parse_json_with_repair(text)
        return {
            "headline": parsed["headline"],
            "summary_zh": parsed["summary_zh"],
            "reason": parsed.get("reason", ""),
            "importance": parsed.get("importance", "medium"),
        }
    except ValueError:
        return {
            "headline": "",
            "summary_zh": _fallback_text(text, "模型返回空响应，无法生成日报摘要。"),
            "reason": "",
            "importance": "low",
        }


def parse_live_research_report_response(payload: dict[str, Any]) -> dict:
    text = _extract_text(payload)
    try:
        parsed = _parse_json_with_repair(text)
        return {
            "report_markdown": parsed["report_markdown"],
            "report_outline": parsed.get("report_outline", []),
            "next_steps": parsed.get("next_steps", []),
        }
    except ValueError:
        return {
            "report_markdown": _fallback_text(text, "模型返回空响应，无法生成研究报告。"),
            "report_outline": [],
            "next_steps": [],
        }


def _repair_unescaped_quotes(text: str) -> str:
    chars = []
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if char == '"' and not escaped:
            if not in_string:
                in_string = True
                chars.append(char)
                continue

            next_char = _next_non_space(text, index + 1)
            if next_char in {",", "}", "]", ":"}:
                in_string = False
                chars.append(char)
            else:
                chars.append('\\"')
            continue

        chars.append(char)
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False

    return "".join(chars)


def _extract_text(payload: dict[str, Any]) -> str:
    error_text = _extract_error_text(payload)
    if error_text:
        return error_text

    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return "\n".join(part.get("text", "") for part in content if isinstance(part, dict)).strip()

    output_items = payload.get("output")
    if isinstance(output_items, list):
        texts = []
        for item in output_items:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for part in item.get("content", []):
                if not isinstance(part, dict):
                    continue
                if part.get("type") in {"output_text", "text"}:
                    texts.append(part.get("text", ""))
        joined = "\n".join(text for text in texts if text).strip()
        if joined:
            return joined

    chunks = payload.get("content", [])
    text = "\n".join(chunk.get("text", "") for chunk in chunks if chunk.get("type") == "text").strip()
    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    if text.startswith("```"):
        text = text[len("```"):].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def _extract_error_text(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return ""
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message") or ""
        code = error.get("code") or error.get("type") or ""
        if isinstance(message, str) and message.strip():
            if isinstance(code, str) and code.strip():
                return f"{code}: {message}".strip()
            return message.strip()
    message = payload.get("message")
    code = payload.get("code")
    if isinstance(message, str) and message.strip():
        if isinstance(code, str) and code.strip():
            return f"{code}: {message}".strip()
        return message.strip()
    return ""


def _extract_json_block(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):].strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[len("```"):].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    brace_index = cleaned.find("{")
    bracket_index = cleaned.find("[")
    if brace_index == -1 and bracket_index == -1:
        return cleaned
    candidates = [index for index in (brace_index, bracket_index) if index != -1]
    start_index = min(candidates)
    if start_index == brace_index:
        end_index = cleaned.rfind("}")
    else:
        end_index = cleaned.rfind("]")
    if end_index != -1 and end_index > start_index:
        return cleaned[start_index : end_index + 1]
    return cleaned[start_index:]


def _sanitize_control_chars(text: str) -> str:
    cleaned = []
    for char in text:
        if char in {"\n", "\t"} or ord(char) >= 32:
            cleaned.append(char)
        else:
            cleaned.append(" ")
    return "".join(cleaned)


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def _balance_brackets(text: str) -> str:
    in_string = False
    escaped = False
    brace_count = 0
    bracket_count = 0

    for char in text:
        if char == '"' and not escaped:
            in_string = not in_string
        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            elif char == "[":
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False

    suffix = ""
    if in_string:
        suffix += '"'
    if bracket_count > 0:
        suffix += "]" * bracket_count
    if brace_count > 0:
        suffix += "}" * brace_count
    return text + suffix


def _prepare_json_text(text: str) -> str:
    text = _extract_json_block(text)
    text = _sanitize_control_chars(text)
    text = _remove_trailing_commas(text)
    text = _repair_unescaped_quotes(text)
    return text


def _parse_json_with_repair(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = _prepare_json_text(text)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            balanced = _balance_brackets(repaired)
            try:
                return json.loads(balanced)
            except json.JSONDecodeError as exc:
                excerpt = text.replace("\n", "\\n")
                if len(excerpt) > 400:
                    excerpt = f"{excerpt[:400]}..."
                raise ValueError(f"Failed to parse LLM JSON: {exc}. raw_excerpt='{excerpt}'") from exc


def _next_non_space(text: str, start: int) -> str:
    for char in text[start:]:
        if not char.isspace():
            return char
    return ""


def normalize_analysis_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["detail_sections"] = normalized.get("detail_sections") or _derive_detail_sections(normalized.get("details_zh", ""))
    normalized["impact_points"] = normalized.get("impact_points") or _split_inline_points(normalized.get("impact_scope", ""))
    normalized["action_items"] = normalized.get("action_items") or _split_action_items(normalized.get("suggested_action", ""))
    normalized["what_changed"] = normalized.get("what_changed") or []
    normalized["new_technology"] = normalized.get("new_technology") or []
    normalized["behavior_changes"] = normalized.get("behavior_changes") or []
    normalized["config_changes"] = normalized.get("config_changes") or []
    normalized["code_change_focus"] = normalized.get("code_change_focus") or []
    normalized["docs_updates"] = normalized.get("docs_updates") or []
    normalized["upgrade_risks"] = normalized.get("upgrade_risks") or []
    normalized["future_direction"] = normalized.get("future_direction") or []
    normalized["evidence"] = normalized.get("evidence") or []
    normalized["analysis_mode"] = normalized.get("analysis_mode") or ""
    normalized["doc_summary"] = normalized.get("doc_summary") or ""
    normalized["doc_key_points"] = normalized.get("doc_key_points") or []
    normalized["changed_pages"] = normalized.get("changed_pages") or []
    normalized["diff_highlights"] = normalized.get("diff_highlights") or []
    normalized["reading_guide"] = normalized.get("reading_guide") or []
    return normalized


def _derive_detail_sections(details_text: str) -> list[dict[str, list[str] | str]]:
    if not details_text.strip():
        return []

    sections = []
    current_title = "核心变化点"
    current_bullets: list[str] = []

    for raw_line in details_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        generic_heading = re.match(r"^\*\*(.+?)[:：]?\*\*$", line)
        numbered_section = re.match(r"^\d+\.\s+\*\*(.+?)\*\*$", line)
        bullet_match = re.match(r"^[-*•]\s+(.*)$", line)

        if generic_heading:
            heading = _clean_markdown_token(generic_heading.group(1))
            if heading and heading not in {"核心变化点"}:
                if current_bullets:
                    sections.append({"title": current_title, "bullets": current_bullets})
                current_title = heading
                current_bullets = []
            continue

        if numbered_section:
            if current_bullets:
                sections.append({"title": current_title, "bullets": current_bullets})
            current_title = _clean_markdown_token(numbered_section.group(1))
            current_bullets = []
            continue

        if bullet_match:
            current_bullets.append(_clean_markdown_token(bullet_match.group(1)))
            continue

        numbered_bullet = re.match(r"^\d+\.\s+(.*)$", line)
        if numbered_bullet:
            current_bullets.append(_clean_markdown_token(numbered_bullet.group(1)))
            continue

        current_bullets.append(_clean_markdown_token(line))

    if current_bullets:
        sections.append({"title": current_title, "bullets": current_bullets})

    return [section for section in sections if section["bullets"]]


def _split_inline_points(text: str) -> list[str]:
    if not text.strip():
        return []
    parts = re.split(r"[；;\n]+", text)
    return [_clean_markdown_token(part) for part in parts if _clean_markdown_token(part)]


def _split_action_items(text: str) -> list[str]:
    if not text.strip():
        return []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) == 1:
        lines = re.split(r"(?=\d+\.\s+)", lines[0])

    items = []
    for line in lines:
        cleaned = re.sub(r"^\d+\.\s*", "", line).strip()
        cleaned = _clean_markdown_token(cleaned)
        if cleaned:
            items.append(cleaned)
    return items


def _post_with_retry(*, settings: dict, payload: dict, max_attempts: int = 2):
    last_error = None
    for attempt in range(max_attempts):
        try:
            headers = {"content-type": "application/json"}
            if _use_openai_protocol(settings):
                headers["Authorization"] = f"Bearer {settings['api_key']}"
            else:
                headers["x-api-key"] = settings["api_key"]
                headers["anthropic-version"] = "2023-06-01"
            return requests.post(
                settings["api_url"],
                headers=headers,
                json=payload,
                timeout=60,
            )
        except requests.exceptions.ReadTimeout as exc:
            last_error = exc
            if attempt == max_attempts - 1:
                raise
            time.sleep(0.5)
    raise last_error


def _request_with_fallback(*, settings: dict, prompt: str, max_tokens: int):
    targets = _build_request_targets(settings)
    errors: list[LLMRequestError] = []

    for index, target in enumerate(targets):
        payload = _build_request_payload(settings=target, prompt=prompt, max_tokens=max_tokens)
        try:
            response = _post_with_retry(settings=target, payload=payload)
            _raise_for_status_with_context(response, target)
            metadata = {
                "provider": target["provider"],
                "model": target["model"],
                "api_url": target["api_url"],
                "route_alias": target.get("route_alias", ""),
                "used_fallback": index > 0,
            }
            if index > 0 and targets:
                primary_target = targets[0]
                metadata.update(
                    {
                        "fallback_from_provider": primary_target["provider"],
                        "fallback_from_model": primary_target["model"],
                        "fallback_from_route_alias": primary_target.get("route_alias", ""),
                        "fallback_reason": str(errors[0]) if errors else "",
                    }
                )
            return response, metadata
        except (LLMRequestError, requests.exceptions.RequestException) as exc:
            normalized = _normalize_llm_error(exc, target)
            errors.append(normalized)
            if index >= len(targets) - 1 or not _should_try_next_target(normalized):
                if len(errors) == 1:
                    raise normalized
                raise _combine_llm_errors(errors[0], normalized, targets[0], target)

    raise errors[-1]


def _build_request_targets(settings: dict) -> list[dict]:
    targets = []
    for target in settings.get("targets") or []:
        merged = dict(target)
        merged["reasoning_effort"] = settings.get("reasoning_effort", "")
        merged["disable_response_storage"] = settings.get("disable_response_storage", False)
        targets.append(merged)
    if targets:
        return targets

    primary_target = _build_target_settings(settings=settings)
    targets.append(primary_target)
    if settings.get("fallback_api_key") and settings.get("fallback_model"):
        targets.append(_build_target_settings(settings=settings, use_fallback=True))
    return targets


def _build_target_settings(*, settings: dict, use_fallback: bool = False) -> dict:
    if not use_fallback:
        return {
            "api_key": settings["api_key"],
            "api_url": settings["api_url"],
            "model": settings["model"],
            "provider": settings.get("provider", "primary-gateway"),
            "protocol": settings.get("protocol", ""),
            "route_alias": settings.get("route_alias", ""),
            "reasoning_effort": settings.get("reasoning_effort", ""),
            "disable_response_storage": settings.get("disable_response_storage", False),
        }

    return {
        "api_key": settings["fallback_api_key"],
        "api_url": settings["fallback_api_url"],
        "model": settings["fallback_model"],
        "provider": settings.get("fallback_provider", "fallback-provider"),
        "protocol": settings.get("fallback_protocol", ""),
        "route_alias": settings.get("fallback_route_alias", ""),
        "reasoning_effort": settings.get("reasoning_effort", ""),
        "disable_response_storage": settings.get("disable_response_storage", False),
    }


def _raise_for_status_with_context(response, settings: dict) -> None:
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        status_code = getattr(response, "status_code", "unknown")
        raise LLMRequestError(
            f"LLM gateway request failed: url={settings['api_url']} model={settings['model']} status={status_code}",
            provider=settings.get("provider", ""),
            model=settings.get("model", ""),
            api_url=settings.get("api_url", ""),
            route_alias=settings.get("route_alias", ""),
            status_code=status_code,
        ) from exc


def _use_openai_protocol(settings: dict) -> bool:
    protocol = (settings.get("protocol") or "").lower()
    if protocol in {"openai", "openai-chat", "responses", "openai-responses", "codex"}:
        return True
    api_url = settings.get("api_url", "")
    return "/v1/chat/completions" in api_url or "/v1/responses" in api_url


def _use_openai_responses_protocol(settings: dict) -> bool:
    protocol = (settings.get("protocol") or "").lower()
    if protocol in {"responses", "openai-responses", "codex"}:
        return True
    api_url = settings.get("api_url", "")
    return "/v1/responses" in api_url


def _build_request_payload(*, settings: dict, prompt: str, max_tokens: int) -> dict:
    if _use_openai_responses_protocol(settings):
        payload = {
            "model": settings["model"],
            "input": prompt,
            "max_output_tokens": max_tokens,
            "text": {"format": {"type": "text"}},
        }
        if settings.get("reasoning_effort"):
            payload["reasoning_effort"] = settings["reasoning_effort"]
        if settings.get("disable_response_storage"):
            payload["store"] = False
        return payload

    payload = {
        "model": settings["model"],
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }
    if _use_openai_protocol(settings):
        if settings.get("reasoning_effort"):
            payload["reasoning_effort"] = settings["reasoning_effort"]
        if settings.get("disable_response_storage"):
            payload["store"] = False
    return payload


def _env_flag(name: str) -> bool:
    value = (os.getenv(name) or "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _should_try_next_target(error: Exception) -> bool:
    if isinstance(error, LLMRequestError):
        if error.status_code in {429, "429"}:
            return True
        try:
            return int(error.status_code) >= 500
        except (TypeError, ValueError):
            return False
    return isinstance(
        error,
        (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ),
    )


def _normalize_llm_error(error: Exception, settings: dict) -> LLMRequestError:
    if isinstance(error, LLMRequestError):
        if error.provider and error.model and error.api_url:
            return error
        return LLMRequestError(
            str(error),
            error_kind=error.error_kind,
            provider=error.provider or settings.get("provider", ""),
            model=error.model or settings.get("model", ""),
            api_url=error.api_url or settings.get("api_url", ""),
            route_alias=error.route_alias or settings.get("route_alias", ""),
            status_code=error.status_code,
            used_fallback=error.used_fallback,
            fallback_provider=error.fallback_provider,
            fallback_model=error.fallback_model,
            fallback_route_alias=error.fallback_route_alias,
        )
    return LLMRequestError(
        f"LLM gateway request failed: url={settings['api_url']} model={settings['model']} error={error}",
        provider=settings.get("provider", ""),
        model=settings.get("model", ""),
        api_url=settings.get("api_url", ""),
        route_alias=settings.get("route_alias", ""),
    )


def _combine_llm_errors(primary_error: Exception, fallback_error: Exception, primary_settings: dict, fallback_settings: dict) -> LLMRequestError:
    primary = _normalize_llm_error(primary_error, primary_settings)
    fallback = _normalize_llm_error(fallback_error, fallback_settings)
    return LLMRequestError(
        f"主模型 {primary_settings.get('model', 'unknown')} 不可用（{primary}）；备用模型 {fallback_settings.get('model', 'unknown')} 也不可用（{fallback}）",
        provider=primary_settings.get("provider", ""),
        model=primary_settings.get("model", ""),
        api_url=primary_settings.get("api_url", ""),
        route_alias=primary_settings.get("route_alias", ""),
        status_code=getattr(primary, "status_code", None),
        used_fallback=True,
        fallback_provider=fallback_settings.get("provider", ""),
        fallback_model=fallback_settings.get("model", ""),
        fallback_route_alias=fallback_settings.get("route_alias", ""),
    )


def _clean_markdown_token(text: str) -> str:
    return text.replace("**", "").replace("__", "").strip(" :-")
