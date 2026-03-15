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


def get_llm_settings() -> dict:
    api_url = os.getenv("PACKY_API_URL", DEFAULT_API_URL)
    return {
        "api_key": os.getenv("PACKY_API_KEY", ""),
        "api_url": api_url,
        "model": os.getenv("PACKY_MODEL", DEFAULT_MODEL),
        "provider": os.getenv("PACKY_PROVIDER", "primary-gateway"),
        "protocol": os.getenv("PACKY_PROTOCOL", ""),
        "fallback_api_key": os.getenv("LLM_FALLBACK_API_KEY", ""),
        "fallback_api_url": os.getenv("LLM_FALLBACK_API_URL", api_url),
        "fallback_model": os.getenv("LLM_FALLBACK_MODEL", ""),
        "fallback_provider": os.getenv("LLM_FALLBACK_PROVIDER", "fallback-provider"),
    }


def analyze_event(event: dict) -> dict:
    settings = get_llm_settings()
    if not settings["api_key"]:
        raise RuntimeError("PACKY_API_KEY is not configured")

    response, llm_meta = _request_with_fallback(
        settings=settings,
        payload={
            "model": settings["model"],
            "max_tokens": 1200,
            "messages": [
                {
                    "role": "user",
                    "content": build_analysis_prompt(event),
                }
            ],
        },
    )
    analysis = parse_analysis_response(response.json())
    analysis["_llm"] = llm_meta
    return analysis


def answer_question_with_context(*, query: str, filters: dict, local_evidence: list[dict], web_results: list[dict], answer_prompt: str = "") -> dict:
    settings = get_llm_settings()
    if not settings["api_key"]:
        raise RuntimeError("PACKY_API_KEY is not configured")

    response, _llm_meta = _request_with_fallback(
        settings=settings,
        payload={
            "model": settings["model"],
            "max_tokens": 1400,
            "messages": [
                {
                    "role": "user",
                    "content": build_assistant_answer_prompt(
                        query=query,
                        filters=filters,
                        local_evidence=local_evidence,
                        web_results=web_results,
                        answer_prompt=answer_prompt,
                    ),
                }
            ],
        },
    )
    return parse_assistant_response(response.json())


def summarize_project_daily_intel(*, project: dict, evidence_items: list[dict], summary_date: str) -> dict:
    settings = get_llm_settings()
    if not settings["api_key"]:
        raise RuntimeError("PACKY_API_KEY is not configured")

    response, _llm_meta = _request_with_fallback(
        settings=settings,
        payload={
            "model": settings["model"],
            "max_tokens": 700,
            "messages": [
                {
                    "role": "user",
                    "content": build_project_daily_summary_prompt(
                        project=project,
                        evidence_items=evidence_items,
                        summary_date=summary_date,
                    ),
                }
            ],
        },
    )
    return parse_project_daily_summary_response(response.json())


def generate_live_research_report(*, query: str, filters: dict, plan: dict, evidence: list[dict], answer_prompt: str = "") -> dict:
    settings = get_llm_settings()
    if not settings["api_key"]:
        raise RuntimeError("PACKY_API_KEY is not configured")

    response, _llm_meta = _request_with_fallback(
        settings=settings,
        payload={
            "model": settings["model"],
            "max_tokens": 1800,
            "messages": [
                {
                    "role": "user",
                    "content": build_live_research_report_prompt(
                        query=query,
                        filters=filters,
                        plan=plan,
                        evidence=evidence,
                        answer_prompt=answer_prompt,
                    ),
                }
            ],
        },
    )
    return parse_live_research_report_response(response.json())


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
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return "\n".join(part.get("text", "") for part in content if isinstance(part, dict)).strip()

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


def _request_with_fallback(*, settings: dict, payload: dict):
    primary_settings = {
        "api_key": settings["api_key"],
        "api_url": settings["api_url"],
        "model": settings["model"],
        "provider": settings.get("provider", "primary-gateway"),
    }
    try:
        response = _post_with_retry(settings=primary_settings, payload=payload)
        _raise_for_status_with_context(response, primary_settings)
        return response, {
            "provider": primary_settings["provider"],
            "model": primary_settings["model"],
            "used_fallback": False,
        }
    except (LLMRequestError, requests.exceptions.RequestException) as primary_exc:
        if not _should_fallback(primary_exc, settings):
            raise _normalize_llm_error(primary_exc, primary_settings)

        fallback_settings = {
            "api_key": settings["fallback_api_key"],
            "api_url": settings["fallback_api_url"],
            "model": settings["fallback_model"],
            "provider": settings.get("fallback_provider", "fallback-provider"),
        }
        fallback_payload = dict(payload)
        fallback_payload["model"] = fallback_settings["model"]
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
    if protocol == "openai":
        return True
    api_url = settings.get("api_url", "")
    return "/v1/chat/completions" in api_url


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
