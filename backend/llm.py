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
        status_code: int | str | None = None,
        used_fallback: bool = False,
        fallback_provider: str = "",
        fallback_model: str = "",
    ):
        super().__init__(message)
        self.error_kind = error_kind
        self.provider = provider
        self.model = model
        self.status_code = status_code
        self.used_fallback = used_fallback
        self.fallback_provider = fallback_provider
        self.fallback_model = fallback_model


def get_llm_settings(llm_config: dict | None = None) -> dict:
    active_provider = _resolve_active_provider(llm_config)
    if not active_provider:
        raise RuntimeError("No LLM provider enabled")

    primary_settings = _resolve_provider_settings(active_provider, llm_config)
    fallback_provider_key = "openai" if active_provider == "packy" else "packy"
    if _is_provider_enabled(llm_config, fallback_provider_key):
        fallback_settings = _resolve_provider_settings(fallback_provider_key, llm_config)
        fallback_api_url = fallback_settings["api_url"] or primary_settings["api_url"]
    else:
        fallback_settings = _empty_provider_settings()
        fallback_api_url = ""

    return {
        "api_key": primary_settings["api_key"],
        "api_url": primary_settings["api_url"],
        "model": primary_settings["model"],
        "provider": primary_settings["provider"],
        "protocol": primary_settings["protocol"],
        "reasoning_effort": _resolve_shared_reasoning_effort(llm_config),
        "disable_response_storage": _resolve_shared_disable_response_storage(llm_config),
        "fallback_api_key": fallback_settings["api_key"],
        "fallback_api_url": fallback_api_url,
        "fallback_model": fallback_settings["model"],
        "fallback_provider": fallback_settings["provider"],
        "fallback_protocol": fallback_settings["protocol"] or (
            primary_settings["protocol"] if fallback_api_url == primary_settings["api_url"] else ""
        ),
    }


def build_llm_config_view(llm_config: dict | None = None) -> dict:
    llm_config = llm_config or {}
    packy_enabled = _is_provider_enabled(llm_config, "packy")
    openai_enabled = _is_provider_enabled(llm_config, "openai")
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
    openai_api_key_configured = openai_enabled and bool(_resolve_provider_settings("openai", llm_config)["api_key"])
    raw_packy = (llm_config.get("packy") or {})
    raw_openai = (llm_config.get("openai") or {})
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
        },
        "openai": {
            "enabled": openai_enabled,
            "api_key": raw_openai.get("api_key", "") if openai_enabled else "",
            "provider": openai_settings["provider"],
            "api_url": openai_settings["api_url"],
            "model": openai_settings["model"],
            "protocol": openai_settings["protocol"],
            "api_key_configured": openai_api_key_configured,
        },
    }


def analyze_event(event: dict, llm_config: dict | None = None) -> dict:
    settings = get_llm_settings(llm_config)
    if not settings["api_key"]:
        raise RuntimeError(f"{_missing_api_key_name(llm_config)} is not configured")

    response, llm_meta = _request_with_fallback(settings=settings, prompt=build_analysis_prompt(event), max_tokens=1200)
    analysis = parse_analysis_response(response.json())
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

    response, _llm_meta = _request_with_fallback(
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
    return parse_assistant_response(response.json())


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

    response, _llm_meta = _request_with_fallback(
        settings=settings,
        prompt=build_project_daily_summary_prompt(
            project=project,
            evidence_items=evidence_items,
            summary_date=summary_date,
        ),
        max_tokens=700,
    )
    return parse_project_daily_summary_response(response.json())


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

    response, _llm_meta = _request_with_fallback(
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
    return parse_live_research_report_response(response.json())


def _resolve_active_provider(llm_config: dict | None) -> str:
    provider = ((llm_config or {}).get("active_provider") or "").lower()
    if provider in {"packy", "openai"} and _is_provider_enabled(llm_config, provider):
        return provider
    if _is_provider_enabled(llm_config, "packy") and _resolve_provider_settings("packy", llm_config)["api_key"]:
        return "packy"
    if _is_provider_enabled(llm_config, "openai") and _resolve_provider_settings("openai", llm_config)["api_key"]:
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
    }


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


def parse_analysis_response(payload: dict[str, Any]) -> dict:
    text = _extract_text(payload)
    parsed = _parse_json_with_repair(text)
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
    parsed = _parse_json_with_repair(text)
    return {
        "answer": parsed["answer"],
        "next_steps": parsed.get("next_steps", []),
    }


def parse_project_daily_summary_response(payload: dict[str, Any]) -> dict:
    text = _extract_text(payload)
    parsed = _parse_json_with_repair(text)
    return {
        "headline": parsed["headline"],
        "summary_zh": parsed["summary_zh"],
        "reason": parsed.get("reason", ""),
        "importance": parsed.get("importance", "medium"),
    }


def parse_live_research_report_response(payload: dict[str, Any]) -> dict:
    text = _extract_text(payload)
    parsed = _parse_json_with_repair(text)
    return {
        "report_markdown": parsed["report_markdown"],
        "report_outline": parsed.get("report_outline", []),
        "next_steps": parsed.get("next_steps", []),
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
    primary_settings = _build_target_settings(settings=settings)
    primary_payload = _build_request_payload(settings=primary_settings, prompt=prompt, max_tokens=max_tokens)
    try:
        response = _post_with_retry(settings=primary_settings, payload=primary_payload)
        _raise_for_status_with_context(response, primary_settings)
        return response, {
            "provider": primary_settings["provider"],
            "model": primary_settings["model"],
            "used_fallback": False,
        }
    except (LLMRequestError, requests.exceptions.RequestException) as primary_exc:
        if not _should_fallback(primary_exc, settings):
            raise _normalize_llm_error(primary_exc, primary_settings)

        fallback_settings = _build_target_settings(settings=settings, use_fallback=True)
        fallback_payload = _build_request_payload(settings=fallback_settings, prompt=prompt, max_tokens=max_tokens)
        try:
            response = _post_with_retry(settings=fallback_settings, payload=fallback_payload)
            _raise_for_status_with_context(response, fallback_settings)
            return response, {
                "provider": fallback_settings["provider"],
                "model": fallback_settings["model"],
                "used_fallback": True,
                "fallback_from_provider": primary_settings["provider"],
                "fallback_from_model": primary_settings["model"],
                "fallback_reason": str(primary_exc),
            }
        except (LLMRequestError, requests.exceptions.RequestException) as fallback_exc:
            raise _combine_llm_errors(primary_exc, fallback_exc, primary_settings, fallback_settings)


def _build_target_settings(*, settings: dict, use_fallback: bool = False) -> dict:
    if not use_fallback:
        return {
            "api_key": settings["api_key"],
            "api_url": settings["api_url"],
            "model": settings["model"],
            "provider": settings.get("provider", "primary-gateway"),
            "protocol": settings.get("protocol", ""),
            "reasoning_effort": settings.get("reasoning_effort", ""),
            "disable_response_storage": settings.get("disable_response_storage", False),
        }

    return {
        "api_key": settings["fallback_api_key"],
        "api_url": settings["fallback_api_url"],
        "model": settings["fallback_model"],
        "provider": settings.get("fallback_provider", "fallback-provider"),
        "protocol": settings.get("fallback_protocol", ""),
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
            status_code=status_code,
        ) from exc


def _use_openai_protocol(settings: dict) -> bool:
    protocol = (settings.get("protocol") or "").lower()
    if protocol in {"openai", "openai-chat", "responses", "openai-responses"}:
        return True
    api_url = settings.get("api_url", "")
    return "/v1/chat/completions" in api_url or "/v1/responses" in api_url


def _use_openai_responses_protocol(settings: dict) -> bool:
    protocol = (settings.get("protocol") or "").lower()
    if protocol in {"responses", "openai-responses"}:
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


def _should_fallback(error: Exception, settings: dict) -> bool:
    if not settings.get("fallback_api_key") or not settings.get("fallback_model"):
        return False
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
        return error
    return LLMRequestError(
        f"LLM gateway request failed: url={settings['api_url']} model={settings['model']} error={error}",
        provider=settings.get("provider", ""),
        model=settings.get("model", ""),
    )


def _combine_llm_errors(primary_error: Exception, fallback_error: Exception, primary_settings: dict, fallback_settings: dict) -> LLMRequestError:
    fallback = _normalize_llm_error(fallback_error, fallback_settings)
    return LLMRequestError(
        f"{primary_error}; fallback failed: {fallback}",
        provider=primary_settings.get("provider", ""),
        model=primary_settings.get("model", ""),
        status_code=getattr(primary_error, "status_code", None),
        used_fallback=True,
        fallback_provider=fallback_settings.get("provider", ""),
        fallback_model=fallback_settings.get("model", ""),
    )


def _clean_markdown_token(text: str) -> str:
    return text.replace("**", "").replace("__", "").strip(" :-")
