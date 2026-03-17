from pathlib import Path


def _seed_project(store, project_id: str, name: str, repo: str = "", docs_url: str = ""):
    store.save_project(
        {
            "id": project_id,
            "name": name,
            "github_url": f"https://github.com/{repo}" if repo else "",
            "repo": repo,
            "docs_url": docs_url,
            "enabled": True,
            "release_area_enabled": bool(repo),
            "docs_area_enabled": bool(docs_url),
            "sync_interval_minutes": 60,
            "created_at": "2026-03-09T12:40:00Z",
            "updated_at": "2026-03-09T12:40:00Z",
        }
    )


def _seed_release(store, project_id: str, repo: str, version: str, title: str, published_at: str, summary: str):
    event_id = f"github-release:{repo}:{version}"
    store.save_event(
        {
            "id": event_id,
            "project_id": project_id,
            "source": "github_release",
            "repo": repo,
            "source_key": repo,
            "title": title,
            "version": version,
            "url": f"https://example.com/{project_id}/{version}",
            "published_at": published_at,
        }
    )
    store.save_analysis(
        event_id,
        {
            "title_zh": title,
            "summary_zh": summary,
            "detail_sections": [{"title": "核心变化点", "bullets": [summary]}],
            "impact_points": ["升级和运维流程"],
            "action_items": ["继续跟进。"],
            "urgency": "high",
            "tags": [project_id, "升级"],
            "is_stable": True,
        },
    )


def test_assistant_query_endpoint_returns_live_report_and_filters_unrelated_evidence(tmp_path: Path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    _seed_project(store, "openclaw", "OpenClaw", repo="openclaw/openclaw", docs_url="https://openclaw.dev/docs")
    _seed_project(store, "cuda-toolkit", "CUDA 工具链", docs_url="https://docs.nvidia.com/cuda/")
    _seed_release(
        store,
        "openclaw",
        "openclaw/openclaw",
        "v2026.3.13",
        "OpenClaw v2026.3.13",
        "2026-03-14T05:19:41Z",
        "修复 WebSocket 劫持并新增多模态记忆索引。",
    )
    _seed_release(
        store,
        "cuda-toolkit",
        "",
        "13.2",
        "CUDA Toolkit 13.2 文档发布",
        "2026-03-09T16:23:25Z",
        "新增 Blackwell 架构支持与 cuTile Python。",
    )

    monkeypatch.setattr(
        "backend.assistant.search_web",
        lambda query, max_results=5: [
            {"title": "OpenClaw 2026.3.13 release", "url": "https://example.com/openclaw/release", "snippet": "OpenClaw update"},
            {"title": "CUDA Toolkit 13.2", "url": "https://example.com/cuda/13.2", "snippet": "CUDA update"},
        ],
    )
    monkeypatch.setattr(
        "backend.assistant.fetch_search_result_pages",
        lambda results, max_pages=3: [
            {
                "title": "OpenClaw 2026.3.13 release",
                "url": "https://example.com/openclaw/release",
                "excerpt": "OpenClaw 2026.3.13 fixes Telegram SSRF and improves multimodal memory index.",
            },
            {
                "title": "CUDA Toolkit 13.2",
                "url": "https://example.com/cuda/13.2",
                "excerpt": "CUDA 13.2 adds Blackwell architecture support.",
            },
        ],
    )
    monkeypatch.setattr(
        "backend.assistant.fetch_page_content",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("seed unavailable")),
    )

    app = create_app(store=store, sync_runner=lambda **_kwargs: {"status": "noop"})
    client = app.test_client()

    response = client.post("/api/assistant/query", json={"query": "openclaw最近更新了几次 主要方向是什么", "timeframe": "30d"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["applied_filters"]["mode"] == "live"
    assert payload["applied_plan"]["primary_entities"] == ["openclaw"]
    assert payload["report_markdown"].startswith("## 结论摘要")
    assert payload["evidence"]
    assert all(item["project_id"] == "openclaw" for item in payload["evidence"])
    assert all(item["relation_to_query"] != "unrelated" for item in payload["evidence"])
    assert payload["sources"][0]["url"] == "https://example.com/openclaw/release"


def test_build_research_report_surfaces_llm_error(monkeypatch):
    from backend.assistant import _build_research_report
    from backend.llm import LLMRequestError

    def boom(**_kwargs):
        raise LLMRequestError("Invalid API key")

    monkeypatch.setattr("backend.assistant.generate_live_research_report", boom)

    report = _build_research_report(
        query="test",
        filters={},
        plan={"primary_entities": [], "timeframe": "14d"},
        evidence=[],
        llm_config={},
        answer_prompt="",
    )

    assert "Invalid API key" in report["report_markdown"]


def test_assistant_query_endpoint_allows_related_cross_project_evidence(tmp_path: Path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    _seed_project(store, "vllm", "vLLM", repo="vllm-project/vllm", docs_url="https://docs.vllm.ai/")
    _seed_project(store, "cuda-toolkit", "CUDA 工具链", docs_url="https://docs.nvidia.com/cuda/")
    _seed_release(
        store,
        "vllm",
        "vllm-project/vllm",
        "v0.9.0",
        "vLLM 0.9.0",
        "2026-03-12T08:00:00Z",
        "新增 Blackwell 相关推理能力。",
    )

    monkeypatch.setattr(
        "backend.assistant.search_web",
        lambda query, max_results=5: [
            {"title": "vLLM Blackwell support", "url": "https://example.com/vllm/blackwell", "snippet": "vLLM update"},
            {"title": "CUDA 13.2 Blackwell support", "url": "https://example.com/cuda/blackwell", "snippet": "CUDA update"},
        ],
    )
    monkeypatch.setattr(
        "backend.assistant.fetch_search_result_pages",
        lambda results, max_pages=3: [
            {
                "title": "vLLM Blackwell support",
                "url": "https://example.com/vllm/blackwell",
                "excerpt": "vLLM adds runtime tuning for Blackwell inference deployment.",
            },
            {
                "title": "CUDA 13.2 Blackwell support",
                "url": "https://example.com/cuda/blackwell",
                "excerpt": "CUDA 13.2 introduces Blackwell support required by the latest vLLM deployment guides.",
            },
        ],
    )

    app = create_app(store=store, sync_runner=lambda **_kwargs: {"status": "noop"})
    client = app.test_client()

    response = client.post("/api/assistant/query", json={"query": "vllm 最新支持了哪些架构，和 CUDA 有什么关系？", "timeframe": "30d"})
    payload = response.get_json()

    assert response.status_code == 200
    project_ids = {item["project_id"] for item in payload["evidence"]}
    assert "vllm" in project_ids
    assert "cuda-toolkit" in project_ids
    cuda_evidence = next(item for item in payload["evidence"] if item["project_id"] == "cuda-toolkit")
    assert cuda_evidence["relation_to_query"] == "supports_primary_project"
    assert "CUDA" in payload["report_markdown"]


def test_assistant_query_endpoint_returns_browser_trace_when_http_extraction_is_weak(tmp_path: Path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    _seed_project(store, "openclaw", "OpenClaw", repo="openclaw/openclaw", docs_url="https://openclaw.dev/docs")
    _seed_release(
        store,
        "openclaw",
        "openclaw/openclaw",
        "v2026.3.13",
        "OpenClaw v2026.3.13",
        "2026-03-14T05:19:41Z",
        "修复 WebSocket 劫持并新增多模态记忆索引。",
    )

    monkeypatch.setattr(
        "backend.assistant.search_web",
        lambda query, max_results=5: [
            {"title": "OpenClaw release note", "url": "https://example.com/openclaw/release", "snippet": "release note"}
        ],
    )
    monkeypatch.setattr(
        "backend.assistant.fetch_search_result_pages",
        lambda results, max_pages=3: [
            {"title": "OpenClaw release note", "url": "https://example.com/openclaw/release", "excerpt": "short"}
        ],
    )

    app = create_app(store=store, sync_runner=lambda **_kwargs: {"status": "noop"})
    client = app.test_client()

    response = client.post("/api/assistant/query", json={"query": "openclaw 最近更新方向", "timeframe": "30d"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["search_trace"]
    assert any(item["fetch_mode"] == "browser" for item in payload["search_trace"])


def test_assistant_query_endpoint_gracefully_handles_search_failures(tmp_path: Path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    _seed_project(store, "openclaw", "OpenClaw", repo="openclaw/openclaw", docs_url="https://openclaw.dev/docs")
    _seed_release(
        store,
        "openclaw",
        "openclaw/openclaw",
        "v2026.3.13",
        "OpenClaw v2026.3.13",
        "2026-03-14T05:19:41Z",
        "修复 WebSocket 劫持并新增多模态记忆索引。",
    )

    def boom(*_args, **_kwargs):
        raise RuntimeError("search failed")

    monkeypatch.setattr("backend.assistant.search_web", boom)
    monkeypatch.setattr(
        "backend.assistant.fetch_page_content",
        lambda url, title="": {
            "title": title or "OpenClaw project page",
            "url": url,
            "excerpt": "OpenClaw 2026.3.13 fixes Telegram SSRF and improves multimodal memory index.",
        },
    )

    app = create_app(store=store, sync_runner=lambda **_kwargs: {"status": "noop"})
    client = app.test_client()

    response = client.post("/api/assistant/query", json={"query": "openclaw 最近更新方向", "timeframe": "30d"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["applied_filters"]["mode"] == "live"
    assert payload["applied_plan"]["primary_entities"] == ["openclaw"]
    assert payload["report_markdown"].startswith("## 结论摘要")
    assert payload["evidence"]
    assert all(item["project_id"] == "openclaw" for item in payload["evidence"])
    assert payload["search_trace"]
    assert any(item["fetch_mode"] == "project_seed" for item in payload["search_trace"])


def test_assistant_query_endpoint_uses_project_cache_when_live_fetch_is_unavailable(tmp_path: Path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    _seed_project(store, "openclaw", "OpenClaw", repo="openclaw/openclaw", docs_url="https://openclaw.dev/docs")
    _seed_release(
        store,
        "openclaw",
        "openclaw/openclaw",
        "v2026.3.13",
        "OpenClaw v2026.3.13",
        "2026-03-14T05:19:41Z",
        "修复 WebSocket 劫持并新增多模态记忆索引。",
    )

    def boom(*_args, **_kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("backend.assistant.search_web", boom)
    monkeypatch.setattr("backend.assistant.fetch_page_content", boom)

    app = create_app(store=store, sync_runner=lambda **_kwargs: {"status": "noop"})
    client = app.test_client()

    response = client.post("/api/assistant/query", json={"query": "openclaw 最近更新方向", "timeframe": "30d"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["evidence"]
    assert payload["evidence"][0]["project_id"] == "openclaw"
    assert payload["evidence"][0]["source"] == "github_release"
    assert any(item["fetch_mode"] == "cache_fallback" for item in payload["search_trace"])
