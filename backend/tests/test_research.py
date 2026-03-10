from types import SimpleNamespace


def test_build_release_research_bundle_extracts_changelog_and_doc_refs(monkeypatch):
    from backend.research import build_release_research_bundle

    release = {
        "tag_name": "v1.35.2",
        "name": "v1.35.2",
        "body": (
            "See the [CHANGELOG](https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.35.md) "
            "for more details.\n\n"
            "Storage notes: https://kubernetes.io/zh-cn/docs/concepts/storage/"
        ),
        "html_url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.2",
    }

    changelog = """# v1.35.2

## Changelog since v1.35.1
- [abc123] Improve volume lifecycle handling

## Changes by Kind

### Feature
- Introduce more explicit storage validation for CSI workflows

### Dependencies

#### Changed
- github.com/example/dependency v1.0.0 -> v1.1.0

# v1.35.1
"""
    docs_html = """<html><main><h1>存储</h1><p>CSI 卷快照、持久卷和动态制备是这一节的重点。</p></main></html>"""

    def fake_get(url, timeout=30, headers=None):
        if "raw.githubusercontent.com" in url:
            return SimpleNamespace(text=changelog, raise_for_status=lambda: None, headers={})
        if "kubernetes.io/zh-cn/docs/concepts/storage" in url:
            return SimpleNamespace(text=docs_html, raise_for_status=lambda: None, headers={})
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr("backend.research.requests.get", fake_get)

    bundle = build_release_research_bundle("kubernetes/kubernetes", release)

    assert bundle["release"]["version"] == "v1.35.2"
    assert bundle["changelog"]["url"] == "https://raw.githubusercontent.com/kubernetes/kubernetes/master/CHANGELOG/CHANGELOG-1.35.md"
    assert "# v1.35.2" in bundle["changelog"]["version_section"]
    assert bundle["changelog"]["sections"][0]["title"] == "Feature"
    assert "CSI workflows" in bundle["changelog"]["sections"][0]["content"]
    assert bundle["doc_refs"][0]["url"] == "https://kubernetes.io/zh-cn/docs/concepts/storage/"
    assert "CSI 卷快照" in bundle["doc_refs"][0]["snippet"]


def test_build_docs_group_research_bundle_preserves_page_level_context():
    from backend.research import build_docs_group_research_bundle

    bundle = build_docs_group_research_bundle(
        category="存储",
        items=[
            {
                "title": "存储卷",
                "url": "https://kubernetes.io/zh-cn/docs/concepts/storage/volumes/",
                "body": "介绍卷、持久卷和临时卷的基本行为。",
                "last_seen_at": "2026-03-10T00:00:00Z",
            },
            {
                "title": "持久卷",
                "url": "https://kubernetes.io/zh-cn/docs/concepts/storage/persistent-volumes/",
                "body": "介绍 PV、PVC、StorageClass 和动态制备。",
                "last_seen_at": "2026-03-09T00:00:00Z",
            },
        ],
    )

    assert bundle["category"] == "存储"
    assert bundle["pages"][0]["title"] == "存储卷"
    assert bundle["pages"][0]["url"].endswith("/volumes/")
    assert "临时卷" in bundle["pages"][0]["snippet"]
    assert bundle["page_count"] == 2


def test_extract_doc_urls_skips_download_and_archive_links():
    from backend.research import _extract_doc_urls

    urls = _extract_doc_urls(
        "https://dl.k8s.io/v1.35.2/kubernetes.tar.gz",
        "https://kubernetes.io/zh-cn/docs/concepts/storage/",
        "https://github.com/kubernetes/kubernetes/releases/tag/v1.35.2",
    )

    assert urls == ["https://kubernetes.io/zh-cn/docs/concepts/storage/"]
