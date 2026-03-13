from pathlib import Path


def test_build_sync_runner_uses_store_config_and_persists_results(tmp_path: Path, monkeypatch):
    from backend.runtime import build_incremental_sync_runner
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

    captured = {}

    def fake_run_sync_once(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "new_events": 1,
            "analyzed_events": 1,
            "failed_events": 0,
            "last_sync_at": kwargs["now_iso"],
        }

    monkeypatch.setattr("backend.runtime.run_sync_once", fake_run_sync_once)

    runner = build_incremental_sync_runner(store, now_provider=lambda: "2026-03-09T12:00:00Z")

    result = runner()
    snapshot = store.load_all()

    assert result["analyzed_events"] == 1
    assert captured["kwargs"]["max_workers"] == 4
    assert captured["kwargs"]["source_timeout_seconds"] == 120
    assert snapshot["state"]["last_sync_at"] == "2026-03-09T12:00:00Z"
    assert snapshot["state"]["last_fetch_success_at"] == "2026-03-09T12:00:00Z"
    assert snapshot["state"]["last_incremental_analysis_at"] == "2026-03-09T12:00:00Z"
    assert captured["kwargs"]["repos"] == ["kubernetes/kubernetes"]
    assert captured["kwargs"]["feeds"] == [
        {
            "id": "kubernetes:docs",
            "project_id": "kubernetes",
            "name": "Kubernetes 文档",
            "url": "https://example.com/feed.atom",
            "type": "page",
            "entry_urls": ["https://example.com/feed.atom"],
            "allowed_path_prefixes": ["/"],
            "blocked_path_prefixes": [],
            "max_depth": 1,
            "max_pages": 40,
            "category_hints": [],
            "discovery_prompt": "",
            "classification_prompt": "",
        }
    ]
    assert snapshot["events"] == {}
    assert snapshot["daily_project_summaries"] == {}


def test_build_sync_runner_uses_configured_concurrency_values(tmp_path: Path, monkeypatch):
    from backend.runtime import build_incremental_sync_runner
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_config({"sync_interval_minutes": 30, "sync_concurrency": 7, "sync_source_timeout_seconds": 45})
    captured = {}

    def fake_run_sync_once(**kwargs):
        captured["kwargs"] = kwargs
        return {"new_events": 0, "analyzed_events": 0, "failed_events": 0, "last_sync_at": kwargs["now_iso"]}

    monkeypatch.setattr("backend.runtime.run_sync_once", fake_run_sync_once)

    runner = build_incremental_sync_runner(store, now_provider=lambda: "2026-03-09T12:00:00Z")
    runner()

    assert captured["kwargs"]["max_workers"] == 7
    assert captured["kwargs"]["source_timeout_seconds"] == 45


def test_build_sync_runner_includes_docs_only_projects(tmp_path: Path, monkeypatch):
    from backend.runtime import build_incremental_sync_runner
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_project(
        {
            "id": "cuda-toolkit",
            "name": "CUDA 工具链",
            "github_url": "",
            "repo": "",
            "docs_url": "https://docs.nvidia.com/cuda/",
            "enabled": True,
            "release_area_enabled": False,
            "docs_area_enabled": True,
            "sync_interval_minutes": 60,
        }
    )
    store.save_crawl_profile(
        "cuda-toolkit",
        {
            "entry_urls": ["https://docs.nvidia.com/cuda/"],
            "allowed_path_prefixes": ["/cuda"],
            "blocked_path_prefixes": [],
            "max_depth": 3,
        }
    )

    captured = {}

    def fake_run_sync_once(**kwargs):
        captured["kwargs"] = kwargs
        return {"new_events": 0, "analyzed_events": 0, "failed_events": 0, "last_sync_at": kwargs["now_iso"]}

    monkeypatch.setattr("backend.runtime.run_sync_once", fake_run_sync_once)

    runner = build_incremental_sync_runner(store, now_provider=lambda: "2026-03-09T12:00:00Z")
    runner()

    assert captured["kwargs"]["repos"] == []
    assert [feed["project_id"] for feed in captured["kwargs"]["feeds"]] == ["cuda-toolkit"]


def test_build_daily_digest_runner_persists_digest_and_history(tmp_path: Path):
    from backend.runtime import build_daily_digest_runner
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_project(
        {
            "id": "cilium",
            "name": "Cilium",
            "github_url": "https://github.com/cilium/cilium",
            "repo": "cilium/cilium",
            "docs_url": "",
            "enabled": True,
            "release_area_enabled": True,
            "docs_area_enabled": False,
            "sync_interval_minutes": 60,
        }
    )
    store.save_event(
        {
            "id": "github-release:cilium/cilium:v1.20.0-pre.0",
            "source": "github_release",
            "repo": "cilium/cilium",
            "source_key": "cilium/cilium",
            "project_id": "cilium",
            "title": "Cilium v1.20.0-pre.0",
            "version": "v1.20.0-pre.0",
            "url": "https://example.com/cilium",
            "content_hash": "hash-cilium",
            "published_at": "2026-03-11T00:10:00Z",
        }
    )
    store.save_analysis(
        "github-release:cilium/cilium:v1.20.0-pre.0",
        {
            "title_zh": "Cilium 1.20 预发布",
            "summary_zh": "高优先级变化。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["重大网络变更"]}],
            "impact_scope": "cluster",
            "impact_points": ["cluster"],
            "suggested_action": "验证升级。",
            "action_items": ["验证升级。"],
            "urgency": "high",
            "tags": ["cilium"],
            "is_stable": True,
        },
    )

    runner = build_daily_digest_runner(store, now_provider=lambda: "2026-03-11T00:30:00Z")
    result = runner()
    snapshot = store.load_all()

    assert result["summary_date"] == "2026-03-11"
    assert result["summary_count"] == 1
    assert snapshot["state"]["last_daily_digest_at"] == "2026-03-11T00:30:00Z"
    assert snapshot["state"]["last_heartbeat_at"] == "2026-03-11T00:30:00Z"
    assert "2026-03-11:cilium" in snapshot["daily_project_summaries"]


def test_incremental_runner_passes_run_logger_and_id(tmp_path: Path, monkeypatch):
    from backend.runtime import build_incremental_sync_runner
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_config({})

    captured = {}

    def fake_run_sync_once(*, run_logger=None, run_id=None, **_kwargs):
        captured["run_logger"] = run_logger
        captured["run_id"] = run_id
        return {"new_events": 0, "analyzed_events": 0, "failed_events": 0}

    monkeypatch.setattr("backend.runtime.run_sync_once", fake_run_sync_once)

    runner = build_incremental_sync_runner(store, now_provider=lambda: "2026-03-09T12:00:00Z")
    recorder = object()
    runner(run_logger=recorder, run_id="run_1")

    assert captured["run_logger"] is recorder
    assert captured["run_id"] == "run_1"
