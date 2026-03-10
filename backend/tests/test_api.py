from pathlib import Path


def test_health_endpoint_returns_ok(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore

    app = create_app(store=JsonStore(tmp_path), sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_dashboard_endpoint_returns_grouped_chinese_analysis(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.31.0",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "source_key": "kubernetes/kubernetes",
            "title": "Kubernetes v1.31.0",
            "version": "v1.31.0",
            "url": "https://example.com/v1.31.0",
            "content_hash": "hash-1",
            "published_at": "2026-03-09T10:00:00Z",
        }
    )
    store.save_event(
        {
            "id": "github-release:kubernetes/kubernetes:v1.31.1",
            "source": "github_release",
            "repo": "kubernetes/kubernetes",
            "source_key": "kubernetes/kubernetes",
            "title": "Kubernetes v1.31.1",
            "version": "v1.31.1",
            "url": "https://example.com/v1.31.1",
            "content_hash": "hash-1-1",
            "published_at": "2026-03-10T10:00:00Z",
        }
    )
    store.save_event(
        {
            "id": "docs-feed:kubernetes:docs:https://example.com/docs/network",
            "source": "docs_feed",
            "project_id": "kubernetes",
            "source_key": "kubernetes:docs",
            "title": "Network Policies",
            "url": "https://example.com/docs/network",
            "content_hash": "hash-2",
            "category": "网络",
            "body": "CNI kube-proxy nftables network policy",
            "published_at": "2026-03-09T11:00:00Z",
        }
    )
    store.save_event(
        {
            "id": "docs-feed:kubernetes:docs:https://example.com/docs/concepts",
            "source": "docs_feed",
            "project_id": "kubernetes",
            "source_key": "kubernetes:docs",
            "title": "概念",
            "url": "https://example.com/docs/concepts",
            "content_hash": "hash-3",
            "category": "其他",
            "body": "generic landing page",
            "published_at": "2026-03-08T11:00:00Z",
        }
    )
    store.save_analysis(
        "github-release:kubernetes/kubernetes:v1.31.0",
        {
            "title_zh": "Kubernetes 1.31 网络推荐变化",
            "summary_zh": "Kubernetes 1.31 推荐使用 nftables 路径。",
            "details_zh": "**核心变化点：**\n\n1. **网络变化**\n   - 推荐使用 nftables 路径",
            "impact_scope": "Kubernetes 网络层",
            "suggested_action": "1. 检查网络插件兼容性。\n2. 验证节点内核支持。",
            "urgency": "medium",
            "tags": ["kubernetes", "networking"],
            "is_stable": True,
        },
    )
    store.save_analysis(
        "github-release:kubernetes/kubernetes:v1.31.1",
        {
            "title_zh": "Kubernetes 1.31.1 补丁说明",
            "summary_zh": "Kubernetes 1.31.1 比 1.31.0 更新。",
            "details_zh": "补丁版本内容。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["较新补丁"]}],
            "impact_scope": "Kubernetes 网络层",
            "impact_points": ["Kubernetes 网络层"],
            "suggested_action": "升级。",
            "action_items": ["升级。"],
            "urgency": "low",
            "tags": ["kubernetes"],
            "is_stable": True,
        },
    )
    store.save_analysis(
        "docs-feed:kubernetes:docs:https://example.com/docs/network",
        {
            "title_zh": "网络策略文档更新",
            "summary_zh": "文档强调了网络策略和 CNI 相关行为。",
            "details_zh": "网络分类下的一条文档结论。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["网络策略行为说明"]}],
            "impact_scope": "Kubernetes 网络层",
            "impact_points": ["Kubernetes 网络层"],
            "suggested_action": "检查网络策略配置。",
            "action_items": ["检查网络策略配置。"],
            "urgency": "low",
            "tags": ["kubernetes", "network"],
            "is_stable": True,
        },
    )
    store.save_analysis(
        "docs-feed:kubernetes:docs:https://example.com/docs/concepts",
        {
            "title_zh": "文档概览更新",
            "summary_zh": "通用目录页变化。",
            "details_zh": "低价值概览页。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["概览页变化"]}],
            "impact_scope": "Kubernetes 文档",
            "impact_points": ["Kubernetes 文档"],
            "suggested_action": "忽略。",
            "action_items": ["忽略。"],
            "urgency": "low",
            "tags": ["kubernetes"],
            "is_stable": True,
        },
    )
    store.save_projects(
        [
            {
                "id": "kubernetes",
                "name": "Kubernetes",
                "github_url": "https://github.com/kubernetes/kubernetes",
                "repo": "kubernetes/kubernetes",
                "docs_url": "https://example.com/docs",
                "enabled": True,
                "release_area_enabled": True,
                "docs_area_enabled": True,
                "sync_interval_minutes": 60,
                "created_at": "2026-03-09T12:00:00Z",
                "updated_at": "2026-03-09T12:00:00Z",
            }
        ]
    )
    store.save_crawl_profile(
        "kubernetes",
        {
            "entry_urls": ["https://example.com/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 2,
        },
    )
    store.save_state(
        {
            "last_sync_at": "2026-03-09T12:00:00Z",
            "last_analysis_at": "2026-03-09T12:00:00Z",
            "scheduler": {"running": True, "interval_minutes": 60},
        }
    )

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.get("/api/dashboard")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["overview"]["total_items"] == 3
    assert payload["overview"]["stable_items"] == 3
    assert payload["homepage_projects"][0]["project_id"] == "kubernetes"
    assert payload["homepage_projects"][0]["headline"] == "Kubernetes 今日重点：Kubernetes 1.31.1 补丁说明"
    assert payload["homepage_projects"][0]["evidence_items"][0]["title_zh"] == "Kubernetes 1.31.1 补丁说明"
    assert payload["projects"][0]["name"] == "Kubernetes"
    assert payload["projects"][0]["release_area"]["items"][0]["version"] == "v1.31.1"
    assert payload["projects"][0]["release_area"]["items"][0]["summary_zh"] == "Kubernetes 1.31.1 比 1.31.0 更新。"
    assert [item["category"] for item in payload["projects"][0]["docs_area"]["categories"]] == ["网络"]
    assert payload["projects"][0]["docs_area"]["categories"][0]["items"][0]["title_zh"] == "网络策略文档更新"


def test_manual_sync_endpoint_returns_runner_result(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore

    app = create_app(
        store=JsonStore(tmp_path),
        sync_runner=lambda: {"new_events": 2, "analyzed_events": 2},
    )
    client = app.test_client()

    response = client.post("/api/sync")

    assert response.status_code == 200
    assert response.get_json()["analyzed_events"] == 2


def test_dashboard_resorts_homepage_projects_after_backfilling_missing_summaries(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_projects(
        [
            {
                "id": "low-project",
                "name": "Low Project",
                "github_url": "https://example.com/low",
                "repo": "example/low",
                "docs_url": "",
                "enabled": True,
                "release_area_enabled": True,
                "docs_area_enabled": False,
                "sync_interval_minutes": 60,
                "created_at": "2026-03-09T12:00:00Z",
                "updated_at": "2026-03-09T12:00:00Z",
            },
            {
                "id": "high-project",
                "name": "High Project",
                "github_url": "https://example.com/high",
                "repo": "example/high",
                "docs_url": "",
                "enabled": True,
                "release_area_enabled": True,
                "docs_area_enabled": False,
                "sync_interval_minutes": 60,
                "created_at": "2026-03-09T12:00:00Z",
                "updated_at": "2026-03-09T12:00:00Z",
            },
        ]
    )
    store.save_daily_project_summaries(
        {
            "2026-03-10:low-project": {
                "id": "2026-03-10:low-project",
                "date": "2026-03-10",
                "project_id": "low-project",
                "project_name": "Low Project",
                "headline": "Low Project 近期待关注：旧条目",
                "summary_zh": "旧低优先级摘要。",
                "reason": "低优先级。",
                "importance": "low",
                "evidence_ids": [],
                "evidence_items": [],
                "updated_at": "2026-03-10T08:00:00Z",
            }
        }
    )
    store.save_event(
        {
            "id": "github-release:example/high:v2.0.0",
            "source": "github_release",
            "repo": "example/high",
            "source_key": "example/high",
            "title": "High 2.0.0",
            "version": "v2.0.0",
            "url": "https://example.com/high/v2.0.0",
            "content_hash": "hash-high",
            "published_at": "2026-03-10T10:00:00Z",
        }
    )
    store.save_analysis(
        "github-release:example/high:v2.0.0",
        {
            "title_zh": "High Project 核心升级",
            "summary_zh": "高优先级变化。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["重大变更"]}],
            "impact_scope": "cluster",
            "impact_points": ["cluster"],
            "suggested_action": "验证升级。",
            "action_items": ["验证升级。"],
            "urgency": "high",
            "tags": ["high"],
            "is_stable": True,
        },
    )
    store.save_state(
        {
            "last_sync_at": "2026-03-10T10:00:00Z",
            "last_analysis_at": "2026-03-10T10:00:00Z",
            "last_daily_summary_at": "2026-03-09T23:00:00Z",
            "scheduler": {"running": True, "interval_minutes": 60},
        }
    )

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    payload = client.get("/api/dashboard").get_json()

    assert [item["project_id"] for item in payload["homepage_projects"][:2]] == ["high-project", "low-project"]


def test_dashboard_orders_release_items_by_stable_semver_not_publish_time(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_projects(
        [
            {
                "id": "kubernetes",
                "name": "Kubernetes",
                "github_url": "https://github.com/kubernetes/kubernetes",
                "repo": "kubernetes/kubernetes",
                "docs_url": "",
                "enabled": True,
                "release_area_enabled": True,
                "docs_area_enabled": False,
                "sync_interval_minutes": 60,
                "created_at": "2026-03-09T12:00:00Z",
                "updated_at": "2026-03-09T12:00:00Z",
            }
        ]
    )

    for version, published_at in [
        ("v1.35.2", "2026-02-27T00:09:07Z"),
        ("v1.32.13", "2026-02-26T23:58:24Z"),
        ("v1.33.9", "2026-02-26T23:57:29Z"),
        ("v1.34.5", "2026-02-26T23:56:38Z"),
        ("v1.35.1", "2026-02-10T19:03:38Z"),
        ("v1.36.0-alpha.2", "2026-02-26T14:31:43Z"),
    ]:
        event_id = f"github-release:kubernetes/kubernetes:{version}"
        store.save_event(
            {
                "id": event_id,
                "source": "github_release",
                "repo": "kubernetes/kubernetes",
                "source_key": "kubernetes/kubernetes",
                "title": version,
                "version": version,
                "url": f"https://example.com/{version}",
                "content_hash": f"hash-{version}",
                "published_at": published_at,
            }
        )
        store.save_analysis(
            event_id,
            {
                "title_zh": version,
                "summary_zh": version,
                "details_zh": version,
                "impact_scope": "cluster",
                "suggested_action": "check",
                "urgency": "medium",
                "tags": ["kubernetes"],
                "is_stable": not version.endswith("alpha.2"),
            },
        )

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    payload = client.get("/api/dashboard").get_json()
    versions = [item["version"] for item in payload["projects"][0]["release_area"]["items"]]

    assert versions[:6] == ["v1.35.2", "v1.35.1", "v1.34.5", "v1.33.9", "v1.32.13", "v1.36.0-alpha.2"]
