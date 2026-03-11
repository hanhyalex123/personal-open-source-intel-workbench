def test_build_daily_digest_history_groups_summaries_by_date():
    from backend.digest_history import build_daily_digest_history

    history = build_daily_digest_history(
        {
            "2026-03-10:cilium": {
                "date": "2026-03-10",
                "project_id": "cilium",
                "importance": "high",
                "updated_at": "2026-03-10T08:00:00Z",
            },
            "2026-03-10:vllm": {
                "date": "2026-03-10",
                "project_id": "vllm",
                "importance": "medium",
                "updated_at": "2026-03-10T08:05:00Z",
            },
            "2026-03-09:kubernetes": {
                "date": "2026-03-09",
                "project_id": "kubernetes",
                "importance": "high",
                "updated_at": "2026-03-09T08:00:00Z",
            },
        }
    )

    assert history[0]["date"] == "2026-03-10"
    assert history[0]["project_count"] == 2
    assert history[0]["high_importance_count"] == 1
    assert history[1]["date"] == "2026-03-09"


def test_build_recent_project_updates_only_returns_items_after_digest():
    from backend.digest_history import build_recent_project_updates

    snapshot = {
        "projects": [
            {"id": "cilium", "name": "Cilium", "repo": "cilium/cilium"},
            {"id": "vllm", "name": "vLLM", "repo": "vllm-project/vllm"},
        ],
        "events": {
            "github-release:cilium/cilium:v1.20.0-pre.0": {
                "id": "github-release:cilium/cilium:v1.20.0-pre.0",
                "project_id": "cilium",
                "repo": "cilium/cilium",
                "source": "github_release",
                "published_at": "2026-03-11T09:00:00Z",
                "url": "https://example.com/cilium",
                "version": "v1.20.0-pre.0",
            },
            "github-release:vllm-project/vllm:v0.17.0": {
                "id": "github-release:vllm-project/vllm:v0.17.0",
                "project_id": "vllm",
                "repo": "vllm-project/vllm",
                "source": "github_release",
                "published_at": "2026-03-10T07:00:00Z",
                "url": "https://example.com/vllm",
                "version": "v0.17.0",
            },
        },
        "analyses": {
            "github-release:cilium/cilium:v1.20.0-pre.0": {
                "title_zh": "Cilium 1.20 预发布",
                "summary_zh": "高风险更新。",
                "detail_sections": [{"title": "核心变化点", "bullets": ["重大变更"]}],
                "impact_points": ["cluster"],
                "action_items": ["验证升级。"],
                "urgency": "high",
                "tags": ["cilium"],
                "is_stable": True,
            },
            "github-release:vllm-project/vllm:v0.17.0": {
                "title_zh": "vLLM 0.17",
                "summary_zh": "昨日更新。",
                "detail_sections": [{"title": "核心变化点", "bullets": ["变更"]}],
                "impact_points": ["serving"],
                "action_items": ["看文档。"],
                "urgency": "medium",
                "tags": ["vllm"],
                "is_stable": True,
            },
        },
    }

    updates = build_recent_project_updates(snapshot=snapshot, since_iso="2026-03-11T08:00:00Z")

    assert [item["project_id"] for item in updates] == ["cilium"]
    assert updates[0]["items"][0]["title_zh"] == "Cilium 1.20 预发布"
