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

    result = crawl_docs_pages(
        project_id="kubernetes",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": ["/blog"],
            "max_depth": 2,
        },
    )
    records = result["records"]

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/network",
        "https://example.com/docs/storage",
    ]
    assert result["crawl_complete"] is True
    assert records[1]["title"] == "Network"
    assert "nftables" in records[1]["body"].lower()
    assert records[1]["extractor_hint"] == "html-main"
    assert records[1]["headings"] == ["Network"]


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

    result = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 1,
        },
    )
    records = result["records"]

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/a",
    ]
    assert result["crawl_complete"] is True


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

    result = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 2,
        },
    )
    records = result["records"]

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/network",
    ]
    assert result["crawl_complete"] is True


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

    result = crawl_docs_pages(
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
    records = result["records"]

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/concepts",
        "https://example.com/docs/tasks",
    ]
    assert result["crawl_complete"] is False
    assert "max_pages_reached" in result["incomplete_reasons"]


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

    result = crawl_docs_pages(
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
    records = result["records"]

    assert "Storage Concepts" in records[0]["body"]
    assert "services-networking" not in records[0]["body"]
    assert result["crawl_complete"] is True


def test_crawl_docs_pages_detects_furo_layout_and_extracts_structure(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    html = """
      <html class="furo">
        <body>
          <nav class="breadcrumb"><a href="/">Docs</a><a href="/guide">Guide</a></nav>
          <main>
            <article>
              <h1>Deployment Guide</h1>
              <h2>Install</h2>
              <p>Use docker compose for local startup.</p>
            </article>
          </main>
          <div class="toc-drawer">table of contents</div>
        </body>
      </html>
    """

    class DummyResponse:
        def __init__(self, text):
            self.text = text
            self.headers = {"Last-Modified": "Mon, 09 Mar 2026 10:00:00 GMT"}

        def raise_for_status(self):
            return None

    monkeypatch.setattr("backend.docs_crawl.requests.get", lambda url, timeout=30: DummyResponse(html))

    result = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 0,
            "doc_system": "auto",
        },
    )
    records = result["records"]

    assert records[0]["extractor_hint"] == "furo"
    assert records[0]["headings"] == ["Deployment Guide", "Install"]
    assert records[0]["breadcrumbs"] == ["Docs Guide"]
    assert result["crawl_complete"] is True


def test_crawl_docs_pages_furo_nav_tree_prefers_real_pages_over_anchor_variants(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    pages = {
        "https://example.com/docs": """
          <html class="furo">
            <body>
              <div class="sidebar-tree">
                <ul class="current">
                  <li class="toctree-l1 current current-page"><a class="current reference internal" href="#">Home</a></li>
                  <li class="toctree-l1"><a class="reference internal" href="guide/">Guide</a></li>
                  <li class="toctree-l1 has-children">
                    <a class="reference internal" href="networks/">Networks</a>
                    <ul>
                      <li class="toctree-l2"><a class="reference internal" href="reference/network_bridge/">Bridge</a></li>
                    </ul>
                  </li>
                </ul>
              </div>
              <main>
                <article>
                  <h1>Home</h1>
                  <a href="#home">Anchor</a>
                  <a href="guide/#install">Guide install</a>
                </article>
              </main>
            </body>
          </html>
        """,
        "https://example.com/docs/guide": "<main><article><h1>Guide</h1><p>step by step</p></article></main>",
        "https://example.com/docs/networks": "<main><article><h1>Networks</h1><p>ovn bridge acl</p></article></main>",
        "https://example.com/docs/reference/network_bridge": "<main><article><h1>Bridge</h1><p>bridge config</p></article></main>",
    }

    class DummyResponse:
        def __init__(self, text):
            self.text = text
            self.headers = {}

        def raise_for_status(self):
            return None

    monkeypatch.setattr("backend.docs_crawl.requests.get", lambda url, timeout=30: DummyResponse(pages[url]))

    result = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs/",
        profile={
            "entry_urls": ["https://example.com/docs/"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 2,
            "max_pages": 4,
            "doc_system": "furo",
            "link_strategy": "furo_nav_first",
            "canonicalize_fragments": True,
        },
    )
    records = result["records"]

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/guide",
        "https://example.com/docs/networks",
        "https://example.com/docs/reference/network_bridge",
    ]
    assert records[2]["nav_title"] == "Networks"
    assert records[3]["parent_section"] == "Networks"
    assert result["crawl_complete"] is True


def test_crawl_docs_pages_canonicalizes_anchor_and_index_urls(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    pages = {
        "https://example.com/docs": """
          <html><body>
            <main>
              <h1>Docs</h1>
              <a href="index.html#overview">Overview</a>
              <a href="./network/#acl">Network</a>
            </main>
          </body></html>
        """,
        "https://example.com/docs/network": "<main><h1>Network</h1><p>acl rules</p></main>",
    }

    class DummyResponse:
        def __init__(self, text):
            self.text = text
            self.headers = {}

        def raise_for_status(self):
            return None

    monkeypatch.setattr("backend.docs_crawl.requests.get", lambda url, timeout=30: DummyResponse(pages[url]))

    result = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs/",
        profile={
            "entry_urls": ["https://example.com/docs/"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 1,
            "max_pages": 3,
            "doc_system": "html-main",
            "canonicalize_fragments": True,
        },
    )
    records = result["records"]

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/network",
    ]
    assert result["crawl_complete"] is True


def test_crawl_docs_pages_reuses_cached_snapshot_on_304(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    class DummyResponse:
        def __init__(self):
            self.status_code = 304
            self.headers = {}
            self.text = ""

        def raise_for_status(self):
            return None

    def fake_get(url, timeout=30, headers=None):
        assert headers["If-None-Match"] == '"etag-1"'
        assert headers["If-Modified-Since"] == "Mon, 09 Mar 2026 10:00:00 GMT"
        return DummyResponse()

    monkeypatch.setattr("backend.docs_crawl.requests.Session.get", lambda self, url, timeout=30, headers=None: fake_get(url, timeout, headers))

    result = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs/",
        profile={
            "entry_urls": ["https://example.com/docs/guide/"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 0,
        },
        previous_pages={
            "https://example.com/docs/guide": {
                "id": "guide-page",
                "url": "https://example.com/docs/guide",
                "path": "/docs/guide",
                "title": "Guide",
                "section": "Guide",
                "section_key": "Guide",
                "parent_section": "",
                "category": "架构",
                "extractor_hint": "furo",
                "nav_title": "Guide",
                "nav_depth": 0,
                "nav_order": 1,
                "is_index_page": True,
                "headings": ["Guide"],
                "breadcrumbs": ["Docs", "Guide"],
                "text_content": "cached body",
                "content_hash": "content-hash",
                "page_hash": "page-hash",
                "last_seen_at": "2026-03-09T10:00:00Z",
                "etag": '"etag-1"',
                "http_last_modified": "Mon, 09 Mar 2026 10:00:00 GMT",
            }
        },
    )
    records = result["records"]

    assert len(records) == 1
    assert records[0]["url"] == "https://example.com/docs/guide"
    assert records[0]["body"] == "cached body"
    assert records[0]["was_modified"] is False
    assert result["crawl_complete"] is True


def test_crawl_docs_pages_reuses_cached_discovered_links_on_304(monkeypatch):
    from backend.docs_crawl import crawl_docs_pages

    class NotModifiedResponse:
        def __init__(self):
            self.status_code = 304
            self.headers = {}
            self.text = ""

        def raise_for_status(self):
            return None

    class HtmlResponse:
        def __init__(self, text):
            self.status_code = 200
            self.headers = {}
            self.text = text

        def raise_for_status(self):
            return None

    def fake_session_get(_self, url, timeout=30, headers=None):
        assert headers["If-None-Match"] == '"etag-home"'
        return NotModifiedResponse()

    def fake_get(url, timeout=30):
        assert url == "https://example.com/docs/network"
        return HtmlResponse("<main><h1>Network</h1><p>nftables</p></main>")

    monkeypatch.setattr("backend.docs_crawl.requests.Session.get", fake_session_get)
    monkeypatch.setattr("backend.docs_crawl.requests.get", fake_get)

    result = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs/",
        profile={
            "entry_urls": ["https://example.com/docs/"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 1,
        },
        previous_pages={
            "https://example.com/docs": {
                "id": "docs-home",
                "url": "https://example.com/docs",
                "path": "/docs",
                "title": "Docs",
                "section": "Docs",
                "text_content": "cached docs home",
                "content_hash": "content-hash",
                "page_hash": "page-hash",
                "etag": '"etag-home"',
                "http_last_modified": "Mon, 09 Mar 2026 10:00:00 GMT",
                "discovered_links": [
                    {
                        "url": "https://example.com/docs/network",
                        "priority_source": "content",
                        "order_hint": 0,
                        "is_index_page": False,
                    }
                ],
            }
        },
    )
    records = result["records"]

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/network",
    ]
    assert records[0]["was_modified"] is False
    assert result["crawl_complete"] is True


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

    result = crawl_docs_pages(
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
    assert result["crawl_complete"] is True


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

    result = crawl_docs_pages(
        project_id="demo",
        docs_url="https://example.com/docs",
        profile={
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 1,
        },
    )
    records = result["records"]

    assert [record["url"] for record in records] == [
        "https://example.com/docs",
        "https://example.com/docs/good",
    ]
    assert result["crawl_complete"] is False
    assert "request_failed:https://example.com/docs/bad" in result["incomplete_reasons"]
