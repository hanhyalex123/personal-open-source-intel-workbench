NETWORK_KEYWORDS = ["network", "networking", "cni", "kube-proxy", "nftables", "service", "gateway"]
STORAGE_KEYWORDS = ["storage", "csi", "volume", "snapshot", "pv", "pvc"]
SCHEDULING_KEYWORDS = ["scheduler", "scheduling", "taint", "toleration", "affinity", "dynamic resource allocation", "resourceclaim", "resource class", "dra"]
ARCHITECTURE_KEYWORDS = ["architecture", "control plane", "api server", "etcd"]
SECURITY_KEYWORDS = ["security", "pod security", "authentication", "authorization", "rbac", "confidential containers", "kata"]
UPGRADE_KEYWORDS = ["upgrade", "migration", "kubeadm", "release notes", "changelog", "prerequisites"]
RUNTIME_KEYWORDS = ["runtime", "containerd", "cri", "cgroup", "container toolkit", "device plugin", "driver", "cdi"]
OBSERVABILITY_KEYWORDS = ["monitoring", "metrics", "logging", "trace"]

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
]


def classify_doc_page(record: dict) -> str:
    if record.get("category"):
        return record["category"]
    url = record.get("url", "").lower()
    for prefix, category in PATH_RULES:
        if prefix in url:
            return category

    text = f'{record.get("url", "")} {record.get("title", "")} {record.get("body", "")}'.lower()
    if _contains_any(text, NETWORK_KEYWORDS):
        return "网络"
    if _contains_any(text, STORAGE_KEYWORDS):
        return "存储"
    if _contains_any(text, SCHEDULING_KEYWORDS):
        return "调度"
    if _contains_any(text, ARCHITECTURE_KEYWORDS):
        return "架构"
    if _contains_any(text, SECURITY_KEYWORDS):
        return "安全"
    if _contains_any(text, UPGRADE_KEYWORDS):
        return "升级"
    if _contains_any(text, RUNTIME_KEYWORDS):
        return "运行时"
    if _contains_any(text, OBSERVABILITY_KEYWORDS):
        return "可观测性"
    return "其他"


def group_docs_records(records: list[dict]) -> list[dict]:
    grouped = {}
    for record in records:
        category = classify_doc_page(record)
        grouped.setdefault(category, []).append({**record, "category": category})

    if len(grouped) > 1 and "其他" in grouped:
        grouped.pop("其他")

    result = []
    for category, items in grouped.items():
        items = sorted(items, key=lambda item: item.get("last_seen_at") or "", reverse=True)
        result.append({"category": category, "items": items})

    return sorted(result, key=lambda group: group["items"][0].get("last_seen_at") or "", reverse=True)


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)
