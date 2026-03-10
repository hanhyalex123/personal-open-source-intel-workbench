def test_search_web_parses_html_results(monkeypatch):
    from backend.search import search_web

    html = """
      <html><body>
        <a class="result__a" href="https://example.com/a">OpenClaw release notes</a>
        <a class="result__a" href="https://example.com/b">Kubernetes docs</a>
        <div class="result__snippet">A snippet about routing</div>
        <div class="result__snippet">A snippet about kube-proxy</div>
      </body></html>
    """

    class DummyResponse:
        text = html

        def raise_for_status(self):
            return None

    monkeypatch.setattr("backend.search.requests.get", lambda url, params=None, timeout=30, headers=None: DummyResponse())

    results = search_web("openclaw routing", max_results=2)

    assert results[0]["title"] == "OpenClaw release notes"
    assert results[0]["url"] == "https://example.com/a"
    assert "snippet" in results[0]["snippet"].lower()
