from pathlib import Path


def test_assistant_query_endpoint_returns_structured_local_answer(tmp_path: Path):
    from backend.app import create_app
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
            "created_at": "2026-03-09T12:40:00Z",
            "updated_at": "2026-03-09T12:40:00Z",
        }
    )
    store.save_event(
        {
            "id": "github-release:openclaw/openclaw:v2026.3.8",
            "project_id": "openclaw",
            "source": "github_release",
            "repo": "openclaw/openclaw",
            "source_key": "openclaw/openclaw",
            "title": "OpenClaw v2026.3.8",
            "version": "v2026.3.8",
            "url": "https://example.com/openclaw/v2026.3.8",
            "published_at": "2026-03-08T10:00:00Z",
        }
    )
    store.save_event(
        {
            "id": "docs-feed:openclaw:docs:https://example.com/network",
            "project_id": "openclaw",
            "source": "docs_feed",
            "source_key": "openclaw:docs",
            "title": "Network guide",
            "url": "https://example.com/network",
            "category": "网络",
            "body": "network agent policy routing",
            "published_at": "2026-03-07T10:00:00Z",
        }
    )
    store.save_analysis(
        "github-release:openclaw/openclaw:v2026.3.8",
        {
            "title_zh": "OpenClaw v2026.3.8 发布",
            "summary_zh": "新增本地状态备份和验证命令。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["新增 backup create 和 verify 命令"]}],
            "impact_points": ["升级和运维流程"],
            "action_items": ["验证现有备份脚本。"],
            "urgency": "high",
            "tags": ["openclaw", "升级"],
            "is_stable": True,
        },
    )
    store.save_analysis(
        "docs-feed:openclaw:docs:https://example.com/network",
        {
            "title_zh": "OpenClaw 网络文档更新",
            "summary_zh": "新增网络策略与路由说明。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["补充网络策略示例"]}],
            "impact_points": ["网络配置"],
            "action_items": ["检查网络策略默认值。"],
            "urgency": "medium",
            "tags": ["openclaw", "网络"],
            "is_stable": True,
        },
    )

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.post(
        "/api/assistant/query",
        json={
            "query": "OpenClaw 最近网络相关有什么变化？",
            "project_ids": ["openclaw"],
            "categories": ["网络"],
            "timeframe": "30d",
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert "OpenClaw" in payload["answer"]
    assert payload["applied_filters"] == {
        "mode": "hybrid",
        "project_ids": ["openclaw"],
        "categories": ["网络"],
        "timeframe": "30d",
    }
    assert payload["evidence"][0]["title"] == "OpenClaw 网络文档更新"
    assert payload["evidence"][0]["source"] == "docs_feed"
    assert payload["next_steps"] == ["检查网络策略默认值。", "验证现有备份脚本。"]
    assert payload["sources"][0]["url"] == "https://example.com/network"


def test_assistant_query_endpoint_supports_hybrid_mode_with_live_search(tmp_path: Path, monkeypatch):
    from backend.app import create_app
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
            "created_at": "2026-03-09T12:40:00Z",
            "updated_at": "2026-03-09T12:40:00Z",
        }
    )
    store.save_event(
        {
            "id": "github-release:openclaw/openclaw:v2026.3.8",
            "project_id": "openclaw",
            "source": "github_release",
            "repo": "openclaw/openclaw",
            "source_key": "openclaw/openclaw",
            "title": "OpenClaw v2026.3.8",
            "version": "v2026.3.8",
            "url": "https://example.com/openclaw/v2026.3.8",
            "published_at": "2026-03-08T10:00:00Z",
        }
    )
    store.save_analysis(
        "github-release:openclaw/openclaw:v2026.3.8",
        {
            "title_zh": "OpenClaw v2026.3.8 发布",
            "summary_zh": "新增本地状态备份和验证命令。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["新增 backup create 和 verify 命令"]}],
            "impact_points": ["升级和运维流程"],
            "action_items": ["验证现有备份脚本。"],
            "urgency": "high",
            "tags": ["openclaw", "升级"],
            "is_stable": True,
        },
    )

    monkeypatch.setattr(
        "backend.assistant.search_web",
        lambda query, max_results=5: [
            {
                "title": "OpenClaw blog post",
                "url": "https://example.com/blog/openclaw",
                "snippet": "OpenClaw added realtime policy checks",
            }
        ],
    )
    monkeypatch.setattr(
        "backend.assistant.fetch_search_result_pages",
        lambda results, max_pages=3: [
            {
                "title": "OpenClaw blog post",
                "url": "https://example.com/blog/openclaw",
                "excerpt": "Realtime policy checks and new routing docs",
            }
        ],
    )
    monkeypatch.setattr(
        "backend.assistant.answer_with_context",
        lambda **kwargs: {
            "answer": "结合本地知识和实时网页结果，OpenClaw 最近补充了实时策略检查。",
            "next_steps": ["阅读实时策略检查文档。"],
        },
    )

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.post(
        "/api/assistant/query",
        json={
            "query": "OpenClaw 最近还有什么新变化？",
            "project_ids": ["openclaw"],
            "categories": [],
            "timeframe": "30d",
            "mode": "hybrid",
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["answer"].startswith("结合本地知识和实时网页结果")
    assert payload["applied_filters"]["mode"] == "hybrid"
    assert payload["sources"][-1]["url"] == "https://example.com/blog/openclaw"
    assert payload["next_steps"] == ["阅读实时策略检查文档。"]


def test_assistant_query_endpoint_falls_back_to_local_when_live_answer_fails(tmp_path: Path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    store.save_project(
        {
            "id": "openclaw",
            "name": "OpenClaw",
            "github_url": "https://github.com/openclaw/openclaw",
            "repo": "openclaw/openclaw",
            "docs_url": "",
            "enabled": True,
            "release_area_enabled": True,
            "docs_area_enabled": False,
            "sync_interval_minutes": 60,
            "created_at": "2026-03-09T12:40:00Z",
            "updated_at": "2026-03-09T12:40:00Z",
        }
    )
    store.save_event(
        {
            "id": "github-release:openclaw/openclaw:v2026.3.8",
            "project_id": "openclaw",
            "source": "github_release",
            "repo": "openclaw/openclaw",
            "source_key": "openclaw/openclaw",
            "title": "OpenClaw v2026.3.8",
            "version": "v2026.3.8",
            "url": "https://example.com/openclaw/v2026.3.8",
            "published_at": "2026-03-08T10:00:00Z",
        }
    )
    store.save_analysis(
        "github-release:openclaw/openclaw:v2026.3.8",
        {
            "title_zh": "OpenClaw v2026.3.8 发布",
            "summary_zh": "新增本地状态备份和验证命令。",
            "detail_sections": [{"title": "核心变化点", "bullets": ["新增 backup create 和 verify 命令"]}],
            "impact_points": ["升级和运维流程"],
            "action_items": ["验证现有备份脚本。"],
            "urgency": "high",
            "tags": ["openclaw", "升级"],
            "is_stable": True,
        },
    )

    monkeypatch.setattr("backend.assistant.search_web", lambda query, max_results=5: [])
    monkeypatch.setattr("backend.assistant.fetch_search_result_pages", lambda results, max_pages=3: [])
    monkeypatch.setattr("backend.assistant.answer_with_context", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("llm error")))

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.post(
        "/api/assistant/query",
        json={
            "query": "OpenClaw 最近有什么变化？",
            "project_ids": ["openclaw"],
            "categories": [],
            "timeframe": "30d",
            "mode": "hybrid",
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert "OpenClaw" in payload["answer"]
    assert payload["applied_filters"]["mode"] == "hybrid"
    assert payload["evidence"][0]["title"] == "OpenClaw v2026.3.8 发布"
