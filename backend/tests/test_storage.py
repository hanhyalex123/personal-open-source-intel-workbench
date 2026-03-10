from pathlib import Path


def test_storage_initializes_default_json_state(tmp_path: Path):
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)

    snapshot = store.load_all()

    assert snapshot == {
        "config": {
            "sync_interval_minutes": 60,
            "assistant": {
                "enabled": True,
                "default_mode": "hybrid",
                "default_project_ids": [],
                "default_categories": [],
                "default_timeframe": "14d",
                "max_evidence_items": 3,
                "max_source_items": 4,
                "retrieval": {
                    "release_weight": 1.0,
                    "docs_weight": 1.2,
                },
                "live_search": {
                    "enabled": True,
                    "provider": "duckduckgo",
                    "max_results": 5,
                    "max_pages": 3,
                },
                "prompts": {
                    "classification": "",
                    "answer": "",
                },
            },
        },
        "events": {},
        "analyses": {},
        "projects": [],
        "crawl_profiles": {},
        "daily_project_summaries": {},
        "state": {
            "last_sync_at": None,
            "last_analysis_at": None,
            "last_daily_summary_at": None,
            "scheduler": {"running": False, "interval_minutes": 60},
        },
    }


def test_storage_round_trips_event_and_analysis_records(tmp_path: Path):
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.31.0",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "title": "Kubernetes v1.31.0",
            "version": "v1.31.0",
            "content_hash": "abc123",
        }
    )
    store.save_analysis(
        "github-release:kubernetes/kubernetes:v1.31.0",
        {
            "title_zh": "Kubernetes 1.31 正式发布",
            "summary_zh": "这是一个固定版本结论",
            "is_stable": True,
        },
    )

    snapshot = store.load_all()

    assert snapshot["events"]["github-release:kubernetes/kubernetes:v1.31.0"]["version"] == "v1.31.0"
    assert snapshot["analyses"]["github-release:kubernetes/kubernetes:v1.31.0"]["is_stable"] is True


def test_storage_round_trips_projects_and_crawl_profiles(tmp_path: Path):
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_project(
        {
            "id": "openclaw",
            "name": "OpenClaw",
            "github_url": "https://github.com/openclaw/openclaw",
            "repo": "openclaw/openclaw",
            "docs_url": "https://openclaw.dev/docs",
            "enabled": True,
            "release_area_enabled": True,
            "docs_area_enabled": True,
            "sync_interval_minutes": 60,
        }
    )
    store.save_crawl_profile(
        "openclaw",
        {
            "entry_urls": ["https://openclaw.dev/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 3,
        },
    )

    snapshot = store.load_all()

    assert snapshot["projects"][0]["repo"] == "openclaw/openclaw"
    assert snapshot["crawl_profiles"]["openclaw"]["entry_urls"] == ["https://openclaw.dev/docs"]
