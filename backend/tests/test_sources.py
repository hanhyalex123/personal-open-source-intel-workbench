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
        lambda **kwargs: {
            "records": [
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
            "crawl_complete": True,
            "incomplete_reasons": [],
        },
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
    assert all(entry["event_kind"] == "docs_initial_read" for entry in entries)
    assert entries[1]["category"] == "网络"
    assert entries[1]["research_bundle"]["category"] == "网络"
    assert entries[1]["research_bundle"]["analysis_mode"] == "initial_read"


def test_fetch_feed_entries_for_page_sources_reports_crawl_progress(monkeypatch):
    from backend.sources import fetch_feed_entries

    progress = []

    def fake_crawl_docs_pages(**kwargs):
        kwargs["progress_callback"](current_url="https://example.com/docs", processed_pages=1, max_pages=40)
        kwargs["progress_callback"](current_url="https://example.com/docs/network", processed_pages=2, max_pages=40)
        return {
            "records": [
                {
                    "url": "https://example.com/docs/network",
                    "title": "服务与网络",
                    "body": "CNI kube-proxy nftables",
                    "last_seen_at": "Mon, 09 Mar 2026 10:00:00 GMT",
                    "category": "网络",
                }
            ],
            "crawl_complete": True,
            "incomplete_reasons": [],
        }

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


def test_fetch_feed_entries_builds_diff_updates_when_snapshot_exists(tmp_path, monkeypatch):
    from backend.sources import fetch_feed_entries
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_docs_snapshots(
        {
            "kubernetes": {
                "project_id": "kubernetes",
                "source_key": "k8s-zh-docs-home",
                "updated_at": "2026-03-09T10:00:00Z",
                "pages": {
                    "https://example.com/docs/network": {
                        "id": "network-page",
                        "url": "https://example.com/docs/network",
                        "path": "/docs/network",
                        "title": "网络",
                        "category": "网络",
                        "text_content": "旧内容",
                        "summary": "旧内容",
                        "headings": ["网络"],
                        "breadcrumbs": ["文档", "网络"],
                        "content_hash": "old-content",
                        "page_hash": "old-page",
                        "last_seen_at": "2026-03-09T10:00:00Z",
                    }
                },
            }
        }
    )

    monkeypatch.setattr(
        "backend.sources.crawl_docs_pages",
        lambda **kwargs: {
            "records": [
                {
                    "id": "network-page",
                    "url": "https://example.com/docs/network",
                    "path": "/docs/network",
                    "title": "网络",
                    "body": "新内容\n\n加入 nftables 推荐。",
                    "text_content": "新内容\n\n加入 nftables 推荐。",
                    "headings": ["网络", "代理模式"],
                    "breadcrumbs": ["文档", "网络"],
                    "last_seen_at": "2026-03-10T10:00:00Z",
                    "content_hash": "new-content",
                    "page_hash": "new-page",
                    "category": "网络",
                }
            ],
            "crawl_complete": True,
            "incomplete_reasons": [],
        },
    )

    entries = fetch_feed_entries(
        {
            "id": "k8s-zh-docs-home",
            "project_id": "kubernetes",
            "name": "Kubernetes 中文文档首页",
            "url": "https://example.com/docs",
            "type": "page",
        },
        store=store,
    )

    assert len(entries) == 1
    assert entries[0]["event_kind"] == "docs_diff_update"
    assert entries[0]["research_bundle"]["analysis_mode"] == "diff_update"
    assert entries[0]["research_bundle"]["changed_pages"][0]["change_type"] == "changed"


def test_fetch_feed_entries_skips_partial_page_snapshots(tmp_path, monkeypatch):
    from backend.sources import fetch_feed_entries
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_docs_snapshots(
        {
            "kubernetes": {
                "project_id": "kubernetes",
                "source_key": "k8s-zh-docs-home",
                "updated_at": "2026-03-09T10:00:00Z",
                "pages": {
                    "https://example.com/docs/network": {
                        "id": "network-page",
                        "url": "https://example.com/docs/network",
                        "path": "/docs/network",
                        "title": "网络",
                        "category": "网络",
                        "text_content": "旧内容",
                        "summary": "旧内容",
                        "content_hash": "old-content",
                        "page_hash": "old-page",
                        "last_seen_at": "2026-03-09T10:00:00Z",
                    }
                },
            }
        }
    )

    monkeypatch.setattr(
        "backend.sources.crawl_docs_pages",
        lambda **kwargs: {
            "records": [
                {
                    "id": "network-page",
                    "url": "https://example.com/docs/network",
                    "path": "/docs/network",
                    "title": "网络",
                    "body": "只抓到一部分内容",
                    "text_content": "只抓到一部分内容",
                    "headings": ["网络"],
                    "breadcrumbs": ["文档", "网络"],
                    "last_seen_at": "2026-03-10T10:00:00Z",
                    "content_hash": "new-content",
                    "page_hash": "new-page",
                    "category": "网络",
                }
            ],
            "crawl_complete": False,
            "incomplete_reasons": ["request_failed:https://example.com/docs/storage"],
        },
    )

    entries = fetch_feed_entries(
        {
            "id": "k8s-zh-docs-home",
            "project_id": "kubernetes",
            "name": "Kubernetes 中文文档首页",
            "url": "https://example.com/docs",
            "type": "page",
        },
        store=store,
    )

    assert entries == []


def test_fetch_feed_entries_without_initial_read_builds_baseline_without_diff_events(tmp_path, monkeypatch):
    from backend.sources import fetch_feed_entries
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)

    monkeypatch.setattr(
        "backend.sources.crawl_docs_pages",
        lambda **kwargs: {
            "records": [
                {
                    "id": "network-page",
                    "url": "https://example.com/docs/network",
                    "path": "/docs/network",
                    "title": "网络",
                    "body": "首次抓取内容",
                    "text_content": "首次抓取内容",
                    "headings": ["网络"],
                    "breadcrumbs": ["文档", "网络"],
                    "last_seen_at": "2026-03-10T10:00:00Z",
                    "content_hash": "baseline-content",
                    "page_hash": "baseline-page",
                    "category": "网络",
                }
            ],
            "crawl_complete": True,
            "incomplete_reasons": [],
        },
    )

    entries = fetch_feed_entries(
        {
            "id": "k8s-zh-docs-home",
            "project_id": "kubernetes",
            "name": "Kubernetes 中文文档首页",
            "url": "https://example.com/docs",
            "type": "page",
            "initial_read_enabled": False,
        },
        store=store,
    )

    assert entries == []
    assert entries.docs_snapshot_payload["project_id"] == "kubernetes"
    assert entries.docs_snapshot_payload["pages"]["https://example.com/docs/network"]["id"] == "network-page"
