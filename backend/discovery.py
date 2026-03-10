import json
from urllib.parse import urlparse

import requests


DEFAULT_CATEGORY_HINTS = ["网络", "存储", "调度", "架构", "安全", "升级", "运行时", "可观测性"]


def build_discovery_prompt(*, project: dict, homepage_excerpt: str) -> str:
    return f"""You are a documentation discovery agent.

Generate a crawl profile for the following project docs homepage.

Return JSON only with these fields:
- entry_urls
- allowed_path_prefixes
- blocked_path_prefixes
- max_depth
- max_pages
- expand_mode
- category_hints
- discovery_prompt
- classification_prompt

Project: {project.get("name")}
Docs URL: {project.get("docs_url")}
Homepage excerpt:
{homepage_excerpt[:2500]}
"""


def parse_discovery_response(text: str) -> dict:
    parsed = json.loads(text)
    return {
        "entry_urls": parsed["entry_urls"],
        "allowed_path_prefixes": parsed["allowed_path_prefixes"],
        "blocked_path_prefixes": parsed["blocked_path_prefixes"],
        "max_depth": parsed["max_depth"],
        "max_pages": parsed["max_pages"],
        "expand_mode": parsed["expand_mode"],
        "category_hints": parsed["category_hints"],
        "discovery_prompt": parsed["discovery_prompt"],
        "classification_prompt": parsed["classification_prompt"],
    }


def build_profile_from_homepage(*, docs_url: str, homepage_excerpt: str) -> dict:
    parsed = urlparse(docs_url)
    path = parsed.path.rstrip("/") or "/"
    prefix = path
    if path.endswith("/home"):
        prefix = path[: -len("/home")] or "/"
    hints = [hint for hint in DEFAULT_CATEGORY_HINTS if hint in homepage_excerpt]
    return {
        "entry_urls": [docs_url],
        "allowed_path_prefixes": [prefix],
        "blocked_path_prefixes": [f"{prefix}/_print"] if prefix != "/" else ["/_print"],
        "max_depth": 3,
        "max_pages": 40,
        "expand_mode": "auto",
        "category_hints": hints or DEFAULT_CATEGORY_HINTS[:4],
        "discovery_prompt": "",
        "classification_prompt": "",
    }


def generate_crawl_profile(project: dict) -> dict:
    docs_url = project.get("docs_url", "")
    if not docs_url:
        return build_profile_from_homepage(docs_url="", homepage_excerpt="")

    response = requests.get(docs_url, timeout=30)
    response.raise_for_status()
    excerpt = response.text[:12000]
    return build_profile_from_homepage(docs_url=docs_url, homepage_excerpt=excerpt)
