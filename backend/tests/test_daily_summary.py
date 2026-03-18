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





def test_build_daily_project_summaries_ignores_empty_llm_daily_summary_fallback():
    from backend.daily_summary import build_daily_project_summaries

    snapshot = {
        "projects": [
            {
                "id": "crio",
                "name": "CRI-O",
                "github_url": "https://github.com/cri-o/cri-o",
                "repo": "cri-o/cri-o",
                "docs_url": "",
            }
        ],
        "events": {
            "github-release:cri-o/cri-o:v1.35.1": {
                "id": "github-release:cri-o/cri-o:v1.35.1",
                "project_id": "crio",
                "source": "github_release",
                "repo": "cri-o/cri-o",
                "title": "CRI-O v1.35.1",
                "version": "v1.35.1",
                "url": "https://example.com/crio",
                "published_at": "2026-03-03T00:35:59Z",
            }
        },
        "analyses": {
            "github-release:cri-o/cri-o:v1.35.1": {
                "title_zh": "CRI-O v1.35.1 版本发布",
                "summary_zh": "CRI-O v1.35.1 是 v1.35.0 后的首个补丁版本。",
                "detail_sections": [],
                "impact_points": [],
                "action_items": [],
                "urgency": "low",
                "tags": ["cri-o"],
                "is_stable": True,
            }
        },
        "daily_project_summaries": {},
    }

    def summarizer(**_kwargs):
        return {
            "headline": "CRI-O 今日重点：CRI-O v1.35.1 版本发布",
            "summary_zh": "模型返回空响应，无法生成日报摘要。",
            "reason": "",
            "importance": "low",
        }

    summaries = build_daily_project_summaries(
        snapshot=snapshot,
        summary_date="2026-03-17",
        now_iso="2026-03-17T08:00:00Z",
        summarizer=summarizer,
    )

    assert summaries[0]["summary_zh"] == "CRI-O 今天最值得看的变化是 CRI-O v1.35.1 版本发布，它已经进入首页项目级摘要。"
    assert summaries[0]["reason"] == "该变化在今天的项目证据里最值得优先查看。"


def test_resolve_summary_date_prefers_freshest_known_date():
    from backend.daily_summary import resolve_summary_date

    snapshot = {
        "events": {
            "github-release:cilium/cilium:v1.20.0-pre.0": {
                "published_at": "2026-03-10T08:00:00Z",
            }
        },
        "state": {
            "last_sync_at": "2026-03-10T09:30:00Z",
            "last_daily_summary_at": "2026-03-09T21:00:00Z",
        },
    }

    assert resolve_summary_date(snapshot) == "2026-03-10"


def test_resolve_summary_date_accepts_rfc_2822_dates():
    from backend.daily_summary import resolve_summary_date

    snapshot = {
        "events": {
            "docs-feed:podman:docs:https://example.com/podman": {
                "published_at": "Wed, 11 Mar 2026 10:08:25 GMT",
            }
        },
        "state": {},
    }

    assert resolve_summary_date(snapshot) == "2026-03-11"


def test_build_daily_project_summaries_replaces_english_analysis_with_chinese_text():
    from backend.daily_summary import build_daily_project_summaries

    snapshot = {
        "projects": [
            {
                "id": "podman",
                "name": "Podman",
                "github_url": "https://github.com/containers/podman",
                "repo": "containers/podman",
                "docs_url": "https://docs.podman.io",
            }
        ],
        "events": {
            "docs-feed:podman:docs:https://docs.podman.io/en/latest/markdown/podman-run.1.html": {
                "id": "docs-feed:podman:docs:https://docs.podman.io/en/latest/markdown/podman-run.1.html",
                "project_id": "podman",
                "source": "docs_feed",
                "title": "podman run",
                "url": "https://docs.podman.io/en/latest/markdown/podman-run.1.html",
                "published_at": "2026-03-17T01:00:00Z",
                "category": "运行",
            },
        },
        "analyses": {
            "docs-feed:podman:docs:https://docs.podman.io/en/latest/markdown/podman-run.1.html": {
                "title_zh": "podman run",
                "summary_zh": "Rootless networking flags updated.",
                "detail_sections": [],
                "impact_points": ["Rootless containers"],
                "action_items": ["Check existing scripts."],
                "urgency": "medium",
                "tags": ["podman"],
                "is_stable": True,
            }
        },
        "daily_project_summaries": {},
    }

    summaries = build_daily_project_summaries(snapshot=snapshot, summary_date="2026-03-17", now_iso="2026-03-17T08:00:00Z")

    assert summaries[0]["headline"] == "Podman 今日重点"
    assert summaries[0]["summary_zh"] == "今天检测到新的项目变化，建议查看最新中文解读。"
    assert summaries[0]["reason"] == "当前证据的中文摘要不足，已回退为中文提示。"
    assert summaries[0]["evidence_items"][0]["title_zh"] == "Podman 文档更新"
    assert summaries[0]["evidence_items"][0]["summary_zh"] == "该条证据的中文解读暂不可用，建议进入详情查看页面变化。"


def test_build_daily_digest_buckets_filters_by_recency():
    from backend.daily_summary import build_daily_digest_buckets

    snapshot = {
        "config": {
            "daily_digest": {
                "must_watch_project_ids": ["alpha", "beta"],
                "emerging_project_ids": ["gamma", "beta"],
                "must_watch_days": 30,
                "emerging_days": 3,
            }
        },
        "projects": [
            {"id": "alpha", "name": "Alpha"},
            {"id": "beta", "name": "Beta"},
            {"id": "gamma", "name": "Gamma"},
        ],
        "events": {
            "github-release:alpha/alpha:v1.0.0": {
                "id": "github-release:alpha/alpha:v1.0.0",
                "project_id": "alpha",
                "source": "github_release",
                "title": "Alpha v1.0.0",
                "published_at": "2026-03-10T09:00:00Z",
            },
            "github-release:beta/beta:v0.9.0": {
                "id": "github-release:beta/beta:v0.9.0",
                "project_id": "beta",
                "source": "github_release",
                "title": "Beta v0.9.0",
                "published_at": "2026-01-10T09:00:00Z",
            },
            "github-release:gamma/gamma:v0.1.0": {
                "id": "github-release:gamma/gamma:v0.1.0",
                "project_id": "gamma",
                "source": "github_release",
                "title": "Gamma v0.1.0",
                "published_at": "2026-03-16T09:00:00Z",
            },
        },
        "analyses": {
            "github-release:alpha/alpha:v1.0.0": {
                "title_zh": "Alpha v1.0.0 发布",
                "summary_zh": "Alpha 发布了首个正式版。",
                "urgency": "medium",
                "tags": ["alpha"],
            },
            "github-release:beta/beta:v0.9.0": {
                "title_zh": "Beta v0.9.0 发布",
                "summary_zh": "Beta 发布了预览版本。",
                "urgency": "low",
                "tags": ["beta"],
            },
            "github-release:gamma/gamma:v0.1.0": {
                "title_zh": "Gamma v0.1.0 发布",
                "summary_zh": "Gamma 首次发布。",
                "urgency": "high",
                "tags": ["gamma"],
            },
        },
        "daily_project_summaries": {},
    }

    buckets = build_daily_digest_buckets(
        snapshot=snapshot,
        summary_date="2026-03-17",
        now_iso="2026-03-17T08:00:00Z",
    )

    assert [item["project_id"] for item in buckets["must_watch_projects"]] == ["alpha"]
    assert [item["project_id"] for item in buckets["emerging_projects"]] == ["gamma"]


def test_build_daily_digest_buckets_auto_selects_recent_projects_when_emerging_config_is_empty():
    from backend.daily_summary import build_daily_digest_buckets

    snapshot = {
        "config": {
            "daily_digest": {
                "must_watch_project_ids": ["alpha"],
                "emerging_project_ids": [],
                "must_watch_days": 30,
                "emerging_days": 3,
            }
        },
        "projects": [
            {"id": "alpha", "name": "Alpha"},
            {"id": "beta", "name": "Beta"},
            {"id": "gamma", "name": "Gamma"},
        ],
        "events": {
            "github-release:alpha/alpha:v1.0.0": {
                "id": "github-release:alpha/alpha:v1.0.0",
                "project_id": "alpha",
                "source": "github_release",
                "title": "Alpha v1.0.0",
                "published_at": "2026-01-10T09:00:00Z",
            },
            "docs-feed:beta:docs:https://example.com/beta": {
                "id": "docs-feed:beta:docs:https://example.com/beta",
                "project_id": "beta",
                "source": "docs_feed",
                "title": "Beta docs",
                "published_at": "Sun, 15 Mar 2026 11:27:21 GMT",
            },
            "github-release:gamma/gamma:v0.1.0": {
                "id": "github-release:gamma/gamma:v0.1.0",
                "project_id": "gamma",
                "source": "github_release",
                "title": "Gamma v0.1.0",
                "published_at": "2026-03-16T09:00:00Z",
            },
        },
        "analyses": {
            "github-release:alpha/alpha:v1.0.0": {
                "title_zh": "Alpha v1.0.0 发布",
                "summary_zh": "Alpha 发布了首个正式版。",
                "urgency": "medium",
                "tags": ["alpha"],
            },
            "docs-feed:beta:docs:https://example.com/beta": {
                "title_zh": "Beta 文档更新",
                "summary_zh": "Beta 最近有新文档变化。",
                "urgency": "medium",
                "tags": ["beta"],
            },
            "github-release:gamma/gamma:v0.1.0": {
                "title_zh": "Gamma v0.1.0 发布",
                "summary_zh": "Gamma 首次发布。",
                "urgency": "high",
                "tags": ["gamma"],
            },
        },
        "daily_project_summaries": {},
    }

    buckets = build_daily_digest_buckets(
        snapshot=snapshot,
        summary_date="2026-03-17",
        now_iso="2026-03-17T08:00:00Z",
    )

    assert buckets["must_watch_projects"] == []
    assert {item["project_id"] for item in buckets["emerging_projects"]} == {"beta", "gamma"}


def _project_board_snapshot(*, config: dict, project_specs: list[dict], read_events: list[dict] | None = None) -> dict:
    projects = []
    events = {}
    analyses = {}

    for spec in project_specs:
        project_id = spec["id"]
        project_name = spec.get("name", project_id.replace("-", " ").title())
        repo = spec.get("repo", f"example/{project_id}")
        version = spec.get("version", "v1.0.0")
        base_event_id = f"github-release:{repo}:{version}"
        projects.append(
            {
                "id": project_id,
                "name": project_name,
                "github_url": f"https://example.com/{project_id}",
                "repo": repo,
                "docs_url": "",
            }
        )
        events[base_event_id] = {
            "id": base_event_id,
            "project_id": project_id,
            "source": spec.get("source", "github_release"),
            "repo": repo,
            "title": spec.get("title", f"{project_name} {version}"),
            "version": version,
            "url": f"https://example.com/{project_id}/{version}",
            "published_at": spec["published_at"],
        }
        analyses[base_event_id] = {
            "title_zh": spec.get("title_zh", f"{project_name} 更新"),
            "summary_zh": spec.get("summary_zh", f"{project_name} 有新的变化。"),
            "urgency": spec.get("urgency", "medium"),
            "action_items": spec.get("action_items", []),
            "impact_points": spec.get("impact_points", []),
            "detail_sections": spec.get("detail_sections", []),
            "tags": spec.get("tags", [project_id]),
            "is_stable": True,
        }
        for index, extra_published_at in enumerate(spec.get("extra_published_at", []), start=1):
            extra_event_id = f"docs-feed:{project_id}:docs:{index}"
            events[extra_event_id] = {
                "id": extra_event_id,
                "project_id": project_id,
                "source": "docs_feed",
                "title": f"{project_name} doc {index}",
                "url": f"https://example.com/{project_id}/docs/{index}",
                "published_at": extra_published_at,
                "category": "文档",
            }
            analyses[extra_event_id] = {
                "title_zh": f"{project_name} 文档更新 {index}",
                "summary_zh": f"{project_name} 文档有新增变化。",
                "urgency": spec.get("extra_urgency", spec.get("urgency", "medium")),
                "action_items": [],
                "impact_points": [],
                "detail_sections": [],
                "tags": spec.get("tags", [project_id]),
                "is_stable": True,
            }

    return {
        "config": config,
        "projects": projects,
        "events": events,
        "analyses": analyses,
        "daily_project_summaries": {},
        "read_events": read_events or [],
    }



def test_build_project_rank_board_keeps_stale_must_watch_project_for_monitoring():
    from backend.daily_summary import build_project_rank_board

    snapshot = _project_board_snapshot(
        config={
            "daily_digest": {
                "must_watch_project_ids": ["core-infra"],
                "emerging_project_ids": ["fresh-ai"],
                "must_watch_days": 30,
                "emerging_days": 3,
            }
        },
        project_specs=[
            {
                "id": "core-infra",
                "name": "Core Infra",
                "published_at": "2026-02-10T09:00:00Z",
                "urgency": "high",
                "title_zh": "Core Infra 核心升级",
            },
            {
                "id": "fresh-ai",
                "name": "Fresh AI",
                "published_at": "2026-03-18T09:00:00Z",
                "urgency": "low",
                "title_zh": "Fresh AI 文档更新",
            },
        ],
    )

    board = build_project_rank_board(
        snapshot=snapshot,
        summary_date="2026-03-19",
        now_iso="2026-03-19T12:00:00Z",
    )

    assert [item["project_id"] for item in board] == ["fresh-ai", "core-infra"]
    assert board[1]["last_activity_label"] == "37d"



def test_build_project_rank_board_prefers_fresher_candidate_over_more_important_one():
    from backend.daily_summary import build_project_rank_board

    snapshot = _project_board_snapshot(
        config={
            "daily_digest": {
                "must_watch_project_ids": ["important-core", "fresh-docs"],
                "emerging_project_ids": [],
                "must_watch_days": 30,
                "emerging_days": 3,
            }
        },
        project_specs=[
            {
                "id": "important-core",
                "name": "Important Core",
                "published_at": "2026-03-14T09:00:00Z",
                "urgency": "high",
                "title_zh": "Important Core 核心升级",
                "action_items": ["安排验证"],
                "impact_points": ["集群核心路径"],
                "detail_sections": [{"title": "核心变化", "bullets": ["需要关注"]}],
            },
            {
                "id": "fresh-docs",
                "name": "Fresh Docs",
                "published_at": "2026-03-19T06:00:00Z",
                "urgency": "low",
                "title_zh": "Fresh Docs 页面更新",
            },
        ],
    )

    board = build_project_rank_board(
        snapshot=snapshot,
        summary_date="2026-03-19",
        now_iso="2026-03-19T12:00:00Z",
    )

    assert [item["project_id"] for item in board[:2]] == ["fresh-docs", "important-core"]
    assert board[0]["board_score"] > board[1]["board_score"]



def test_build_project_rank_board_outputs_30d_series_breakdown_and_explanation():
    from backend.daily_summary import build_project_rank_board

    snapshot = _project_board_snapshot(
        config={
            "daily_digest": {
                "must_watch_project_ids": ["alpha"],
                "emerging_project_ids": [],
                "must_watch_days": 30,
                "emerging_days": 3,
            }
        },
        project_specs=[
            {
                "id": "alpha",
                "name": "Alpha",
                "published_at": "2026-03-19T08:00:00Z",
                "urgency": "medium",
                "title_zh": "Alpha release",
                "extra_published_at": ["2026-03-18T08:00:00Z", "2026-03-02T08:00:00Z"],
            },
        ],
    )

    board = build_project_rank_board(
        snapshot=snapshot,
        summary_date="2026-03-19",
        now_iso="2026-03-19T12:00:00Z",
    )

    assert len(board[0]["activity_series_30d"]) == 30
    assert board[0]["activity_breakdown_30d"] == {"total": 3, "release": 1, "docs": 2}
    assert "30天内" in board[0]["board_explanation"]


def test_digest_and_monitor_rankings_can_diverge_for_same_projects():
    from backend.daily_summary import build_daily_project_summaries, build_project_rank_board

    snapshot = _project_board_snapshot(
        config={
            "daily_digest": {
                "must_watch_project_ids": ["steady-core"],
                "emerging_project_ids": [],
                "must_watch_days": 30,
                "emerging_days": 3,
            }
        },
        project_specs=[
            {
                "id": "steady-core",
                "name": "Steady Core",
                "published_at": "2026-03-17T09:00:00Z",
                "urgency": "high",
                "title_zh": "Steady Core 连续修复",
                "action_items": ["安排验证"],
                "impact_points": ["核心链路"],
                "detail_sections": [{"title": "核心变化", "bullets": ["持续修复"]}],
                "extra_published_at": [
                    "2026-03-16T09:00:00Z",
                    "2026-03-15T09:00:00Z",
                    "2026-03-14T09:00:00Z",
                    "2026-03-13T09:00:00Z",
                ],
            },
            {
                "id": "fresh-flash",
                "name": "Fresh Flash",
                "published_at": "2026-03-19T08:00:00Z",
                "urgency": "medium",
                "title_zh": "Fresh Flash 今日更新",
            },
        ],
    )

    summaries = build_daily_project_summaries(
        snapshot=snapshot,
        summary_date="2026-03-19",
        now_iso="2026-03-19T12:00:00Z",
    )
    board = build_project_rank_board(
        snapshot=snapshot,
        summary_date="2026-03-19",
        now_iso="2026-03-19T12:00:00Z",
    )

    assert [item["project_id"] for item in summaries[:2]] == ["fresh-flash", "steady-core"]
    assert [item["project_id"] for item in board[:2]] == ["steady-core", "fresh-flash"]
    assert "新鲜度" in summaries[0]["ranking_explanation"]
    assert "30天变化量" in board[0]["board_explanation"]


def test_build_project_rank_board_applies_recent_read_decay():
    from backend.daily_summary import build_project_rank_board

    snapshot = _project_board_snapshot(
        config={
            "daily_digest": {
                "must_watch_project_ids": ["read-heavy", "unread"],
                "emerging_project_ids": [],
                "must_watch_days": 30,
                "emerging_days": 3,
            }
        },
        project_specs=[
            {
                "id": "read-heavy",
                "name": "Read Heavy",
                "published_at": "2026-03-18T10:00:00Z",
                "urgency": "medium",
                "title_zh": "Read Heavy 每日更新",
            },
            {
                "id": "unread",
                "name": "Unread",
                "published_at": "2026-03-18T10:00:00Z",
                "urgency": "medium",
                "title_zh": "Unread 每日更新",
            },
        ],
        read_events=[
            {"project_id": "read-heavy", "event_id": "x1", "read_at": "2026-03-18T12:00:00Z"},
            {"project_id": "read-heavy", "event_id": "x2", "read_at": "2026-03-19T08:00:00Z"},
        ],
    )

    board = build_project_rank_board(
        snapshot=snapshot,
        summary_date="2026-03-19",
        now_iso="2026-03-19T12:00:00Z",
    )

    assert [item["project_id"] for item in board[:2]] == ["unread", "read-heavy"]
    assert board[1]["read_count"] == 2
    assert board[1]["read_decay_applied"] is True



def test_daily_ranking_base_score_uses_importance_recency_evidence_source():
    from backend.daily_ranking import compute_base_score

    now_iso = "2026-03-10T12:00:00Z"
    weights = {"importance": 0.45, "recency": 0.25, "evidence": 0.2, "source": 0.1}

    base_item = {
        "published_at": "2026-03-01T12:00:00Z",
        "action_items": [],
        "impact_points": [],
        "detail_sections": [],
        "source": "docs_feed",
        "category": "",
        "tags": [],
    }

    base_summary = {"importance": "medium", "evidence_items": [base_item]}
    base_score = compute_base_score(
        base_summary,
        weights=weights,
        now_iso=now_iso,
        recency_half_life_days=3,
    )

    assert (
        compute_base_score(
            {"importance": "high", "evidence_items": [base_item]},
            weights=weights,
            now_iso=now_iso,
            recency_half_life_days=3,
        )
        > base_score
    )

    assert (
        compute_base_score(
            {
                "importance": "medium",
                "evidence_items": [{**base_item, "published_at": "2026-03-10T12:00:00Z"}],
            },
            weights=weights,
            now_iso=now_iso,
            recency_half_life_days=3,
        )
        > base_score
    )

    assert (
        compute_base_score(
            {
                "importance": "medium",
                "evidence_items": [
                    {
                        **base_item,
                        "action_items": ["a", "b", "c"],
                        "impact_points": ["i1", "i2"],
                        "detail_sections": [{"title": "t", "bullets": ["x"]}],
                    }
                ],
            },
            weights=weights,
            now_iso=now_iso,
            recency_half_life_days=3,
        )
        > base_score
    )

    assert (
        compute_base_score(
            {"importance": "medium", "evidence_items": [{**base_item, "source": "github_release"}]},
            weights=weights,
            now_iso=now_iso,
            recency_half_life_days=3,
        )
        > base_score
    )


def test_daily_ranking_applies_read_decay_within_window():
    from backend.daily_ranking import apply_read_decay

    now_iso = "2026-03-10T12:00:00Z"
    read_events = [{"project_id": "kubernetes", "read_at": "2026-03-09T12:00:00Z"}]

    assert (
        apply_read_decay(
            1.0,
            project_id="kubernetes",
            read_events=read_events,
            now_iso=now_iso,
            read_decay_days=2,
            read_decay_factor=0.5,
        )
        == 0.5
    )

    assert (
        apply_read_decay(
            1.0,
            project_id="kubernetes",
            read_events=[{"project_id": "kubernetes", "read_at": "2026-03-07T11:59:59Z"}],
            now_iso=now_iso,
            read_decay_days=2,
            read_decay_factor=0.5,
        )
        == 1.0
    )


def test_daily_ranking_mmr_rerank_promotes_diversity():
    from backend.daily_ranking import rerank_with_mmr

    items = [
        {
            "project_id": "alpha",
            "ranking_score": 0.9,
            "evidence_items": [
                {"source": "github_release", "category": "network", "tags": ["kubernetes"]}
            ],
        },
        {
            "project_id": "beta",
            "ranking_score": 0.85,
            "evidence_items": [
                {"source": "github_release", "category": "network", "tags": ["kubernetes"]}
            ],
        },
        {
            "project_id": "gamma",
            "ranking_score": 0.7,
            "evidence_items": [
                {"source": "docs_feed", "category": "storage", "tags": ["openclaw"]}
            ],
        },
    ]

    reranked = rerank_with_mmr(items, lambda_param=0.7, diversity_keys=["source", "category", "tags"])

    assert [item["project_id"] for item in reranked] == ["alpha", "gamma", "beta"]
