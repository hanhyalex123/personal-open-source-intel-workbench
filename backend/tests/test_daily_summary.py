def test_build_daily_project_summaries_generates_ranked_project_cards():
    from backend.daily_summary import build_daily_project_summaries

    snapshot = {
        "projects": [
            {
                "id": "kubernetes",
                "name": "Kubernetes",
                "github_url": "https://github.com/kubernetes/kubernetes",
                "repo": "kubernetes/kubernetes",
                "docs_url": "https://example.com/docs",
            },
            {
                "id": "openclaw",
                "name": "OpenClaw",
                "github_url": "https://github.com/openclaw/openclaw",
                "repo": "openclaw/openclaw",
                "docs_url": "",
            },
        ],
        "events": {
            "github-release:kubernetes/kubernetes:v1.31.3": {
                "id": "github-release:kubernetes/kubernetes:v1.31.3",
                "project_id": "kubernetes",
                "source": "github_release",
                "repo": "kubernetes/kubernetes",
                "title": "Kubernetes v1.31.3",
                "version": "v1.31.3",
                "url": "https://example.com/k8s-release",
                "published_at": "2026-03-10T09:00:00Z",
            },
            "docs-feed:kubernetes:docs:https://example.com/docs/network": {
                "id": "docs-feed:kubernetes:docs:https://example.com/docs/network",
                "project_id": "kubernetes",
                "source": "docs_feed",
                "source_key": "kubernetes:docs",
                "title": "Network Policies",
                "url": "https://example.com/docs/network",
                "published_at": "2026-03-10T08:00:00Z",
                "category": "网络",
            },
            "github-release:openclaw/openclaw:v2.4.0": {
                "id": "github-release:openclaw/openclaw:v2.4.0",
                "project_id": "openclaw",
                "source": "github_release",
                "repo": "openclaw/openclaw",
                "title": "OpenClaw v2.4.0",
                "version": "v2.4.0",
                "url": "https://example.com/openclaw-release",
                "published_at": "2026-03-08T09:00:00Z",
            },
        },
        "analyses": {
            "github-release:kubernetes/kubernetes:v1.31.3": {
                "title_zh": "Kubernetes 1.31.3 最新补丁",
                "summary_zh": "补丁收敛了网络兼容性风险。",
                "detail_sections": [{"title": "核心变化点", "bullets": ["nftables 路径更加稳定"]}],
                "impact_points": ["网络插件兼容性"],
                "action_items": ["验证现有 CNI 插件。"],
                "urgency": "high",
                "tags": ["kubernetes", "network"],
                "is_stable": True,
            },
            "docs-feed:kubernetes:docs:https://example.com/docs/network": {
                "title_zh": "网络策略文档更新",
                "summary_zh": "文档更新解释了网络策略默认行为。",
                "detail_sections": [{"title": "核心变化点", "bullets": ["策略默认值说明"]}],
                "impact_points": ["集群网络策略"],
                "action_items": ["比对当前策略配置。"],
                "urgency": "medium",
                "tags": ["kubernetes", "docs"],
                "is_stable": True,
            },
            "github-release:openclaw/openclaw:v2.4.0": {
                "title_zh": "OpenClaw 2.4.0 发布",
                "summary_zh": "最近版本引入了新的备份流程。",
                "detail_sections": [{"title": "核心变化点", "bullets": ["备份流程变更"]}],
                "impact_points": ["备份任务"],
                "action_items": ["检查备份脚本兼容性。"],
                "urgency": "low",
                "tags": ["openclaw"],
                "is_stable": True,
            },
        },
        "daily_project_summaries": {},
    }

    summaries = build_daily_project_summaries(snapshot=snapshot, summary_date="2026-03-10", now_iso="2026-03-10T12:00:00Z")

    assert [item["project_id"] for item in summaries] == ["kubernetes", "openclaw"]
    assert summaries[0]["importance"] == "high"
    assert summaries[0]["headline"] == "Kubernetes 今日重点：Kubernetes 1.31.3 最新补丁"
    assert len(summaries[0]["evidence_items"]) == 2
    assert summaries[1]["summary_zh"] == "今日没有显著新增高影响变化，建议先关注最近仍值得跟进的项目结论。"
    assert summaries[1]["evidence_items"][0]["title_zh"] == "OpenClaw 2.4.0 发布"
