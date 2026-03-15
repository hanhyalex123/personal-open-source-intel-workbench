NETWORK_KEYWORDS = [
    "network",
    "networking",
    "cni",
    "kube-proxy",
    "nftables",
    "gateway",
    "bridge",
    "ovn",
    "acl",
    "bgp",
    "dns",
    "load balancer",
    "forward",
]
STORAGE_KEYWORDS = ["storage", "csi", "volume", "snapshot", "pool", "bucket", "zfs", "btrfs", "ceph", "linstor"]
SCHEDULING_KEYWORDS = ["scheduler", "scheduling", "affinity", "taint", "toleration", "resourceclaim", "dra"]
ARCHITECTURE_KEYWORDS = ["architecture", "control plane", "api server", "etcd", "cluster", "daemon", "internals"]
SECURITY_KEYWORDS = ["security", "authentication", "authorization", "rbac", "tls", "certificates", "bpf token"]
UPGRADE_KEYWORDS = ["upgrade", "migration", "migrating", "release notes", "changelog", "benchmarking", "initialize"]
RUNTIME_KEYWORDS = ["runtime", "containerd", "cri", "cgroup", "device plugin", "driver", "container", "vm", "instance"]
OBSERVABILITY_KEYWORDS = ["monitoring", "metrics", "logging", "trace", "observability"]
API_KEYWORDS = ["api", "rest api", "specification", "events api", "metrics api", "man pages", "command aliases"]

PATH_RULES = [
    ("/datacenter/cloud-native/gpu-operator/latest/release-notes", "升级"),
    ("/datacenter/cloud-native/gpu-operator/latest/upgrade", "升级"),
    ("/datacenter/cloud-native/gpu-operator/latest/cdi", "运行时"),
    ("/datacenter/cloud-native/gpu-operator/latest/custom-driver-params", "运行时"),
    ("/datacenter/cloud-native/gpu-operator/latest/dra", "调度"),
    ("/datacenter/cloud-native/gpu-operator/latest/confidential-containers", "安全"),
    ("/datacenter/cloud-native/gpu-operator/latest/gpu-operator-rdma", "网络"),
    ("/docs/concepts/services-networking", "网络"),
    ("/docs/concepts/storage", "存储"),
    ("/docs/concepts/scheduling-eviction", "调度"),
    ("/docs/concepts/workloads", "工作负载"),
    ("/docs/concepts/containers", "容器"),
    ("/docs/setup/production-environment/tools/kubeadm", "升级"),
    ("/docs/setup", "升级"),
    ("/docs/concepts/security", "安全"),
    ("/docs/reference", "架构"),
    ("/docs/concepts", "架构"),
    ("/networks", "网络"),
    ("/storage", "存储"),
    ("/security", "安全"),
    ("/api", "API"),
    ("/rest-api", "API"),
    ("/reference", "API"),
    ("/internals", "架构"),
    ("/clustering", "架构"),
    ("/instances", "运行时"),
    ("/server", "架构"),
    ("/client", "运行时"),
    ("/images", "运行时"),
]

NAV_RULES = [
    ("networks", "网络"),
    ("network", "网络"),
    ("ovn", "网络"),
    ("bridge", "网络"),
    ("acl", "网络"),
    ("load balancer", "网络"),
    ("storage", "存储"),
    ("volume", "存储"),
    ("pool", "存储"),
    ("bucket", "存储"),
    ("security", "安全"),
    ("authentication", "安全"),
    ("authorization", "安全"),
    ("api", "API"),
    ("rest api", "API"),
    ("specification", "API"),
    ("events api", "API"),
    ("metrics api", "API"),
    ("internals", "架构"),
    ("architecture", "架构"),
    ("cluster", "架构"),
    ("instances", "运行时"),
    ("instance", "运行时"),
    ("client", "运行时"),
    ("server", "架构"),
    ("images", "运行时"),
    ("migration", "升级"),
    ("migrating", "升级"),
    ("benchmark", "升级"),
]


def classify_doc_page(record: dict) -> str:
    if record.get("category"):
        return record["category"]

    url = record.get("url", "").lower()
    path_category = ""
    for prefix, category in PATH_RULES:
        if prefix in url:
            path_category = category
            break

    nav_text = _build_nav_text(record)
    nav_category = _classify_text(nav_text, nav_only=True)
    if nav_category and (not path_category or path_category in {"API", "架构"}):
        return nav_category
    if path_category:
        return path_category
    if nav_category:
        return nav_category

    text = f'{nav_text} {record.get("url", "")} {record.get("title", "")} {record.get("body", "")}'.lower()
    return _classify_text(text) or "其他"


def group_docs_records(records: list[dict]) -> list[dict]:
    grouped = {}
    for record in records:
        category = classify_doc_page(record)
        grouped.setdefault(category, []).append({**record, "category": category})

    if len(grouped) > 1 and "其他" in grouped:
        grouped.pop("其他")

    result = []
    for category, items in grouped.items():
        items = sorted(
            items,
            key=lambda item: (
                item.get("nav_depth", 99),
                0 if item.get("is_index_page") else 1,
                item.get("nav_order", 999999),
                -( _timestamp_value(item.get("last_seen_at")) ),
            ),
        )
        result.append({"category": category, "items": items})

    return sorted(result, key=lambda group: group["items"][0].get("nav_order", 999999))


def _build_nav_text(record: dict) -> str:
    parts = [
        record.get("nav_title", ""),
        record.get("parent_section", ""),
        record.get("section_key", ""),
        record.get("section", ""),
        " ".join(record.get("breadcrumbs", []) or []),
        " ".join(record.get("headings", []) or []),
    ]
    return " ".join(part for part in parts if part).lower()


def _classify_text(text: str, *, nav_only: bool = False) -> str:
    if nav_only:
        for keyword, category in NAV_RULES:
            if keyword in text:
                return category

    if _contains_any(text, NETWORK_KEYWORDS):
        return "网络"
    if _contains_any(text, STORAGE_KEYWORDS):
        return "存储"
    if _contains_any(text, SCHEDULING_KEYWORDS):
        return "调度"
    if _contains_any(text, SECURITY_KEYWORDS):
        return "安全"
    if _contains_any(text, API_KEYWORDS):
        return "API"
    if _contains_any(text, UPGRADE_KEYWORDS):
        return "升级"
    if _contains_any(text, RUNTIME_KEYWORDS):
        return "运行时"
    if _contains_any(text, OBSERVABILITY_KEYWORDS):
        return "可观测性"
    if _contains_any(text, ARCHITECTURE_KEYWORDS):
        return "架构"
    return ""


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _timestamp_value(value: str | None) -> int:
    if not value:
        return 0
    digits = "".join(char for char in value if char.isdigit())
    return int(digits[:14] or 0)
