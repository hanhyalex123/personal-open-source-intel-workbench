from pathlib import Path


def test_projects_endpoint_lists_saved_projects(tmp_path: Path):
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

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.get("/api/projects")

    assert response.status_code == 200
    assert response.get_json()[0]["repo"] == "openclaw/openclaw"


def test_projects_endpoint_creates_project_and_default_crawl_profile(tmp_path: Path):
    from backend.app import create_app
    from backend.storage import JsonStore

    store = JsonStore(tmp_path)
    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.post(
        "/api/projects",
        json={
            "name": "OpenClaw",
            "github_url": "https://github.com/openclaw/openclaw",
            "docs_url": "https://openclaw.dev/docs",
        },
    )

    snapshot = store.load_all()

    assert response.status_code == 201
    assert snapshot["projects"][0]["repo"] == "openclaw/openclaw"
    assert snapshot["projects"][0]["tech_categories"] == ["AI工具"]
    assert snapshot["projects"][0]["focus_topics"] == ["Agent", "大模型推理部署"]
    assert snapshot["crawl_profiles"]["openclaw"]["entry_urls"] == ["https://openclaw.dev/docs"]


def test_projects_endpoint_updates_project_categories_and_topics(tmp_path: Path):
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
            "tech_categories": ["AI工具"],
            "focus_topics": ["Agent"],
            "sync_interval_minutes": 60,
            "created_at": "2026-03-09T12:40:00Z",
            "updated_at": "2026-03-09T12:40:00Z",
        }
    )

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.put(
        "/api/projects/openclaw",
        json={
            "tech_categories": ["AI工具", "运行时"],
            "focus_topics": ["Agent", "大模型推理部署"],
        },
    )

    snapshot = store.load_all()

    assert response.status_code == 200
    assert snapshot["projects"][0]["tech_categories"] == ["AI工具", "运行时"]
    assert snapshot["projects"][0]["focus_topics"] == ["Agent", "大模型推理部署"]


def test_projects_endpoint_builds_crawl_profile_from_docs_homepage(tmp_path: Path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    monkeypatch.setattr(
        "backend.app.generate_crawl_profile",
        lambda project: {
            "entry_urls": [project["docs_url"]],
            "allowed_path_prefixes": ["/docs", "/guide"],
            "blocked_path_prefixes": ["/blog"],
            "max_depth": 3,
            "max_pages": 40,
            "expand_mode": "auto",
            "category_hints": ["网络", "存储"],
            "discovery_prompt": "discover",
            "classification_prompt": "classify",
        },
    )

    store = JsonStore(tmp_path)
    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.post(
        "/api/projects",
        json={
            "name": "Kubernetes",
            "github_url": "https://github.com/kubernetes/kubernetes",
            "docs_url": "https://kubernetes.io/zh-cn/docs/home/",
        },
    )

    snapshot = store.load_all()

    assert response.status_code == 201
    assert snapshot["crawl_profiles"]["kubernetes"]["allowed_path_prefixes"] == ["/docs", "/guide"]
    assert snapshot["crawl_profiles"]["kubernetes"]["category_hints"] == ["网络", "存储"]


def test_crawl_profile_endpoint_reads_and_updates_profile(tmp_path: Path):
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
    store.save_crawl_profile(
        "openclaw",
        {
            "entry_urls": ["https://openclaw.dev/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 3,
            "expand_mode": "auto",
            "category_hints": [],
            "discovery_prompt": "",
            "classification_prompt": "",
        },
    )

    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    get_response = client.get("/api/projects/openclaw/crawl-profile")
    put_response = client.put(
        "/api/projects/openclaw/crawl-profile",
        json={
            "entry_urls": ["https://openclaw.dev/docs"],
            "allowed_path_prefixes": ["/docs", "/guide"],
            "blocked_path_prefixes": ["/blog"],
            "max_depth": 4,
            "expand_mode": "auto",
            "category_hints": ["运行时"],
            "discovery_prompt": "discover",
            "classification_prompt": "classify",
        },
    )

    snapshot = store.load_all()

    assert get_response.status_code == 200
    assert get_response.get_json()["max_depth"] == 3
    assert put_response.status_code == 200
    assert snapshot["crawl_profiles"]["openclaw"]["allowed_path_prefixes"] == ["/docs", "/guide"]


def test_config_endpoint_reads_and_updates_assistant_settings(tmp_path: Path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    monkeypatch.setenv("PACKY_API_KEY", "gateway-key")
    monkeypatch.setenv("PACKY_API_URL", "http://127.0.0.1:8080/v1/messages")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENAI_API_URL", "https://code.swpumc.cn/v1/responses")

    store = JsonStore(tmp_path)
    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    get_response = client.get("/api/config")
    put_response = client.put(
        "/api/config",
        json={
            "sync_interval_minutes": 30,
            "llm": {
                "active_provider": "openai",
                "reasoning_effort": "xhigh",
                "disable_response_storage": True,
                "openai": {
                    "provider": "OpenAI",
                    "api_url": "https://code.swpumc.cn/v1/responses",
                    "model": "gpt-5.4",
                    "protocol": "openai-responses",
                },
            },
            "assistant": {
                "enabled": True,
                "default_project_ids": ["openclaw"],
                "default_categories": ["网络"],
                "default_timeframe": "30d",
                "max_evidence_items": 4,
                "max_source_items": 5,
                "retrieval": {
                    "release_weight": 1.0,
                    "docs_weight": 1.4,
                },
                "prompts": {
                    "classification": "classify prompt",
                    "answer": "answer prompt",
                },
            },
        },
    )

    snapshot = store.load_all()

    assert get_response.status_code == 200
    assert get_response.get_json()["llm"]["active_provider"] == "packy"
    assert get_response.get_json()["llm"]["packy"]["api_key_configured"] is True
    assert get_response.get_json()["llm"]["packy"]["api_url"] == "http://127.0.0.1:8080/v1/messages"
    assert get_response.get_json()["llm"]["openai"]["api_key_configured"] is True
    assert get_response.get_json()["assistant"]["enabled"] is True
    assert get_response.get_json()["assistant"]["default_timeframe"] == "14d"
    assert put_response.status_code == 200
    assert snapshot["config"]["sync_interval_minutes"] == 30
    assert snapshot["config"]["llm"]["active_provider"] == "openai"
    assert snapshot["config"]["llm"]["reasoning_effort"] == "xhigh"
    assert snapshot["config"]["llm"]["openai"]["model"] == "gpt-5.4"
    assert snapshot["config"]["assistant"]["default_project_ids"] == ["openclaw"]
    assert snapshot["config"]["assistant"]["retrieval"]["docs_weight"] == 1.4


def test_config_endpoint_auto_selects_openai_when_only_openai_env_is_configured(tmp_path: Path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    monkeypatch.delenv("PACKY_API_KEY", raising=False)
    monkeypatch.delenv("PACKY_API_URL", raising=False)
    monkeypatch.delenv("PACKY_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENAI_API_URL", "https://code.swpumc.cn/v1/responses")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4")
    monkeypatch.setenv("OPENAI_PROTOCOL", "openai-responses")

    store = JsonStore(tmp_path)
    app = create_app(store=store, sync_runner=lambda: {"status": "noop"})
    client = app.test_client()

    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.get_json()["llm"]["active_provider"] == "openai"
    assert response.get_json()["llm"]["openai"]["api_key_configured"] is True
