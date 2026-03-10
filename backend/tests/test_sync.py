from pathlib import Path


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
    assert "github-release:kubernetes/kubernetes:v1.31.1" in snapshot["analyses"]


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
