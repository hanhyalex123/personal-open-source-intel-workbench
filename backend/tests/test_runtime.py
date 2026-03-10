from pathlib import Path


def test_build_sync_runner_uses_store_config_and_persists_results(tmp_path: Path, monkeypatch):
    from backend.runtime import build_sync_runner
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_project(
        {
            "id": "kubernetes",
            "name": "Kubernetes",
            "github_url": "https://github.com/kubernetes/kubernetes",
            "repo": "kubernetes/kubernetes",
            "docs_url": "https://example.com/feed.atom",
            "enabled": True,
            "release_area_enabled": True,
            "docs_area_enabled": True,
            "sync_interval_minutes": 30,
        }
    )
    store.save_crawl_profile(
        "kubernetes",
        {
            "entry_urls": ["https://example.com/feed.atom"],
            "allowed_path_prefixes": ["/"],
            "blocked_path_prefixes": [],
            "max_depth": 1,
        }
    )
    store.save_config({"sync_interval_minutes": 30})

    monkeypatch.setattr(
        "backend.runtime.fetch_github_releases",
        lambda repo: [
            {
                "tag_name": "v1.31.0",
                "name": f"{repo} v1.31.0",
                "body": "release note",
                "html_url": "https://example.com/release",
                "published_at": "2026-03-09T00:00:00Z",
            }
        ],
    )
    monkeypatch.setattr(
        "backend.runtime.fetch_feed_entries",
        lambda feed: [
            {
                "id": "entry-1",
                "title": f'{feed["id"]} entry',
                "link": "https://example.com/feed-entry",
                "published": "2026-03-09T00:00:00Z",
                "summary": "docs note",
            }
        ],
    )
    monkeypatch.setattr(
        "backend.runtime.analyze_event",
        lambda event: {
            "title_zh": f'{event["title"]} 中文',
            "summary_zh": "中文总结",
            "details_zh": "中文详情",
            "impact_scope": "测试范围",
            "suggested_action": "关注变化",
            "urgency": "medium",
            "tags": ["test"],
            "is_stable": True,
        },
    )

    runner = build_sync_runner(store, now_provider=lambda: "2026-03-09T12:00:00Z")

    result = runner()
    snapshot = store.load_all()

    assert result["analyzed_events"] == 2
    assert snapshot["state"]["last_sync_at"] == "2026-03-09T12:00:00Z"
    assert snapshot["state"]["last_daily_summary_at"] == "2026-03-09T12:00:00Z"
    assert len(snapshot["events"]) == 2
    assert len(snapshot["daily_project_summaries"]) == 1
