from pathlib import Path


def test_health_endpoint_returns_ok(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore

    app = create_app(store=JsonStore(tmp_path), sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_read_events_endpoints_persist_events(tmp_path: Path):
    from datetime import datetime

    from backend.app import create_app
    from backend.storage import JsonStore

    app = create_app(store=JsonStore(tmp_path), sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    post_response = client.post(
        "/api/read-events",
        json={"project_id": "cilium", "event_id": "docs:cilium:intro"},
    )

    assert post_response.status_code == 201

    payload = client.get("/api/read-events").get_json()

    assert len(payload) == 1
    assert payload[0]["project_id"] == "cilium"
    assert payload[0]["event_id"] == "docs:cilium:intro"
    assert payload[0]["read_at"].endswith("Z")
    datetime.fromisoformat(payload[0]["read_at"].replace("Z", "+00:00"))


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
                "tech_categories": ["架构", "调度", "网络", "升级"],
                "focus_topics": ["虚拟化"],
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
    assert payload["overview"]["total_items"] == 4
    assert payload["overview"]["stable_items"] == 4
    assert payload["overview"]["last_fetch_success_at"] is None
    assert payload["overview"]["last_daily_digest_at"] is None
    assert payload["homepage_projects"][0]["project_id"] == "kubernetes"
    assert payload["homepage_projects"][0]["headline"] == "Kubernetes 今日重点：Kubernetes 1.31.1 补丁说明"
    assert payload["homepage_projects"][0]["evidence_items"][0]["title_zh"] == "Kubernetes 1.31.1 补丁说明"
    assert payload["recent_project_updates"] == []
    assert payload["daily_digest_history"] == []
    assert payload["projects"][0]["name"] == "Kubernetes"
    assert payload["projects"][0]["tech_categories"] == ["架构", "调度", "网络", "升级"]
    assert payload["projects"][0]["focus_topics"] == ["虚拟化"]
    assert payload["projects"][0]["release_area"]["items"][0]["version"] == "v1.31.1"
    assert payload["projects"][0]["release_area"]["items"][0]["summary_zh"] == "Kubernetes 1.31.1 比 1.31.0 更新。"
    assert payload["projects"][0]["release_area"]["items"][0]["published_at"] == "2026-03-10T10:00:00Z"
    assert [item["category"] for item in payload["projects"][0]["docs_area"]["categories"]] == ["网络"]
    assert payload["projects"][0]["docs_area"]["categories"][0]["items"][0]["title_zh"] == "网络策略文档更新"


def test_manual_sync_endpoint_returns_runner_result(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore

    app = create_app(
        store=JsonStore(tmp_path),
        sync_runner=lambda **_kwargs: {"new_events": 2, "analyzed_events": 2},
    )
    client = app.test_client()

    response = client.post("/api/sync")

    assert response.status_code == 202
    assert response.get_json()["status"] == "running"


def test_sync_runs_endpoints_list_detail_and_clear(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore
    from backend.sync_runs import SyncRunRecorder

    store = JsonStore(tmp_path)
    recorder = SyncRunRecorder(store)
    run_id = recorder.start_run(run_kind="manual", started_at="2026-03-13T00:00:00Z")
    recorder.record_source(
        run_id,
        {
            "kind": "repo",
            "label": "openclaw/openclaw",
            "url": "https://github.com/openclaw/openclaw",
            "status": "success",
            "metrics": {"new_events": 1, "analyzed_events": 1, "failed_events": 0},
            "error": None,
            "events": [
                {
                    "event_id": "github-release:openclaw/openclaw:v2026.3.12",
                    "title": "OpenClaw v2026.3.12",
                    "version": "v2026.3.12",
                    "url": "https://github.com/openclaw/openclaw",
                    "published_at": "2026-03-13T00:00:00Z",
                    "status": "analyzed",
                    "is_new": True,
                    "analysis": {"title_zh": "t", "summary_zh": "s", "urgency": "low", "action_items": []},
                    "error": None,
                }
            ],
        },
    )

    app = create_app(store=store, sync_runner=lambda **_kwargs: {"status": "noop"})
    client = app.test_client()

    list_response = client.get("/api/sync/runs?limit=5")
    list_payload = list_response.get_json()

    assert list_response.status_code == 200
    assert list_payload[0]["id"] == run_id
    assert "sources" not in list_payload[0]

    detail_response = client.get(f"/api/sync/runs/{run_id}")
    detail_payload = detail_response.get_json()

    assert detail_response.status_code == 200
    assert detail_payload["id"] == run_id
    assert detail_payload["sources"][0]["label"] == "openclaw/openclaw"

    clear_response = client.delete("/api/sync/runs")
    assert clear_response.status_code == 200
    assert clear_response.get_json()["runs"] == []
    assert client.get("/api/sync/runs").get_json() == []


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


def test_dashboard_returns_digest_history_and_recent_updates_separately(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_projects(
        [
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
                "created_at": "2026-03-10T12:00:00Z",
                "updated_at": "2026-03-10T12:00:00Z",
            }
        ]
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
            "published_at": "2026-03-11T09:00:00Z",
        }
    )
    store.save_analysis(
        "github-release:cilium/cilium:v1.20.0-pre.0",
        {
            "title_zh": "Cilium 1.20 预发布",
            "summary_zh": "高优先级变化。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["重大变更"]}],
            "impact_scope": "cluster",
            "impact_points": ["cluster"],
            "suggested_action": "验证升级。",
            "action_items": ["验证升级。"],
            "urgency": "high",
            "tags": ["cilium"],
            "is_stable": True,
        },
    )
    store.save_daily_project_summaries(
        {
            "2026-03-10:cilium": {
                "id": "2026-03-10:cilium",
                "date": "2026-03-10",
                "project_id": "cilium",
                "project_name": "Cilium",
                "headline": "昨日摘要",
                "summary_zh": "昨日内容。",
                "reason": "昨日原因。",
                "importance": "high",
                "evidence_ids": [],
                "evidence_items": [],
                "updated_at": "2026-03-10T08:00:00Z",
            }
        }
    )
    store.save_state(
        {
            "last_sync_at": "2026-03-11T09:30:00Z",
            "last_analysis_at": "2026-03-11T09:30:00Z",
            "last_fetch_success_at": "2026-03-11T09:30:00Z",
            "last_incremental_analysis_at": "2026-03-11T09:30:00Z",
            "last_daily_summary_at": "2026-03-10T08:00:00Z",
            "last_daily_digest_at": "2026-03-10T08:00:00Z",
            "last_heartbeat_at": "2026-03-11T09:30:00Z",
            "scheduler": {"running": True, "interval_minutes": 60},
        }
    )

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    payload = app.test_client().get("/api/dashboard").get_json()

    assert payload["homepage_projects"][0]["date"] == "2026-03-10"
    assert payload["daily_digest_history"][0]["date"] == "2026-03-10"
    assert payload["recent_project_updates"][0]["project_id"] == "cilium"
    assert payload["overview"]["last_daily_digest_at"] == "2026-03-10T08:00:00Z"
    assert payload["overview"]["last_incremental_analysis_at"] == "2026-03-11T09:30:00Z"


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

    assert versions[:6] == ["v1.35.2", "v1.32.13", "v1.33.9", "v1.34.5", "v1.35.1", "v1.36.0-alpha.2"]


def test_docs_endpoints_return_project_events_pages_and_diff(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_projects(
        [
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
                "created_at": "2026-03-15T10:00:00Z",
                "updated_at": "2026-03-15T10:00:00Z",
            }
        ]
    )
    store.save_docs_snapshots(
        {
            "openclaw": {
                "project_id": "openclaw",
                "source_key": "openclaw:docs",
                "updated_at": "2026-03-15T10:00:00Z",
                "pages": {
                    "https://openclaw.dev/docs/network": {
                        "id": "network-page",
                        "url": "https://openclaw.dev/docs/network",
                        "path": "/docs/network",
                        "title": "Network",
                        "section": "Network",
                        "category": "网络",
                        "extractor_hint": "furo",
                        "headings": ["Network", "Routing"],
                        "breadcrumbs": ["Docs", "Network"],
                        "summary": "network summary",
                        "text_content": "network summary",
                        "last_seen_at": "2026-03-15T10:00:00Z",
                    }
                },
            }
        }
    )
    store.save_event(
        {
            "id": "docs-feed:openclaw:docs:network:initial",
            "source": "docs_feed",
            "project_id": "openclaw",
            "source_key": "openclaw:docs",
            "event_kind": "docs_initial_read",
            "title": "OpenClaw 文档 · 网络 首次解读",
            "url": "https://openclaw.dev/docs/network",
            "content_hash": "initial-hash",
            "category": "网络",
            "published_at": "2026-03-15T09:00:00Z",
            "research_bundle": {
                "analysis_mode": "initial_read",
                "changed_pages": [
                    {
                        "page_id": "network-page",
                        "url": "https://openclaw.dev/docs/network",
                        "title_after": "Network",
                        "change_type": "added",
                    }
                ],
            },
        }
    )
    store.save_analysis(
        "docs-feed:openclaw:docs:network:initial",
        {
            "title_zh": "OpenClaw 文档首读",
            "summary_zh": "首读总结。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["文档覆盖网络能力"]}],
            "impact_scope": "network",
            "impact_points": ["network"],
            "suggested_action": "read",
            "action_items": ["read"],
            "urgency": "medium",
            "tags": ["docs"],
            "analysis_mode": "initial_read",
            "doc_summary": "覆盖网络主题。",
            "doc_key_points": ["先看网络章节"],
            "reading_guide": ["先读 Network 页面"],
            "changed_pages": [
                {
                    "url": "https://openclaw.dev/docs/network",
                    "title": "Network",
                    "change_type": "added",
                }
            ],
            "is_stable": True,
        },
    )
    store.save_event(
        {
            "id": "docs-feed:openclaw:docs:network:diff",
            "source": "docs_feed",
            "project_id": "openclaw",
            "source_key": "openclaw:docs",
            "event_kind": "docs_diff_update",
            "title": "OpenClaw 文档 · 网络 文档更新解读",
            "url": "https://openclaw.dev/docs/network",
            "content_hash": "diff-hash",
            "category": "网络",
            "published_at": "2026-03-15T10:00:00Z",
            "research_bundle": {
                "analysis_mode": "diff_update",
                "changed_pages": [
                    {
                        "page_id": "network-page",
                        "url": "https://openclaw.dev/docs/network",
                        "title_after": "Network",
                        "change_type": "changed",
                        "added_blocks": ["加入 docker compose 部署说明。"],
                        "removed_blocks": ["移除了旧版启动命令。"],
                        "before_summary": "旧说明",
                        "after_summary": "新说明",
                    }
                ],
            },
        }
    )
    store.save_analysis(
        "docs-feed:openclaw:docs:network:diff",
        {
            "title_zh": "OpenClaw 网络文档更新",
            "summary_zh": "更新了部署说明。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["更新 docker compose 说明"]}],
            "impact_scope": "network",
            "impact_points": ["network"],
            "suggested_action": "sync",
            "action_items": ["sync"],
            "urgency": "high",
            "tags": ["docs"],
            "analysis_mode": "diff_update",
            "doc_summary": "这次主要更新部署方式。",
            "doc_key_points": ["部署入口变了"],
            "diff_highlights": ["docker compose 成为推荐入口"],
            "reading_guide": ["先看 Network 页面 diff"],
            "changed_pages": [
                {
                    "url": "https://openclaw.dev/docs/network",
                    "title": "Network",
                    "change_type": "changed",
                    "after_summary": "新说明",
                }
            ],
            "is_stable": True,
        },
    )

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    projects_payload = client.get("/api/docs/projects").get_json()
    detail_payload = client.get("/api/docs/projects/openclaw").get_json()
    events_payload = client.get("/api/docs/projects/openclaw/events?mode=docs_diff_update").get_json()
    pages_payload = client.get("/api/docs/projects/openclaw/pages").get_json()
    diff_payload = client.get("/api/docs/projects/openclaw/pages/network-page/diff").get_json()

    assert projects_payload[0]["project_id"] == "openclaw"
    assert detail_payload["initial_read"]["analysis_mode"] == "initial_read"
    assert detail_payload["initial_read"]["changed_pages"][0]["page_id"] == "network-page"
    assert detail_payload["latest_update"]["analysis_mode"] == "diff_update"
    assert detail_payload["latest_update"]["changed_pages"][0]["page_id"] == "network-page"
    assert events_payload[0]["event_kind"] == "docs_diff_update"
    assert events_payload[0]["changed_pages"][0]["page_id"] == "network-page"
    assert pages_payload[0]["id"] == "network-page"
    assert diff_payload["latest_diff"]["change_type"] == "changed"


def test_docs_pages_ignore_initial_read_when_marking_recent_changes(tmp_path):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_projects(
        [
            {
                "id": "openclaw",
                "name": "OpenClaw",
                "repo": "openclaw/openclaw",
                "repo_url": "https://github.com/openclaw/openclaw",
                "docs_url": "https://openclaw.dev/docs",
                "enabled": True,
                "release_area_enabled": True,
                "docs_area_enabled": True,
                "sync_interval_minutes": 60,
                "created_at": "2026-03-15T10:00:00Z",
                "updated_at": "2026-03-15T10:00:00Z",
            }
        ]
    )
    store.save_docs_snapshots(
        {
            "openclaw": {
                "project_id": "openclaw",
                "source_key": "openclaw:docs",
                "updated_at": "2026-03-15T10:00:00Z",
                "pages": {
                    "https://openclaw.dev/docs/network": {
                        "id": "network-page",
                        "url": "https://openclaw.dev/docs/network",
                        "path": "/docs/network",
                        "title": "Network",
                        "section": "Network",
                        "category": "网络",
                        "extractor_hint": "furo",
                        "headings": ["Network", "Routing"],
                        "breadcrumbs": ["Docs", "Network"],
                        "summary": "network summary",
                        "text_content": "network summary",
                        "last_seen_at": "2026-03-15T10:00:00Z",
                    }
                },
            }
        }
    )
    store.save_event(
        {
            "id": "docs-feed:openclaw:docs:network:initial",
            "source": "docs_feed",
            "project_id": "openclaw",
            "source_key": "openclaw:docs",
            "event_kind": "docs_initial_read",
            "title": "OpenClaw 文档 · 网络 首次解读",
            "url": "https://openclaw.dev/docs/network",
            "content_hash": "initial-hash",
            "category": "网络",
            "published_at": "2026-03-15T09:00:00Z",
            "research_bundle": {
                "analysis_mode": "initial_read",
                "changed_pages": [
                    {
                        "page_id": "network-page",
                        "url": "https://openclaw.dev/docs/network",
                        "title_after": "Network",
                        "change_type": "added",
                    }
                ],
            },
        }
    )
    store.save_analysis(
        "docs-feed:openclaw:docs:network:initial",
        {
            "title_zh": "OpenClaw 文档首读",
            "summary_zh": "首读总结。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["文档覆盖网络能力"]}],
            "impact_scope": "network",
            "impact_points": ["network"],
            "suggested_action": "read",
            "action_items": ["read"],
            "urgency": "medium",
            "tags": ["docs"],
            "analysis_mode": "initial_read",
            "doc_summary": "覆盖网络主题。",
            "doc_key_points": ["先看网络章节"],
            "reading_guide": ["先读 Network 页面"],
            "changed_pages": [
                {
                    "url": "https://openclaw.dev/docs/network",
                    "title": "Network",
                    "change_type": "added",
                }
            ],
            "is_stable": True,
        },
    )

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    pages_payload = client.get("/api/docs/projects/openclaw/pages").get_json()

    assert pages_payload[0]["id"] == "network-page"
    assert pages_payload[0]["latest_change"] is None
    assert pages_payload[0]["is_recently_changed"] is False


def test_config_response_includes_effective_values_and_key_source(tmp_path: Path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    monkeypatch.setenv("PACKY_API_KEY", "sk-packy-1234567890")
    monkeypatch.setenv("PACKY_API_URL", "https://env.packy.test/v1/messages")
    monkeypatch.setenv("PACKY_MODEL", "claude-opus-4-6")

    store = JsonStore(tmp_path)
    app = create_app(store=store, sync_runner=lambda **_kwargs: {"status": "noop"})
    client = app.test_client()

    response = client.get("/api/config")
    payload = response.get_json()

    assert payload["llm"]["packy"]["api_key_masked"] == "sk-p****7890"
    assert payload["llm"]["packy"]["api_key_source"] == "env"
    assert payload["llm"]["packy"]["effective_api_url"] == "https://env.packy.test/v1/messages"
    assert payload["llm"]["packy"]["effective_model"] == "claude-opus-4-6"
