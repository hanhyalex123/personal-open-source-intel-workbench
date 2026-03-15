def test_classify_docs_page_uses_path_and_keywords():
    from backend.docs_classify import classify_doc_page

    category = classify_doc_page(
        {
            "url": "https://kubernetes.io/zh-cn/docs/concepts/services-networking/network-policies/",
            "title": "网络策略",
            "body": "CNI kube-proxy nftables service networking",
        }
    )

    assert category == "网络"


def test_classify_doc_page_uses_path_prefixes_for_top_level_sections():
    from backend.docs_classify import classify_doc_page

    assert (
        classify_doc_page(
            {
                "url": "https://kubernetes.io/zh-cn/docs/concepts/storage/",
                "title": "存储",
                "body": "overview page",
            }
        )
        == "存储"
    )
    assert (
        classify_doc_page(
            {
                "url": "https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/",
                "title": "调度、抢占和驱逐",
                "body": "overview page",
            }
        )
        == "调度"
    )
    assert (
        classify_doc_page(
            {
                "url": "https://kubernetes.io/zh-cn/docs/setup/production-environment/tools/kubeadm/",
                "title": "使用 kubeadm 引导集群",
                "body": "cluster upgrade and setup",
            }
        )
        == "升级"
    )
    assert (
        classify_doc_page(
            {
                "url": "https://kubernetes.io/zh-cn/docs/concepts/workloads/controllers/deployment/",
                "title": "Deployment",
                "body": "workload controllers deployment replica set",
            }
        )
        == "工作负载"
    )
    assert (
        classify_doc_page(
            {
                "url": "https://kubernetes.io/zh-cn/docs/concepts/containers/images/",
                "title": "镜像",
                "body": "container image pull policy",
            }
        )
        == "容器"
    )


def test_group_docs_records_by_category_and_pick_recent_pages():
    from backend.docs_classify import group_docs_records

    groups = group_docs_records(
        [
            {
                "project_id": "kubernetes",
                "url": "https://example.com/docs/network",
                "title": "Network",
                "body": "CNI kube-proxy nftables",
                "last_seen_at": "2026-03-09T10:00:00Z",
            },
            {
                "project_id": "kubernetes",
                "url": "https://example.com/docs/storage",
                "title": "Storage",
                "body": "CSI volume snapshot storage class",
                "last_seen_at": "2026-03-08T10:00:00Z",
            },
        ]
    )

    assert groups[0]["category"] == "网络"
    assert groups[0]["items"][0]["title"] == "Network"
    assert groups[1]["category"] == "存储"


def test_group_docs_records_filters_other_when_specific_categories_exist():
    from backend.docs_classify import group_docs_records

    groups = group_docs_records(
        [
            {
                "project_id": "kubernetes",
                "url": "https://example.com/docs/concepts",
                "title": "概念",
                "body": "generic landing page",
                "last_seen_at": "2026-03-08T10:00:00Z",
                "category": "其他",
            },
            {
                "project_id": "kubernetes",
                "url": "https://example.com/docs/network",
                "title": "Network",
                "body": "CNI kube-proxy nftables",
                "last_seen_at": "2026-03-09T10:00:00Z",
                "category": "网络",
            },
        ]
    )

    assert [group["category"] for group in groups] == ["网络"]


def test_classify_gpu_operator_release_notes_as_upgrade_not_network():
    from backend.docs_classify import classify_doc_page

    category = classify_doc_page(
        {
            "url": "https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/release-notes.html",
            "title": "Release Notes",
            "body": "Updated software component versions, upgrade prerequisites, confidential containers, GPUDirect RDMA",
        }
    )

    assert category == "升级"


def test_classify_gpu_operator_dra_page_as_scheduling():
    from backend.docs_classify import classify_doc_page

    category = classify_doc_page(
        {
            "url": "https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/dra-intro-install.html",
            "title": "NVIDIA DRA Driver for GPUs",
            "body": "Dynamic Resource Allocation lets Kubernetes request and schedule GPUs more flexibly.",
        }
    )

    assert category == "调度"


def test_classify_doc_page_prefers_navigation_metadata_for_furo_docs():
    from backend.docs_classify import classify_doc_page

    category = classify_doc_page(
        {
            "url": "https://linuxcontainers.org/incus/docs/main/reference/network_bridge/",
            "title": "Bridge network",
            "body": "generic body without many keywords",
            "nav_title": "Bridge network",
            "parent_section": "Networks",
            "section_key": "Networks",
            "headings": ["Bridge network"],
        }
    )

    assert category == "网络"


def test_classify_doc_page_maps_api_navigation_to_api_category():
    from backend.docs_classify import classify_doc_page

    category = classify_doc_page(
        {
            "url": "https://linuxcontainers.org/incus/docs/main/rest-api/",
            "title": "Main API documentation",
            "body": "rest endpoints and schema",
            "nav_title": "Main API documentation",
            "parent_section": "API",
            "section_key": "API",
        }
    )

    assert category == "API"
