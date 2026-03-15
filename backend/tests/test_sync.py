from pathlib import Path
from time import sleep


def test_sync_analyzes_only_new_or_changed_events(tmp_path: Path):
    from backend.normalize import normalize_release_event
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)
    store.save_event(
        normalize_release_event(
            "kubernetes/kubernetes",
            {
                "tag_name": "v1.31.0",
                "name": "Kubernetes v1.31.0",
                "body": "same body",
                "html_url": "https://example.com/v1.31.0",
                "published_at": "2026-03-08T08:00:00Z",
            },
        )
    )
    store.save_analysis(
        "github-release:kubernetes/kubernetes:v1.31.0",
        {
            "title_zh": "Kubernetes 1.31 网络建议",
            "summary_zh": "旧结论",
            "is_stable": True,
        },
    )

    analyzed_ids: list[str] = []

    def release_fetcher(repo: str):
        if repo == "kubernetes/kubernetes":
            return [
                {
                    "tag_name": "v1.31.0",
                    "name": "Kubernetes v1.31.0",
                    "body": "same body",
                    "html_url": "https://example.com/v1.31.0",
                    "published_at": "2026-03-08T08:00:00Z",
                },
                {
                    "tag_name": "v1.32.0",
                    "name": "Kubernetes v1.32.0",
                    "body": "new release body",
                    "html_url": "https://example.com/v1.32.0",
                    "published_at": "2026-03-09T08:00:00Z",
                },
            ]
        return []

    def feed_fetcher(_feed: dict):
        return []

    def analyzer(event: dict):
        analyzed_ids.append(event["id"])
        return {
            "title_zh": f'{event["title"]} 中文分析',
            "summary_zh": "新的中文结论",
            "details_zh": "详细说明",
            "impact_scope": "测试范围",
            "suggested_action": "检查更新",
            "urgency": "medium",
            "tags": ["test"],
            "is_stable": True,
        }

    result = run_sync_once(
        store=store,
        repos=["kubernetes/kubernetes"],
        feeds=[],
        release_fetcher=release_fetcher,
        feed_fetcher=feed_fetcher,
        analyzer=analyzer,
        now_iso="2026-03-09T12:00:00Z",
    )

    snapshot = store.load_all()

    assert analyzed_ids == ["github-release:kubernetes/kubernetes:v1.32.0"]
    assert result["new_events"] == 1
    assert result["analyzed_events"] == 1
    assert snapshot["state"]["last_sync_at"] == "2026-03-09T12:00:00Z"
    assert snapshot["analyses"]["github-release:kubernetes/kubernetes:v1.32.0"]["is_stable"] is True


def test_sync_reanalyzes_changed_hash(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)
    store.save_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.31.0",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "title": "Kubernetes v1.31.0",
            "version": "v1.31.0",
            "content_hash": "old-hash",
        }
    )
    store.save_analysis(
        "github-release:kubernetes/kubernetes:v1.31.0",
        {
            "title_zh": "旧标题",
            "summary_zh": "旧结论",
            "is_stable": True,
        },
    )

    analyzed_ids: list[str] = []

    def release_fetcher(_repo: str):
        return [
            {
                "tag_name": "v1.31.0",
                "name": "Kubernetes v1.31.0",
                "body": "changed body",
                "html_url": "https://example.com/v1.31.0",
                "published_at": "2026-03-08T08:00:00Z",
            }
        ]

    def analyzer(event: dict):
        analyzed_ids.append(event["id"])
        return {
            "title_zh": "新标题",
            "summary_zh": "重新分析后的结论",
            "details_zh": "详细说明",
            "impact_scope": "测试范围",
            "suggested_action": "重新检查",
            "urgency": "high",
            "tags": ["test"],
            "is_stable": True,
        }

    run_sync_once(
        store=store,
        repos=["kubernetes/kubernetes"],
        feeds=[],
        release_fetcher=release_fetcher,
        feed_fetcher=lambda _feed: [],
        analyzer=analyzer,
        now_iso="2026-03-09T12:10:00Z",
    )

    snapshot = store.load_all()

    assert analyzed_ids == ["github-release:kubernetes/kubernetes:v1.31.0"]
    assert snapshot["analyses"]["github-release:kubernetes/kubernetes:v1.31.0"]["summary_zh"] == "重新分析后的结论"


def test_sync_continues_when_single_analysis_fails(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)

    def release_fetcher(_repo: str):
        return [
            {
                "tag_name": "v1.31.0",
                "name": "Kubernetes v1.31.0",
                "body": "first body",
                "html_url": "https://example.com/v1.31.0",
                "published_at": "2026-03-08T08:00:00Z",
            },
            {
                "tag_name": "v1.31.1",
                "name": "Kubernetes v1.31.1",
                "body": "second body",
                "html_url": "https://example.com/v1.31.1",
                "published_at": "2026-03-09T08:00:00Z",
            },
        ]

    def analyzer(event: dict):
        if event["version"] == "v1.31.0":
            raise RuntimeError("llm timeout")
        return {
            "title_zh": "成功分析",
            "summary_zh": "成功结论",
            "details_zh": "详细说明",
            "detail_sections": [{"title": "核心变化点", "bullets": ["成功"]}],
            "impact_scope": "测试范围",
            "impact_points": ["测试范围"],
            "suggested_action": "继续处理",
            "action_items": ["继续处理"],
            "urgency": "low",
            "tags": ["test"],
            "is_stable": True,
        }

    result = run_sync_once(
        store=store,
        repos=["kubernetes/kubernetes"],
        feeds=[],
        release_fetcher=release_fetcher,
        feed_fetcher=lambda _feed: [],
        analyzer=analyzer,
        now_iso="2026-03-09T12:20:00Z",
    )

    snapshot = store.load_all()

    assert result["new_events"] == 2
    assert result["analyzed_events"] == 1
    assert result["failed_events"] == 1


def test_run_sync_once_records_event_logs(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once
    from backend.sync_runs import SyncRunRecorder, load_runs

    store = JsonStore(tmp_path)
    store.save_config({})
    recorder = SyncRunRecorder(store)
    run_id = recorder.start_run(run_kind="manual", started_at="2026-03-13T00:00:00Z")

    def release_fetcher(_repo: str):
        return [
            {
                "tag_name": "v1.0.0",
                "name": "Release v1.0.0",
                "body": "notes",
                "html_url": "https://example.com/v1.0.0",
                "published_at": "2026-03-12T08:00:00Z",
            }
        ]

    def analyzer(_event: dict):
        return {"title_zh": "测试", "summary_zh": "摘要", "urgency": "low", "action_items": []}

    run_sync_once(
        store=store,
        repos=["example/repo"],
        feeds=[],
        release_fetcher=release_fetcher,
        feed_fetcher=lambda _feed: [],
        analyzer=analyzer,
        now_iso="2026-03-13T00:00:00Z",
        run_logger=recorder,
        run_id=run_id,
    )

    payload = load_runs(store)
    assert payload["runs"][0]["sources"]


def test_sync_enriches_only_events_that_need_analysis(tmp_path: Path):
    from backend.normalize import normalize_release_event
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)
    existing_event = normalize_release_event(
        "kubernetes/kubernetes",
        {
            "tag_name": "v1.31.0",
            "name": "Kubernetes v1.31.0",
            "body": "same body",
            "html_url": "https://example.com/v1.31.0",
            "published_at": "2026-03-08T08:00:00Z",
        },
    )
    store.save_event(existing_event)
    store.save_analysis(
        existing_event["id"],
        {
            "title_zh": "旧标题",
            "summary_zh": "旧结论",
            "is_stable": True,
        },
    )

    enriched_ids = []

    def enrich_event(event: dict):
        enriched_ids.append(event["id"])
        return {
            **event,
            "research_bundle": {
                "release": {"version": event["version"]},
            },
        }

    def analyzer(event: dict):
        return {
            "title_zh": f'{event["title"]} 中文分析',
            "summary_zh": "新的中文结论",
            "details_zh": "详细说明",
            "detail_sections": [{"title": "核心变化点", "bullets": ["已重写"]}],
            "impact_scope": "测试范围",
            "impact_points": ["测试范围"],
            "suggested_action": "检查更新",
            "action_items": ["检查更新"],
            "urgency": "medium",
            "tags": ["test"],
            "is_stable": True,
        }

    run_sync_once(
        store=store,
        repos=["kubernetes/kubernetes"],
        feeds=[],
        release_fetcher=lambda _repo: [
            {
                "tag_name": "v1.31.0",
                "name": "Kubernetes v1.31.0",
                "body": "same body",
                "html_url": "https://example.com/v1.31.0",
                "published_at": "2026-03-08T08:00:00Z",
            },
            {
                "tag_name": "v1.32.0",
                "name": "Kubernetes v1.32.0",
                "body": "new body",
                "html_url": "https://example.com/v1.32.0",
                "published_at": "2026-03-09T08:00:00Z",
            },
        ],
        feed_fetcher=lambda _feed: [],
        analyzer=analyzer,
        event_enricher=enrich_event,
        now_iso="2026-03-09T12:30:00Z",
    )

    assert enriched_ids == ["github-release:kubernetes/kubernetes:v1.32.0"]


def test_sync_continues_when_source_times_out(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)

    def slow_release_fetcher(_repo: str):
        sleep(0.2)
        return []

    result = run_sync_once(
        store=store,
        repos=["repo/slow"],
        feeds=[],
        release_fetcher=slow_release_fetcher,
        feed_fetcher=lambda _feed: [],
        analyzer=lambda _event: {},
        now_iso="2026-03-11T12:00:00Z",
        max_workers=2,
        source_timeout_seconds=0.05,
    )

    assert result["failed_events"] == 1
    assert result["new_events"] == 0
    assert result["analyzed_events"] == 0


def test_sync_continues_after_source_exception(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)

    def failing_release_fetcher(_repo: str):
        raise RuntimeError("boom")

    def ok_feed_fetcher(_feed: dict):
        return [{"id": "feed-1", "title": "Doc", "link": "x", "published": "2026-03-11"}]

    def analyzer(event: dict):
        return {"title_zh": event.get("title", ""), "summary_zh": "ok", "is_stable": True}

    result = run_sync_once(
        store=store,
        repos=["repo/fail"],
        feeds=[{"id": "docs", "name": "Docs", "url": "https://example.com", "type": "page"}],
        release_fetcher=failing_release_fetcher,
        feed_fetcher=ok_feed_fetcher,
        analyzer=analyzer,
        now_iso="2026-03-11T12:00:00Z",
        max_workers=2,
        source_timeout_seconds=1,
    )

    assert result["failed_events"] == 1
    assert len(store.load_all()["events"]) == 1


def test_sync_reports_page_feed_progress_while_crawling(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)
    progress_updates = []

    def feed_fetcher(_feed: dict, progress_callback=None):
        progress_callback(current_url="https://example.com/docs", processed_pages=1, max_pages=40)
        progress_callback(current_url="https://example.com/docs/network", processed_pages=2, max_pages=40)
        return []

    run_sync_once(
        store=store,
        repos=[],
        feeds=[{"id": "docs", "name": "MindSpore 文档", "url": "https://example.com/docs", "type": "page", "max_pages": 40}],
        release_fetcher=lambda _repo: [],
        feed_fetcher=feed_fetcher,
        analyzer=lambda _event: {},
        now_iso="2026-03-11T12:00:00Z",
        progress_callback=lambda **payload: progress_updates.append(payload),
    )

    labels = [item["current_label"] for item in progress_updates if item.get("current_label")]

    assert "MindSpore 文档 · 1 / 40 页" in labels
    assert "MindSpore 文档 · 2 / 40 页" in labels


def test_sync_does_not_overwrite_docs_snapshot_when_crawl_is_incomplete(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)
    store.save_docs_snapshots(
        {
            "openclaw": {
                "project_id": "openclaw",
                "source_key": "openclaw-docs",
                "updated_at": "2026-03-09T10:00:00Z",
                "crawl_complete": True,
                "pages": {
                    "https://example.com/docs/network": {
                        "id": "network-page",
                        "url": "https://example.com/docs/network",
                        "title": "网络",
                        "text_content": "旧内容",
                        "content_hash": "old-content",
                        "page_hash": "old-page",
                    }
                },
            }
        }
    )

    def feed_fetcher(_feed: dict):
        return [
            {
                "id": "docs-partial-run",
                "project_id": "openclaw",
                "event_kind": "docs_diff_update",
                "title": "OpenClaw 文档部分抓取",
                "link": "https://example.com/docs/network",
                "published": "2026-03-10T10:00:00Z",
                "summary": "部分抓取结果",
                "_docs_snapshot_payload": {
                    "project_id": "openclaw",
                    "source_key": "openclaw-docs",
                    "updated_at": "2026-03-10T10:00:00Z",
                    "crawl_complete": False,
                    "incomplete_reasons": ["request_failed:https://example.com/docs/storage"],
                    "pages": {
                        "https://example.com/docs/network": {
                            "id": "network-page",
                            "url": "https://example.com/docs/network",
                            "title": "网络",
                            "text_content": "新内容",
                            "content_hash": "new-content",
                            "page_hash": "new-page",
                        }
                    },
                },
            }
        ]

    def analyzer(event: dict):
        return {
            "title_zh": f'{event["title"]} 中文分析',
            "summary_zh": "新的中文结论",
            "details_zh": "详细说明",
            "impact_scope": "测试范围",
            "suggested_action": "检查更新",
            "urgency": "medium",
            "tags": ["test"],
            "is_stable": True,
        }

    run_sync_once(
        store=store,
        repos=[],
        feeds=[{"id": "openclaw-docs", "name": "OpenClaw Docs", "url": "https://example.com/docs", "type": "page"}],
        release_fetcher=lambda _repo: [],
        feed_fetcher=feed_fetcher,
        analyzer=analyzer,
        now_iso="2026-03-10T12:00:00Z",
    )

    snapshot = store.load_docs_snapshots()

    assert snapshot["openclaw"]["updated_at"] == "2026-03-09T10:00:00Z"
    assert snapshot["openclaw"]["pages"]["https://example.com/docs/network"]["page_hash"] == "old-page"


def test_sync_persists_docs_baseline_without_events_when_initial_read_is_disabled(tmp_path: Path, monkeypatch):
    from backend.sources import fetch_feed_entries
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)
    analyzed_events = []

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

    run_sync_once(
        store=store,
        repos=[],
        feeds=[
            {
                "id": "openclaw-docs",
                "project_id": "openclaw",
                "name": "OpenClaw Docs",
                "url": "https://example.com/docs",
                "type": "page",
                "initial_read_enabled": False,
            }
        ],
        release_fetcher=lambda _repo: [],
        feed_fetcher=fetch_feed_entries,
        analyzer=lambda event: analyzed_events.append(event["id"]) or {},
        now_iso="2026-03-10T12:00:00Z",
    )

    snapshot = store.load_docs_snapshots()
    payload = store.load_all()

    assert snapshot["openclaw"]["updated_at"] == "2026-03-10T10:00:00Z"
    assert snapshot["openclaw"]["pages"]["https://example.com/docs/network"]["page_hash"] == "baseline-page"
    assert payload["events"] == {}
    assert payload["analyses"] == {}
    assert analyzed_events == []


def test_sync_builds_docs_diff_after_initial_read_disabled_baseline(tmp_path: Path, monkeypatch):
    from backend.sources import fetch_feed_entries
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)
    crawl_results = [
        {
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
        {
            "records": [
                {
                    "id": "network-page",
                    "url": "https://example.com/docs/network",
                    "path": "/docs/network",
                    "title": "网络",
                    "body": "加入 nftables 推荐。",
                    "text_content": "加入 nftables 推荐。",
                    "headings": ["网络", "代理模式"],
                    "breadcrumbs": ["文档", "网络"],
                    "last_seen_at": "2026-03-11T10:00:00Z",
                    "content_hash": "updated-content",
                    "page_hash": "updated-page",
                    "category": "网络",
                }
            ],
            "crawl_complete": True,
            "incomplete_reasons": [],
        },
    ]
    analyzed_event_kinds = []

    monkeypatch.setattr("backend.sources.crawl_docs_pages", lambda **kwargs: crawl_results.pop(0))

    feed = {
        "id": "openclaw-docs",
        "project_id": "openclaw",
        "name": "OpenClaw Docs",
        "url": "https://example.com/docs",
        "type": "page",
        "initial_read_enabled": False,
    }

    def analyzer(event: dict):
        analyzed_event_kinds.append(event["event_kind"])
        return {
            "title_zh": f'{event["title"]} 中文分析',
            "summary_zh": "检测到文档变更",
            "details_zh": "详细说明",
            "impact_scope": "文档使用者",
            "suggested_action": "同步内部知识库",
            "urgency": "medium",
            "tags": ["docs"],
            "analysis_mode": "diff_update",
            "changed_pages": [{"title": "网络", "url": "https://example.com/docs/network", "change_type": "changed"}],
            "is_stable": True,
        }

    run_sync_once(
        store=store,
        repos=[],
        feeds=[feed],
        release_fetcher=lambda _repo: [],
        feed_fetcher=fetch_feed_entries,
        analyzer=analyzer,
        now_iso="2026-03-10T12:00:00Z",
    )
    run_sync_once(
        store=store,
        repos=[],
        feeds=[feed],
        release_fetcher=lambda _repo: [],
        feed_fetcher=fetch_feed_entries,
        analyzer=analyzer,
        now_iso="2026-03-11T12:00:00Z",
    )

    snapshot = store.load_docs_snapshots()
    payload = store.load_all()
    docs_events = list(payload["events"].values())

    assert analyzed_event_kinds == ["docs_diff_update"]
    assert len(docs_events) == 1
    assert docs_events[0]["event_kind"] == "docs_diff_update"
    assert docs_events[0]["research_bundle"]["changed_pages"][0]["change_type"] == "changed"
    assert snapshot["openclaw"]["updated_at"] == "2026-03-11T10:00:00Z"
    assert snapshot["openclaw"]["pages"]["https://example.com/docs/network"]["page_hash"] == "updated-page"


def test_sync_reports_release_progress_while_processing_repo(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once

    store = JsonStore(tmp_path)
    progress_updates = []

    def release_fetcher(_repo: str, progress_callback=None):
        progress_callback(stage="requesting")
        progress_callback(stage="processing", processed_items=1, total_items=2)
        progress_callback(stage="processing", processed_items=2, total_items=2)
        return []

    run_sync_once(
        store=store,
        repos=["kubernetes/kubernetes"],
        feeds=[],
        release_fetcher=release_fetcher,
        feed_fetcher=lambda _feed: [],
        analyzer=lambda _event: {},
        now_iso="2026-03-11T12:00:00Z",
        progress_callback=lambda **payload: progress_updates.append(payload),
    )

    labels = [item["current_label"] for item in progress_updates if item.get("current_label")]

    assert "kubernetes/kubernetes · 正在请求 GitHub releases" in labels
    assert "kubernetes/kubernetes · 1 / 2 条 release" in labels
    assert "kubernetes/kubernetes · 2 / 2 条 release" in labels


def test_run_sync_once_records_event_logs(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once
    from backend.sync_runs import SyncRunRecorder, load_runs

    store = JsonStore(tmp_path)
    recorder = SyncRunRecorder(store)
    run_id = recorder.start_run(run_kind="manual", started_at="2026-03-13T00:00:00Z")

    def fake_release_fetcher(repo: str, progress_callback=None):
        return [
            {
                "name": "v1",
                "tag_name": "v1",
                "html_url": "https://x",
                "published_at": "2026-03-13T00:00:00Z",
            }
        ]

    def fake_feed_fetcher(feed: dict, progress_callback=None):
        return []

    def fake_analyzer(event: dict):
        return {
            "title_zh": "t",
            "summary_zh": "s",
            "details_zh": "",
            "impact_scope": "low",
            "suggested_action": "",
            "urgency": "low",
            "tags": [],
            "is_stable": True,
        }

    run_sync_once(
        store=store,
        repos=["openclaw/openclaw"],
        feeds=[],
        release_fetcher=fake_release_fetcher,
        feed_fetcher=fake_feed_fetcher,
        analyzer=fake_analyzer,
        now_iso="2026-03-13T00:00:00Z",
        run_logger=recorder,
        run_id=run_id,
        max_workers=1,
        source_timeout_seconds=1,
    )

    runs = load_runs(store)["runs"]
    assert runs[0]["sources"]
    assert runs[0]["sources"][0]["events"][0]["status"] in {"analyzed", "failed", "skipped"}


def test_run_sync_once_records_source_fetch_failure(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once
    from backend.sync_runs import SyncRunRecorder, load_runs

    store = JsonStore(tmp_path)
    recorder = SyncRunRecorder(store)
    run_id = recorder.start_run(run_kind="manual", started_at="2026-03-13T00:00:00Z")

    def failing_release_fetcher(_repo: str, progress_callback=None):
        raise RuntimeError("fetch boom")

    result = run_sync_once(
        store=store,
        repos=["openclaw/openclaw"],
        feeds=[],
        release_fetcher=failing_release_fetcher,
        feed_fetcher=lambda _feed, progress_callback=None: [],
        analyzer=lambda _event: {},
        now_iso="2026-03-13T00:00:00Z",
        run_logger=recorder,
        run_id=run_id,
        max_workers=1,
        source_timeout_seconds=1,
    )

    runs = load_runs(store)["runs"]
    source = runs[0]["sources"][0]
    assert source["status"] == "failed"
    assert "fetch boom" in source["error"]
    assert source["metrics"]["failed_events"] == 1
    assert result["failed_events"] == 1


def test_run_sync_once_records_llm_failure_context_in_event_logs(tmp_path: Path):
    from backend.storage import JsonStore
    from backend.sync import run_sync_once
    from backend.sync_runs import SyncRunRecorder, load_runs

    store = JsonStore(tmp_path)
    recorder = SyncRunRecorder(store)
    run_id = recorder.start_run(run_kind="manual", started_at="2026-03-13T00:00:00Z")

    class FakeLLMError(RuntimeError):
        def __init__(self):
            super().__init__("LLM gateway request failed")
            self.error_kind = "llm_gateway"
            self.provider = "primary-gateway"
            self.model = "claude-sonnet-4-6"
            self.used_fallback = True
            self.fallback_provider = "packy-glm"
            self.fallback_model = "glm-5"

    def fake_release_fetcher(repo: str, progress_callback=None):
        return [
            {
                "name": "v1",
                "tag_name": "v1",
                "html_url": "https://x",
                "published_at": "2026-03-13T00:00:00Z",
            }
        ]

    def fake_analyzer(event: dict):
        raise FakeLLMError()

    run_sync_once(
        store=store,
        repos=["openclaw/openclaw"],
        feeds=[],
        release_fetcher=fake_release_fetcher,
        feed_fetcher=lambda _feed, progress_callback=None: [],
        analyzer=fake_analyzer,
        now_iso="2026-03-13T00:00:00Z",
        run_logger=recorder,
        run_id=run_id,
        max_workers=1,
        source_timeout_seconds=1,
    )

    runs = load_runs(store)["runs"]
    event = runs[0]["sources"][0]["events"][0]
    assert event["status"] == "failed"
    assert event["error_kind"] == "llm_gateway"
    assert event["provider"] == "primary-gateway"
    assert event["model"] == "claude-sonnet-4-6"
    assert event["used_fallback"] is True
    assert event["fallback_model"] == "glm-5"
