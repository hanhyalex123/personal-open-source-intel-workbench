class DummyResponse:
    def __init__(self, payload=None, text="", status_code=200):
        self._payload = payload
        self.text = text
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


def test_fetch_github_releases_uses_repo_api(monkeypatch):
    from backend.sources import fetch_github_releases

    calls = []

    def fake_get(url, headers=None, timeout=None):
        calls.append({"url": url, "headers": headers, "timeout": timeout})
        return DummyResponse(payload=[{"tag_name": "v1.31.0"}])

    monkeypatch.setattr("backend.sources.requests.get", fake_get)

    payload = fetch_github_releases("kubernetes/kubernetes")

    assert calls[0]["url"].endswith("/repos/kubernetes/kubernetes/releases?per_page=6")
    assert payload[0]["tag_name"] == "v1.31.0"


def test_fetch_github_releases_expands_github_changelog_link(monkeypatch):
    from backend.sources import fetch_github_releases

    calls = []

    def fake_get(url, headers=None, timeout=None):
        calls.append(url)
        if "api.github.com" in url:
            return DummyResponse(
                payload=[
                    {
                        "tag_name": "v1.31.0",
                        "body": "See the [CHANGELOG](https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.31.md).",
                    }
                ]
            )
        return DummyResponse(text="nftables recommended in 1.31")

    monkeypatch.setattr("backend.sources.requests.get", fake_get)

    payload = fetch_github_releases("kubernetes/kubernetes")

    assert any("raw.githubusercontent.com" in call for call in calls)
    assert "nftables recommended in 1.31" in payload[0]["body"]


def test_fetch_github_releases_reports_request_and_item_progress(monkeypatch):
    from backend.sources import fetch_github_releases

    progress = []

    def fake_get(url, headers=None, timeout=None):
        return DummyResponse(
            payload=[
                {"tag_name": "v1.31.0", "body": ""},
                {"tag_name": "v1.31.1", "body": ""},
            ]
        )

    monkeypatch.setattr("backend.sources.requests.get", fake_get)

    payload = fetch_github_releases(
        "kubernetes/kubernetes",
        progress_callback=lambda **item: progress.append(item),
    )

    assert len(payload) == 2
    assert progress == [
        {"stage": "requesting"},
        {"stage": "processing", "processed_items": 1, "total_items": 2},
        {"stage": "processing", "processed_items": 2, "total_items": 2},
    ]


def test_fetch_feed_entries_parses_feed(monkeypatch):
    from backend.sources import fetch_feed_entries

    def fake_get(url, timeout):
        assert url == "https://example.com/feed.atom"
        return DummyResponse(text="<feed />")

    def fake_parse(text):
        assert text == "<feed />"
        return {
            "entries": [
                {
                    "id": "entry-1",
                    "title": "Recommend nftables mode",
                    "link": "https://example.com/entry-1",
                    "published": "2026-03-09T00:00:00Z",
                    "summary": "docs changed",
                }
            ]
        }

    monkeypatch.setattr("backend.sources.requests.get", fake_get)
    monkeypatch.setattr("backend.sources.feedparser.parse", fake_parse)

    entries = fetch_feed_entries({"id": "k8s-docs", "url": "https://example.com/feed.atom"})

    assert entries[0]["title"] == "Recommend nftables mode"
    assert entries[0]["summary"] == "docs changed"


def test_fetch_feed_entries_expands_linked_page_for_official_blog(monkeypatch):
    from backend.sources import fetch_feed_entries

    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        if url == "https://example.com/feed.xml":
            return DummyResponse(text="<feed />")
        return DummyResponse(
            text="<html><body><article><h1>NFTables mode for kube-proxy</h1><p>In Kubernetes 1.31, nftables backend became available.</p></article></body></html>"
        )

    def fake_parse(_text):
        return {
            "entries": [
                {
                    "id": "blog-1",
                    "title": "NFTables mode for kube-proxy",
                    "link": "https://example.com/blog/nftables",
                    "published": "2026-03-01T00:00:00Z",
                    "summary": "blog summary",
                }
            ]
        }

    monkeypatch.setattr("backend.sources.requests.get", fake_get)
    monkeypatch.setattr("backend.sources.feedparser.parse", fake_parse)

    entries = fetch_feed_entries(
        {
            "id": "k8s-blog",
            "url": "https://example.com/feed.xml",
            "expand_links": True,
        }
    )

    assert "https://example.com/blog/nftables" in calls
    assert "nftables backend became available" in entries[0]["summary"].lower()


def test_fetch_feed_entries_supports_page_sources(monkeypatch):
    from backend.sources import fetch_feed_entries

    monkeypatch.setattr(
        "backend.sources.crawl_docs_pages",
        lambda **kwargs: [
            {
                "url": "https://kubernetes.io/zh-cn/docs/home/",
                "title": "Kubernetes 中文文档首页",
                "body": "Kubernetes 文档 这里介绍 Kubernetes 文档首页。",
                "last_seen_at": "Mon, 09 Mar 2026 10:00:00 GMT",
                "category": "架构",
            },
            {
                "url": "https://kubernetes.io/zh-cn/docs/concepts/services-networking/",
                "title": "服务与网络",
                "body": "CNI kube-proxy nftables",
                "last_seen_at": "Mon, 09 Mar 2026 10:00:00 GMT",
                "category": "网络",
            },
        ],
    )

    entries = fetch_feed_entries(
        {
            "id": "k8s-zh-docs-home",
            "project_id": "kubernetes",
            "name": "Kubernetes 中文文档首页",
            "url": "https://kubernetes.io/zh-cn/docs/home/",
            "type": "page",
            "allowed_path_prefixes": ["/zh-cn/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 2,
        }
    )

    assert len(entries) == 2
    assert entries[0]["id"] == "https://kubernetes.io/zh-cn/docs/home/#架构"
    assert entries[1]["category"] == "网络"
    assert entries[1]["research_bundle"]["category"] == "网络"


def test_fetch_feed_entries_for_page_sources_reports_crawl_progress(monkeypatch):
    from backend.sources import fetch_feed_entries

    progress = []

    def fake_crawl_docs_pages(**kwargs):
        kwargs["progress_callback"](current_url="https://example.com/docs", processed_pages=1, max_pages=40)
        kwargs["progress_callback"](current_url="https://example.com/docs/network", processed_pages=2, max_pages=40)
        return [
            {
                "url": "https://example.com/docs/network",
                "title": "服务与网络",
                "body": "CNI kube-proxy nftables",
                "last_seen_at": "Mon, 09 Mar 2026 10:00:00 GMT",
                "category": "网络",
            }
        ]

    monkeypatch.setattr("backend.sources.crawl_docs_pages", fake_crawl_docs_pages)

    fetch_feed_entries(
        {
            "id": "k8s-zh-docs-home",
            "project_id": "kubernetes",
            "name": "Kubernetes 中文文档首页",
            "url": "https://example.com/docs",
            "type": "page",
        },
        progress_callback=lambda **payload: progress.append(payload),
    )

    assert progress == [
        {"current_url": "https://example.com/docs", "processed_pages": 1, "max_pages": 40},
        {"current_url": "https://example.com/docs/network", "processed_pages": 2, "max_pages": 40},
    ]
