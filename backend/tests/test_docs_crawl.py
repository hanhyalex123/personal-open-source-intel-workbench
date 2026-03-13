def test_crawl_docs_pages_follows_allowed_internal_links(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    pages = {
        "https://example.com/docs": """
            <html><body>
              <main>
                <h1>Docs Home</h1>
                <a href="/docs/network">Network</a>
                <a href="/docs/storage">Storage</a>
                <a href="/blog/post">Blog</a>
              </main>
            </body></html>
        """,
        "https://example.com/docs/network": """
            <html><body><main><h1>Network</h1><p>kube-proxy nftables and CNI.</p></main></body></html>
        """,
        "https://example.com/docs/storage": """
            <html><body><main><h1>Storage</h1><p>CSI snapshots and volume provisioning.</p></main></body></html>
        """,
    }

    class DummyResponse:
        def __init__(self, text):
            self.text = text
            self.headers = {"Last-Modified": "Mon, 09 Mar 2026 10:00:00 GMT"}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "backend.docs_crawl.requests.get",
        lambda url, timeout=30: DummyResponse(pages[url]),
    )

    records = crawl_docs_pages(
        project_id="kubernetes",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": ["/blog"],
            "max_depth": 2,
        },
    )

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/network",
        "https://example.com/docs/storage",
    ]
    assert records[1]["title"] == "Network"
    assert "nftables" in records[1]["body"].lower()


def test_crawl_docs_pages_respects_depth_limit(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    pages = {
        "https://example.com/docs": '<a href="/docs/a">A</a>',
        "https://example.com/docs/a": '<a href="/docs/b">B</a>',
        "https://example.com/docs/b": "<main><h1>B</h1><p>Deep page</p></main>",
    }

    class DummyResponse:
        def __init__(self, text):
            self.text = text
            self.headers = {}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "backend.docs_crawl.requests.get",
        lambda url, timeout=30: DummyResponse(pages[url]),
    )

    records = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 1,
        },
    )

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/a",
    ]


def test_crawl_docs_pages_extracts_unquoted_href_links(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    pages = {
        "https://example.com/docs": "<a href=/docs/network>Network</a>",
        "https://example.com/docs/network": "<main><h1>Network</h1><p>nftables</p></main>",
    }

    class DummyResponse:
        def __init__(self, text):
            self.text = text
            self.headers = {}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "backend.docs_crawl.requests.get",
        lambda url, timeout=30: DummyResponse(pages[url]),
    )

    records = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 2,
        },
    )

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/network",
    ]


def test_crawl_docs_pages_prefers_shallow_links_first(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    pages = {
        "https://example.com/docs": """
            <a href="/docs/setup/deep-a">Deep A</a>
            <a href="/docs/concepts">Concepts</a>
            <a href="/docs/tasks">Tasks</a>
        """,
        "https://example.com/docs/concepts": "<main><h1>Concepts</h1></main>",
        "https://example.com/docs/tasks": "<main><h1>Tasks</h1></main>",
        "https://example.com/docs/setup/deep-a": "<main><h1>Deep A</h1></main>",
    }

    class DummyResponse:
        def __init__(self, text):
            self.text = text
            self.headers = {}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "backend.docs_crawl.requests.get",
        lambda url, timeout=30: DummyResponse(pages[url]),
    )

    records = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 1,
            "max_pages": 3,
        },
    )

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/concepts",
        "https://example.com/docs/tasks",
    ]


def test_crawl_docs_pages_extracts_main_content_without_nav_noise(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    html = """
      <html><body>
        <nav>services-networking storage class gateway api</nav>
        <main>
          <h1>Storage Concepts</h1>
          <p>CSI volume snapshot provisioning</p>
        </main>
      </body></html>
    """

    class DummyResponse:
        def __init__(self, text):
            self.text = text
            self.headers = {}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "backend.docs_crawl.requests.get",
        lambda url, timeout=30: DummyResponse(html),
    )

    records = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 0,
            "max_pages": 1,
        },
    )

    assert records[0]["body"] == "Storage Concepts CSI volume snapshot provisioning"


def test_crawl_docs_pages_reports_progress_per_page(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    pages = {
        "https://example.com/docs": '<main><h1>Docs</h1><a href="/docs/a">A</a></main>',
        "https://example.com/docs/a": "<main><h1>A</h1><p>alpha</p></main>",
    }
    progress = []

    class DummyResponse:
        def __init__(self, text):
            self.text = text
            self.headers = {}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "backend.docs_crawl.requests.get",
        lambda url, timeout=30: DummyResponse(pages[url]),
    )

    crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 1,
        },
        progress_callback=lambda **payload: progress.append(payload),
    )

    assert [item["current_url"] for item in progress] == [
        "https://example.com/docs",
        "https://example.com/docs/a",
    ]
    assert progress[-1]["processed_pages"] == 2


def test_crawl_docs_pages_skips_unreachable_pages(monkeypatch):
    import requests
    from backend.docs_crawl import crawl_docs_pages

    pages = {
        "https://example.com/docs": '<main><h1>Docs</h1><a href="/docs/good">Good</a><a href="/docs/bad">Bad</a></main>',
        "https://example.com/docs/good": "<main><h1>Good</h1><p>ok</p></main>",
    }

    class DummyResponse:
        def __init__(self, text):
            self.text = text
            self.headers = {}

        def raise_for_status(self):
            return None

    def fake_get(url, timeout=30):
        if url == "https://example.com/docs/bad":
            raise requests.HTTPError("404 Client Error: Not Found for url")
        return DummyResponse(pages[url])

    monkeypatch.setattr("backend.docs_crawl.requests.get", fake_get)

    records = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 1,
        },
    )

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/good",
    ]
