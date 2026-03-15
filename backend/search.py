import re
from html import unescape

import requests

RESULT_LINK_PATTERN = re.compile(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
RESULT_SNIPPET_PATTERN = re.compile(r'<div[^>]*class="result__snippet"[^>]*>(.*?)</div>', re.I | re.S)
TAG_PATTERN = re.compile(r"<[^>]+>")
MAIN_PATTERN = re.compile(r"<main[^>]*>(.*?)</main>", re.I | re.S)
ARTICLE_PATTERN = re.compile(r"<article[^>]*>(.*?)</article>", re.I | re.S)
REQUEST_TIMEOUT_SECONDS = 8


def search_web(query: str, max_results: int = 5) -> list[dict]:
    response = requests.get(
        "https://duckduckgo.com/html/",
        params={"q": query},
        headers={"user-agent": "Mozilla/5.0"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    html = response.text

    links = RESULT_LINK_PATTERN.findall(html)
    snippets = RESULT_SNIPPET_PATTERN.findall(html)

    results = []
    for index, (url, title_html) in enumerate(links[:max_results]):
        results.append(
            {
                "title": _html_to_text(title_html),
                "url": url,
                "snippet": _html_to_text(snippets[index]) if index < len(snippets) else "",
            }
        )
    return results


def fetch_search_result_pages(results: list[dict], max_pages: int = 3, max_chars: int = 2400) -> list[dict]:
    pages = []
    for result in results[:max_pages]:
        try:
            pages.append(fetch_page_content(result["url"], title=result["title"], max_chars=max_chars))
        except Exception:
            pages.append(
                {
                    "title": result["title"],
                    "url": result["url"],
                    "excerpt": result.get("snippet", ""),
                }
            )
    return pages


def fetch_page_content(url: str, title: str = "", max_chars: int = 2400) -> dict:
    response = requests.get(url, headers={"user-agent": "Mozilla/5.0"}, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return {
        "title": title,
        "url": url,
        "excerpt": _extract_primary_text(response.text)[:max_chars],
    }


def _extract_primary_text(html: str) -> str:
    for pattern in (MAIN_PATTERN, ARTICLE_PATTERN):
        match = pattern.search(html)
        if match:
            return _html_to_text(match.group(1))
    return _html_to_text(html)


def _html_to_text(text: str) -> str:
    cleaned = TAG_PATTERN.sub(" ", text)
    cleaned = unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()
