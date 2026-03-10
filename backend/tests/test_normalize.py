def test_normalize_release_builds_stable_event_id_and_hash():
    from backend.normalize import normalize_release_event

    event = normalize_release_event(
        "kubernetes/kubernetes",
        {
            "tag_name": "v1.31.0",
            "name": "Kubernetes v1.31.0",
            "body": "Kubernetes 1.31 recommends nftables-based networking paths.",
            "html_url": "https://github.com/kubernetes/kubernetes/releases/tag/v1.31.0",
            "published_at": "2026-03-08T08:00:00Z",
        },
    )

    assert event["id"] == "github-release:kubernetes/kubernetes:v1.31.0"
    assert event["source"] == "github_release"
    assert event["version"] == "v1.31.0"
    assert event["content_hash"]


def test_normalize_feed_builds_stable_event_id():
    from backend.normalize import normalize_feed_entry

    event = normalize_feed_entry(
        "k8s-docs",
        {
            "id": "https://github.com/kubernetes/website/commit/123",
            "title": "Recommend nftables mode in 1.31 docs",
            "link": "https://github.com/kubernetes/website/commit/123",
            "published": "2026-03-08T10:00:00Z",
            "summary": "Documentation update",
            "category": "网络",
        },
    )

    assert event["id"] == "docs-feed:k8s-docs:https://github.com/kubernetes/website/commit/123"
    assert event["source"] == "docs_feed"
    assert event["source_key"] == "k8s-docs"
    assert event["category"] == "网络"


def test_event_is_pending_analysis_only_when_new_or_changed():
    from backend.normalize import should_analyze_event

    known_events = {
        "github-release:kubernetes/kubernetes:v1.31.0": {
            "id": "github-release:kubernetes/kubernetes:v1.31.0",
            "content_hash": "same-hash",
        }
    }
    stable_analyses = {
        "github-release:kubernetes/kubernetes:v1.31.0": {
            "is_stable": True,
        }
    }

    assert (
        should_analyze_event(
            {
                "id": "github-release:kubernetes/kubernetes:v1.31.0",
                "content_hash": "same-hash",
            },
            known_events,
            stable_analyses,
        )
        is False
    )
    assert (
        should_analyze_event(
            {
                "id": "github-release:kubernetes/kubernetes:v1.31.0",
                "content_hash": "changed-hash",
            },
            known_events,
            stable_analyses,
        )
        is True
    )
    assert (
        should_analyze_event(
            {
                "id": "github-release:kubernetes/kubernetes:v1.32.0",
                "content_hash": "new-hash",
            },
            known_events,
            stable_analyses,
        )
        is True
    )


def test_normalize_release_event_hash_includes_research_bundle():
    from backend.normalize import normalize_release_event

    base_payload = {
        "tag_name": "v1.35.2",
        "name": "v1.35.2",
        "body": "See CHANGELOG",
        "html_url": "https://example.com/v1.35.2",
        "published_at": "2026-03-09T00:00:00Z",
    }

    event_without_bundle = normalize_release_event("kubernetes/kubernetes", base_payload)
    event_with_bundle = normalize_release_event(
        "kubernetes/kubernetes",
        {
            **base_payload,
            "research_bundle": {
                "changelog": {"version_section": "# v1.35.2\n\n### Feature\n- storage validation"},
            },
        },
    )

    assert event_without_bundle["content_hash"] != event_with_bundle["content_hash"]
