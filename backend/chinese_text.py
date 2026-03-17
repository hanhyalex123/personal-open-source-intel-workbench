import re

EMPTY_ANALYSIS_SUMMARY = "模型返回空响应，未能生成结构化分析。"
EMPTY_DAILY_SUMMARY = "模型返回空响应，无法生成日报摘要。"

_CHINESE_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def has_usable_chinese_text(value: str | None) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text or text == EMPTY_ANALYSIS_SUMMARY or text == EMPTY_DAILY_SUMMARY:
        return False
    return bool(_CHINESE_RE.search(text))


def prefer_chinese_text(*values: str | None, fallback: str = "") -> str:
    for value in values:
        if has_usable_chinese_text(value):
            return value.strip()
    return fallback


def sanitize_chinese_list(values: list | None, fallback: str) -> list[str]:
    cleaned: list[str] = []
    for value in values or []:
        if has_usable_chinese_text(value):
            cleaned.append(value.strip())
    return cleaned or [fallback]


def docs_event_title(project_name: str, event_kind: str) -> str:
    if event_kind == "docs_initial_read":
        return f"{project_name} 文档首读"
    return f"{project_name} 文档更新"


def generic_event_title(project_name: str, source: str, event_kind: str = "") -> str:
    if source == "docs_feed":
        return docs_event_title(project_name, event_kind)
    if source == "github_release":
        return f"{project_name} 版本更新"
    return f"{project_name} 项目更新"
