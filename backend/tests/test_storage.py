from pathlib import Path


def test_storage_initializes_default_json_state(tmp_path: Path):
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)

    snapshot = store.load_all()

    assert snapshot == {
        "config": {
            "sync_interval_minutes": 60,
            "sync_concurrency": 4,
            "sync_source_timeout_seconds": 120,
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
            "last_fetch_success_at": None,
            "last_incremental_analysis_at": None,
            "last_daily_digest_at": None,
            "last_heartbeat_at": None,
            "scheduler": {
                "running": False,
                "interval_minutes": 60,
                "timezone": "Asia/Shanghai",
                "jobs": {
                    "incremental": {"enabled": True},
                    "daily_digest": {"enabled": True, "hour": 8, "minute": 0},
                },
            },
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


def test_seed_projects_loaded_when_data_missing(tmp_path: Path):
    from backend.storage import JsonStore

    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "projects.json").write_text(
        '[{"id":"seed","name":"Seed","repo":"","docs_url":"https://example.com","enabled":true,"release_area_enabled":false,"docs_area_enabled":true,"sync_interval_minutes":60,"created_at":"2026-03-11T00:00:00Z","updated_at":"2026-03-11T00:00:00Z"}]',
        encoding="utf-8",
    )
    (seed_dir / "crawl_profiles.json").write_text(
        '{"seed":{"entry_urls":["https://example.com"],"allowed_path_prefixes":["/"],"blocked_path_prefixes":[],"max_depth":3,"max_pages":40,"expand_mode":"auto","category_hints":[],"discovery_prompt":"","classification_prompt":""}}',
        encoding="utf-8",
    )

    store = JsonStore(tmp_path)
    store.seed_dir = seed_dir
    snapshot = store.load_all()

    assert snapshot["projects"][0]["id"] == "seed"
    assert snapshot["crawl_profiles"]["seed"]["entry_urls"] == ["https://example.com"]


def test_bundled_seed_projects_include_container_runtimes():
    import json
    from pathlib import Path

    projects = json.loads((Path.cwd() / "backend" / "seed" / "projects.json").read_text(encoding="utf-8"))
    crawl_profiles = json.loads((Path.cwd() / "backend" / "seed" / "crawl_profiles.json").read_text(encoding="utf-8"))

    project_ids = {project["id"] for project in projects}

    assert {"containerd", "cri-o", "podman"}.issubset(project_ids)
    assert "containerd" in crawl_profiles
    assert "cri-o" in crawl_profiles
    assert "podman" in crawl_profiles


def test_seed_projects_not_overwrite_existing_data(tmp_path: Path):
    from backend.storage import JsonStore

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "projects.json").write_text(
        '[{"id":"local","name":"Local","repo":"","docs_url":"","enabled":true,"release_area_enabled":false,"docs_area_enabled":false,"sync_interval_minutes":60,"created_at":"2026-03-11T00:00:00Z","updated_at":"2026-03-11T00:00:00Z"}]',
        encoding="utf-8",
    )
    (data_dir / "crawl_profiles.json").write_text(
        '{"local":{"entry_urls":[],"allowed_path_prefixes":[],"blocked_path_prefixes":[],"max_depth":3,"max_pages":40,"expand_mode":"auto","category_hints":[],"discovery_prompt":"","classification_prompt":""}}',
        encoding="utf-8",
    )

    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "projects.json").write_text(
        '[{"id":"seed","name":"Seed","repo":"","docs_url":"https://example.com","enabled":true,"release_area_enabled":false,"docs_area_enabled":true,"sync_interval_minutes":60,"created_at":"2026-03-11T00:00:00Z","updated_at":"2026-03-11T00:00:00Z"}]',
        encoding="utf-8",
    )
    (seed_dir / "crawl_profiles.json").write_text(
        '{"seed":{"entry_urls":["https://example.com"],"allowed_path_prefixes":["/"],"blocked_path_prefixes":[],"max_depth":3,"max_pages":40,"expand_mode":"auto","category_hints":[],"discovery_prompt":"","classification_prompt":""}}',
        encoding="utf-8",
    )

    store = JsonStore(data_dir)
    store.seed_dir = seed_dir
    snapshot = store.load_all()

    assert snapshot["projects"][0]["id"] == "local"
    assert "seed" not in snapshot["crawl_profiles"]
