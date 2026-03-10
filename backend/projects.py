from urllib.parse import urlparse


def build_project_record(*, name: str, github_url: str, docs_url: str, now_iso: str) -> dict:
    repo = extract_repo_from_github_url(github_url)
    return {
        "id": _slugify(name or repo.split("/")[-1]),
        "name": name or repo,
        "github_url": github_url,
        "repo": repo,
        "docs_url": docs_url,
        "enabled": True,
        "release_area_enabled": True,
        "docs_area_enabled": True,
        "sync_interval_minutes": 60,
        "created_at": now_iso,
        "updated_at": now_iso,
    }


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
            "expand_mode": "auto",
            "category_hints": ["存储", "网络", "工作负载", "容器", "架构", "调度"],
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
        "expand_mode": "auto",
        "category_hints": [],
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
