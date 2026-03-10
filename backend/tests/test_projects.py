def test_build_project_record_extracts_repo_and_defaults():
    from backend.projects import build_project_record

    project = build_project_record(
        name="OpenClaw",
        github_url="https://github.com/openclaw/openclaw",
        docs_url="https://openclaw.dev/docs",
        now_iso="2026-03-09T12:30:00Z",
    )

    assert project["id"] == "openclaw"
    assert project["repo"] == "openclaw/openclaw"
    assert project["enabled"] is True
    assert project["release_area_enabled"] is True
    assert project["docs_area_enabled"] is True


def test_build_default_crawl_profile_uses_docs_url():
    from backend.projects import build_default_crawl_profile

    profile = build_default_crawl_profile(
        {
            "id": "openclaw",
            "docs_url": "https://openclaw.dev/docs",
        }
    )

    assert profile["entry_urls"] == ["https://openclaw.dev/docs"]
    assert profile["allowed_path_prefixes"] == ["/docs"]
    assert profile["max_depth"] == 3
    assert profile["max_pages"] == 40


def test_build_default_crawl_profile_special_cases_kubernetes_docs_home():
    from backend.projects import build_default_crawl_profile

    profile = build_default_crawl_profile(
        {
            "id": "kubernetes",
            "docs_url": "https://kubernetes.io/zh-cn/docs/home/",
        }
    )

    assert profile["entry_urls"] == [
        "https://kubernetes.io/zh-cn/docs/concepts/storage/",
        "https://kubernetes.io/zh-cn/docs/concepts/services-networking/",
        "https://kubernetes.io/zh-cn/docs/concepts/workloads/",
        "https://kubernetes.io/zh-cn/docs/concepts/containers/",
        "https://kubernetes.io/zh-cn/docs/concepts/architecture/",
        "https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/",
    ]
    assert profile["allowed_path_prefixes"] == [
        "/zh-cn/docs/concepts/storage",
        "/zh-cn/docs/concepts/services-networking",
        "/zh-cn/docs/concepts/workloads",
        "/zh-cn/docs/concepts/containers",
        "/zh-cn/docs/concepts/architecture",
        "/zh-cn/docs/concepts/scheduling-eviction",
    ]


def test_collect_project_sources_returns_enabled_release_and_docs_inputs():
    from backend.projects import collect_project_sources

    repos, feeds = collect_project_sources(
        [
            {
                "id": "openclaw",
                "name": "OpenClaw",
                "repo": "openclaw/openclaw",
                "docs_url": "https://openclaw.dev/docs",
                "enabled": True,
                "release_area_enabled": True,
                "docs_area_enabled": True,
            }
        ],
        {
            "openclaw": {
                "entry_urls": ["https://openclaw.dev/docs"],
                "allowed_path_prefixes": ["/docs"],
                "blocked_path_prefixes": [],
                "max_depth": 3,
            }
        },
    )

    assert repos == ["openclaw/openclaw"]
    assert feeds == [
        {
            "id": "openclaw:docs",
            "project_id": "openclaw",
            "name": "OpenClaw 文档",
            "url": "https://openclaw.dev/docs",
            "type": "page",
            "entry_urls": ["https://openclaw.dev/docs"],
            "allowed_path_prefixes": ["/docs"],
            "blocked_path_prefixes": [],
            "max_depth": 3,
            "max_pages": 40,
            "category_hints": [],
            "discovery_prompt": "",
            "classification_prompt": "",
        }
    ]
