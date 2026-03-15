from urllib.parse import urlparse

TECH_CATEGORY_OPTIONS = ["升级", "运行时", "架构", "网络", "调度", "存储", "AI工具"]
FOCUS_TOPIC_OPTIONS = ["大模型推理部署", "大模型训练", "GPU", "虚拟化", "Agent"]

PROJECT_METADATA_DEFAULTS = {
    "openclaw": {"tech_categories": ["AI工具"], "focus_topics": ["Agent", "大模型推理部署"]},
    "kubernetes": {"tech_categories": ["架构", "调度", "网络", "升级"], "focus_topics": ["虚拟化"]},
    "nvidia-gpu-operator": {"tech_categories": ["架构", "运行时"], "focus_topics": ["GPU", "大模型训练"]},
    "cilium": {"tech_categories": ["网络"], "focus_topics": ["虚拟化"]},
    "iperf3": {"tech_categories": ["网络"], "focus_topics": []},
    "vllm": {"tech_categories": ["AI工具", "运行时"], "focus_topics": ["大模型推理部署", "GPU"]},
    "sglang": {"tech_categories": ["AI工具", "运行时"], "focus_topics": ["大模型推理部署", "GPU"]},
    "ktransformers": {"tech_categories": ["AI工具", "运行时"], "focus_topics": ["大模型推理部署", "GPU"]},
    "containerd": {"tech_categories": ["运行时"], "focus_topics": ["虚拟化"]},
    "cri-o": {"tech_categories": ["运行时"], "focus_topics": ["虚拟化"]},
    "podman": {"tech_categories": ["运行时"], "focus_topics": ["虚拟化"]},
    "cuda-toolkit": {"tech_categories": ["运行时"], "focus_topics": ["GPU", "大模型训练"]},
    "ascend-cann": {"tech_categories": ["运行时", "升级"], "focus_topics": ["GPU", "大模型训练"]},
    "mindspore": {"tech_categories": ["架构", "运行时"], "focus_topics": ["大模型训练", "GPU"]},
    "kind": {"tech_categories": ["架构", "调度"], "focus_topics": ["虚拟化"]},
    "vrag": {"tech_categories": ["AI工具"], "focus_topics": ["Agent", "大模型推理部署"]},
}


def build_project_record(*, name: str, github_url: str, docs_url: str, now_iso: str) -> dict:
    repo = extract_repo_from_github_url(github_url)
    base = {
        "id": _slugify(name or repo.split("/")[-1]),
        "name": name or repo,
        "github_url": github_url,
        "repo": repo,
        "docs_url": docs_url,
        "enabled": True,
        "release_area_enabled": True,
        "docs_area_enabled": True,
        "doc_system": "auto",
        "initial_read_enabled": True,
        "diff_mode": "page",
        "sync_interval_minutes": 60,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    return {**base, **infer_project_metadata(base)}


def build_default_crawl_profile(project: dict) -> dict:
    docs_url = project.get("docs_url", "")
    if docs_url == "https://kubernetes.io/zh-cn/docs/home/":
        return {
            "entry_urls": [
                "https://kubernetes.io/zh-cn/docs/concepts/storage/",
                "https://kubernetes.io/zh-cn/docs/concepts/services-networking/",
                "https://kubernetes.io/zh-cn/docs/concepts/workloads/",
                "https://kubernetes.io/zh-cn/docs/concepts/containers/",
                "https://kubernetes.io/zh-cn/docs/concepts/architecture/",
                "https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/",
            ],
            "allowed_path_prefixes": [
                "/zh-cn/docs/concepts/storage",
                "/zh-cn/docs/concepts/services-networking",
                "/zh-cn/docs/concepts/workloads",
                "/zh-cn/docs/concepts/containers",
                "/zh-cn/docs/concepts/architecture",
                "/zh-cn/docs/concepts/scheduling-eviction",
            ],
            "blocked_path_prefixes": [],
            "max_depth": 3,
            "max_pages": 40,
            "max_pages_per_section": 0,
            "expand_mode": "auto",
            "category_hints": ["存储", "网络", "工作负载", "容器", "架构", "调度"],
            "doc_system": "auto",
            "initial_read_enabled": True,
            "diff_mode": "page",
            "link_strategy": "auto",
            "canonicalize_fragments": True,
            "follow_pagination": True,
            "discovery_prompt": "",
            "classification_prompt": "",
        }
    if docs_url == "https://www.mindspore.cn/docs/":
        return {
            "entry_urls": [
                "https://www.mindspore.cn/docs/zh-CN/master/index.html",
                "https://www.mindspore.cn/tutorials/zh-CN/master/index.html",
            ],
            "allowed_path_prefixes": [
                "/docs/zh-CN/master",
                "/tutorials/zh-CN/master",
            ],
            "blocked_path_prefixes": [
                "/docs/zh-CN/master/_static",
                "/docs/zh-CN/master/_sources",
                "/docs/zh-CN/master/genindex",
                "/docs/zh-CN/master/search",
                "/tutorials/zh-CN/master/_static",
                "/tutorials/zh-CN/master/_sources",
                "/tutorials/zh-CN/master/genindex",
                "/tutorials/zh-CN/master/search",
            ],
            "max_depth": 1,
            "max_pages": 24,
            "max_pages_per_section": 8,
            "expand_mode": "auto",
            "category_hints": ["运行时", "架构", "网络", "存储", "调度"],
            "doc_system": "auto",
            "initial_read_enabled": True,
            "diff_mode": "page",
            "link_strategy": "furo_nav_first",
            "canonicalize_fragments": True,
            "follow_pagination": True,
            "discovery_prompt": "",
            "classification_prompt": "",
        }
    if docs_url == "https://www.hiascend.com/document":
        return {
            "entry_urls": [
                "https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/850/releasenote/releasenote_0005.html",
                "https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/900beta1/softwareinst/instg/instg_0102.html",
                "https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/80RC3alpha003/apiref/aolapi/context/aclnn",
            ],
            "allowed_path_prefixes": ["/document/detail/zh/CANNCommunityEdition"],
            "blocked_path_prefixes": [],
            "max_depth": 0,
            "max_pages": 12,
            "max_pages_per_section": 0,
            "expand_mode": "auto",
            "category_hints": ["升级", "运行时", "架构"],
            "doc_system": "auto",
            "initial_read_enabled": True,
            "diff_mode": "page",
            "link_strategy": "auto",
            "canonicalize_fragments": True,
            "follow_pagination": True,
            "discovery_prompt": "",
            "classification_prompt": "",
        }

    parsed = urlparse(docs_url)
    prefix = parsed.path or "/"
    return {
        "entry_urls": [docs_url] if docs_url else [],
        "allowed_path_prefixes": [prefix],
        "blocked_path_prefixes": [],
        "max_depth": 3,
        "max_pages": 40,
        "max_pages_per_section": 0,
        "expand_mode": "auto",
        "category_hints": [],
        "doc_system": "auto",
        "initial_read_enabled": True,
        "diff_mode": "page",
        "link_strategy": "auto",
        "canonicalize_fragments": True,
        "follow_pagination": True,
        "discovery_prompt": "",
        "classification_prompt": "",
    }


def collect_project_sources(projects: list[dict], crawl_profiles: dict) -> tuple[list[str], list[dict]]:
    repos = []
    feeds = []

    for project in projects:
        if not project.get("enabled", True):
            continue

        if project.get("release_area_enabled", True) and project.get("repo"):
            repos.append(project["repo"])

        if project.get("docs_area_enabled", True) and project.get("docs_url"):
            profile = crawl_profiles.get(project["id"]) or build_default_crawl_profile(project)
            feeds.append(
                {
                    "id": f'{project["id"]}:docs',
                    "project_id": project["id"],
                    "name": f'{project["name"]} 文档',
                    "url": project["docs_url"],
                    "type": "page",
                    "entry_urls": profile.get("entry_urls", [project["docs_url"]]),
                    "allowed_path_prefixes": profile.get("allowed_path_prefixes", []),
                    "blocked_path_prefixes": profile.get("blocked_path_prefixes", []),
                    "max_depth": profile.get("max_depth", 3),
                    "max_pages": profile.get("max_pages", 40),
                    "max_pages_per_section": profile.get("max_pages_per_section", 0),
                    "doc_system": profile.get("doc_system", project.get("doc_system", "auto")),
                    "initial_read_enabled": profile.get(
                        "initial_read_enabled",
                        project.get("initial_read_enabled", True),
                    ),
                    "diff_mode": profile.get("diff_mode", project.get("diff_mode", "page")),
                    "link_strategy": profile.get("link_strategy", "auto"),
                    "canonicalize_fragments": profile.get("canonicalize_fragments", True),
                    "follow_pagination": profile.get("follow_pagination", True),
                    "category_hints": profile.get("category_hints", []),
                    "discovery_prompt": profile.get("discovery_prompt", ""),
                    "classification_prompt": profile.get("classification_prompt", ""),
                }
            )

    return repos, feeds


def extract_repo_from_github_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise ValueError("github_url must point to github.com")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise ValueError("github_url must include owner and repo")
    return f"{parts[0]}/{parts[1]}"


def _slugify(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")


def infer_project_metadata(project: dict) -> dict:
    project_id = project.get("id", "")
    repo = project.get("repo", "")
    defaults = PROJECT_METADATA_DEFAULTS.get(project_id)
    if not defaults and repo:
        defaults = PROJECT_METADATA_DEFAULTS.get(_slugify(repo.split("/")[-1]))
    defaults = defaults or {"tech_categories": [], "focus_topics": []}
    return {
        "tech_categories": _normalize_labels(defaults.get("tech_categories", []), TECH_CATEGORY_OPTIONS),
        "focus_topics": _normalize_labels(defaults.get("focus_topics", []), FOCUS_TOPIC_OPTIONS),
    }


def normalize_project_record(project: dict) -> dict:
    normalized = dict(project)
    defaults = infer_project_metadata(normalized)
    normalized["doc_system"] = normalized.get("doc_system", "auto")
    normalized["initial_read_enabled"] = normalized.get("initial_read_enabled", True)
    normalized["diff_mode"] = normalized.get("diff_mode", "page")
    if "tech_categories" not in normalized:
        normalized["tech_categories"] = defaults["tech_categories"]
    else:
        normalized["tech_categories"] = _normalize_labels(normalized.get("tech_categories", []), TECH_CATEGORY_OPTIONS)
    if "focus_topics" not in normalized:
        normalized["focus_topics"] = defaults["focus_topics"]
    else:
        normalized["focus_topics"] = _normalize_labels(normalized.get("focus_topics", []), FOCUS_TOPIC_OPTIONS)
    return normalized


def _normalize_labels(values: list[str], allowed: list[str]) -> list[str]:
    if not isinstance(values, list):
        return []
    deduped = []
    seen = set()
    for value in values:
        if not isinstance(value, str):
            continue
        item = value.strip()
        if not item or item not in allowed or item in seen:
            continue
        deduped.append(item)
        seen.add(item)
    return deduped
