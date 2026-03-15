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
    assert project["doc_system"] == "auto"
    assert project["initial_read_enabled"] is True
    assert project["diff_mode"] == "page"


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
    assert profile["link_strategy"] == "auto"
    assert profile["canonicalize_fragments"] is True


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


def test_build_default_crawl_profile_special_cases_mindspore_docs():
    from backend.projects import build_default_crawl_profile

    profile = build_default_crawl_profile(
        {
            "id": "mindspore",
            "docs_url": "https://www.mindspore.cn/docs/",
        }
    )

    assert profile["entry_urls"] == [
        "https://www.mindspore.cn/docs/zh-CN/master/index.html",
        "https://www.mindspore.cn/tutorials/zh-CN/master/index.html",
    ]
    assert profile["allowed_path_prefixes"] == [
        "/docs/zh-CN/master",
        "/tutorials/zh-CN/master",
    ]
    assert "/docs/zh-CN/master/_static" in profile["blocked_path_prefixes"]
    assert "/docs/zh-CN/master/genindex" in profile["blocked_path_prefixes"]


def test_build_default_crawl_profile_special_cases_ascend_cann_docs():
    from backend.projects import build_default_crawl_profile

    profile = build_default_crawl_profile(
        {
            "id": "ascend-cann",
            "docs_url": "https://www.hiascend.com/document",
        }
    )

    assert profile["entry_urls"] == [
        "https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/850/releasenote/releasenote_0005.html",
        "https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/900beta1/softwareinst/instg/instg_0102.html",
        "https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/80RC3alpha003/apiref/aolapi/context/aclnn",
    ]
    assert profile["allowed_path_prefixes"] == ["/document/detail/zh/CANNCommunityEdition"]
    assert profile["max_depth"] == 0


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
            "max_pages_per_section": 0,
            "doc_system": "auto",
            "initial_read_enabled": True,
            "diff_mode": "page",
            "link_strategy": "auto",
            "canonicalize_fragments": True,
            "follow_pagination": True,
            "category_hints": [],
            "discovery_prompt": "",
            "classification_prompt": "",
        }
    ]


def test_collect_project_sources_docs_only_project_returns_docs_feed_only():
    from backend.projects import collect_project_sources

    repos, feeds = collect_project_sources(
        [
            {
                "id": "cuda-toolkit",
                "name": "CUDA 工具链",
                "repo": "",
                "docs_url": "https://docs.nvidia.com/cuda/",
                "enabled": True,
                "release_area_enabled": False,
                "docs_area_enabled": True,
            }
        ],
        {
            "cuda-toolkit": {
                "entry_urls": ["https://docs.nvidia.com/cuda/"],
                "allowed_path_prefixes": ["/cuda"],
                "blocked_path_prefixes": [],
                "max_depth": 3,
            }
        },
    )

    assert repos == []
    assert feeds == [
        {
            "id": "cuda-toolkit:docs",
            "project_id": "cuda-toolkit",
            "name": "CUDA 工具链 文档",
            "url": "https://docs.nvidia.com/cuda/",
            "type": "page",
            "entry_urls": ["https://docs.nvidia.com/cuda/"],
            "allowed_path_prefixes": ["/cuda"],
            "blocked_path_prefixes": [],
            "max_depth": 3,
            "max_pages": 40,
            "max_pages_per_section": 0,
            "doc_system": "auto",
            "initial_read_enabled": True,
            "diff_mode": "page",
            "link_strategy": "auto",
            "canonicalize_fragments": True,
            "follow_pagination": True,
            "category_hints": [],
            "discovery_prompt": "",
            "classification_prompt": "",
        }
    ]
