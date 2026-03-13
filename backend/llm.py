import json
import os
import re
import time
from typing import Any

import requests

from .prompts import build_analysis_prompt, build_assistant_answer_prompt, build_project_daily_summary_prompt


DEFAULT_API_URL = "https://www.packyapi.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"


def get_llm_settings() -> dict:
    return {
        "api_key": os.getenv("PACKY_API_KEY", ""),
        "api_url": os.getenv("PACKY_API_URL", DEFAULT_API_URL),
        "model": os.getenv("PACKY_MODEL", DEFAULT_MODEL),
    }


def analyze_event(event: dict) -> dict:
    settings = get_llm_settings()
    if not settings["api_key"]:
        raise RuntimeError("PACKY_API_KEY is not configured")

    response = _post_with_retry(
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
    response.raise_for_status()
    return parse_analysis_response(response.json())


def answer_question_with_context(*, query: str, filters: dict, local_evidence: list[dict], web_results: list[dict], answer_prompt: str = "") -> dict:
    settings = get_llm_settings()
    if not settings["api_key"]:
        raise RuntimeError("PACKY_API_KEY is not configured")

    response = _post_with_retry(
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
    response.raise_for_status()
    return parse_assistant_response(response.json())


def summarize_project_daily_intel(*, project: dict, evidence_items: list[dict], summary_date: str) -> dict:
    settings = get_llm_settings()
    if not settings["api_key"]:
        raise RuntimeError("PACKY_API_KEY is not configured")

    response = _post_with_retry(
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
    response.raise_for_status()
    return parse_project_daily_summary_response(response.json())


def parse_analysis_response(payload: dict[str, Any]) -> dict:
    text = _extract_text(payload)
    parsed = _parse_json_with_repair(text)
    detail_sections = parsed.get("detail_sections") or _derive_detail_sections(parsed.get("details_zh", ""))
    impact_points = parsed.get("impact_points") or _split_inline_points(parsed.get("impact_scope", ""))
    action_items = parsed.get("action_items") or _split_action_items(parsed.get("suggested_action", ""))
    return {
        "title_zh": parsed["title_zh"],
        "summary_zh": parsed["summary_zh"],
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
        "impact_scope": parsed["impact_scope"],
        "impact_points": impact_points,
        "suggested_action": parsed["suggested_action"],
        "action_items": action_items,
        "urgency": parsed["urgency"],
        "tags": parsed["tags"],
        "is_stable": parsed["is_stable"],
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
            return requests.post(
                settings["api_url"],
                headers={
                    "content-type": "application/json",
                    "x-api-key": settings["api_key"],
                    "anthropic-version": "2023-06-01",
                },
                json=payload,
                timeout=60,
            )
        except requests.exceptions.ReadTimeout as exc:
            last_error = exc
            if attempt == max_attempts - 1:
                raise
            time.sleep(0.5)
    raise last_error


def _clean_markdown_token(text: str) -> str:
    return text.replace("**", "").replace("__", "").strip(" :-")
