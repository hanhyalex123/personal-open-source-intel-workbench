def test_build_discovery_prompt_requests_structured_profile():
    from backend.discovery import build_discovery_prompt

    prompt = build_discovery_prompt(
        project={
            "name": "Kubernetes",
            "docs_url": "https://kubernetes.io/zh-cn/docs/home/",
        },
        homepage_excerpt="Kubernetes 文档导航，包含概念、任务、教程、参考。",
    )

    assert "crawl profile" in prompt.lower()
    assert "allowed_path_prefixes" in prompt
    assert "category_hints" in prompt
    assert "Kubernetes" in prompt


def test_parse_discovery_response_reads_profile_json():
    from backend.discovery import parse_discovery_response

    profile = parse_discovery_response(
        """{
  "entry_urls": ["https://kubernetes.io/zh-cn/docs/home/"],
  "allowed_path_prefixes": ["/zh-cn/docs/concepts", "/zh-cn/docs/tasks"],
  "blocked_path_prefixes": ["/zh-cn/docs/home/_print"],
  "max_depth": 3,
  "max_pages": 60,
  "max_pages_per_section": 12,
  "expand_mode": "auto",
  "doc_system": "furo",
  "initial_read_enabled": true,
  "diff_mode": "page",
  "link_strategy": "furo_nav_first",
  "canonicalize_fragments": true,
  "follow_pagination": true,
  "category_hints": ["网络", "存储", "调度"],
  "discovery_prompt": "discover prompt",
  "classification_prompt": "classification prompt"
}"""
    )

    assert profile["max_pages"] == 60
    assert profile["allowed_path_prefixes"] == ["/zh-cn/docs/concepts", "/zh-cn/docs/tasks"]
    assert profile["category_hints"] == ["网络", "存储", "调度"]
    assert profile["doc_system"] == "furo"
    assert profile["max_pages_per_section"] == 12
    assert profile["link_strategy"] == "furo_nav_first"


def test_build_profile_from_homepage_falls_back_to_local_rules():
    from backend.discovery import build_profile_from_homepage

    profile = build_profile_from_homepage(
        docs_url="https://kubernetes.io/zh-cn/docs/home/",
        homepage_excerpt="概念 教程 任务 参考 调度、抢占和驱逐 存储 网络",
    )

    assert profile["entry_urls"] == ["https://kubernetes.io/zh-cn/docs/home/"]
    assert "/zh-cn/docs" in profile["allowed_path_prefixes"]
    assert "/zh-cn/docs/search" in profile["blocked_path_prefixes"]
    assert "网络" in profile["category_hints"]


def test_build_profile_from_homepage_expands_furo_entry_urls():
    from backend.discovery import build_profile_from_homepage

    profile = build_profile_from_homepage(
        docs_url="https://example.com/docs/main/",
        homepage_excerpt="""
          <html class="furo">
            <link rel="next" href="tutorial/first_steps/">
            <div class="sidebar-tree">
              <a class="reference internal" href="guide/">Guide</a>
              <a class="reference internal" href="reference/">Reference</a>
            </div>
          </html>
        """,
    )

    assert profile["doc_system"] == "furo"
    assert profile["link_strategy"] == "furo_nav_first"
    assert profile["entry_urls"][:3] == [
        "https://example.com/docs/main/",
        "https://example.com/docs/main/tutorial/first_steps/",
        "https://example.com/docs/main/guide/",
    ]
