import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";

function formatZhDateTime(value) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

const dashboardPayload = {
  overview: {
    total_items: 1,
    stable_items: 1,
    last_sync_at: "2026-03-09T12:00:00Z",
    last_analysis_at: "2026-03-09T12:00:00Z",
    last_fetch_success_at: "2026-03-10T04:00:00Z",
    last_incremental_analysis_at: "2026-03-10T04:05:00Z",
    last_daily_digest_at: "2026-03-10T01:00:00Z",
    last_heartbeat_at: "2026-03-10T04:05:00Z",
    scheduler: {
      running: true,
      interval_minutes: 60,
      timezone: "Asia/Shanghai",
    },
  },
  homepage_projects: [
    {
      project_id: "kubernetes",
      project_name: "Kubernetes",
      headline: "Kubernetes 今日重点：1.31 补丁与网络策略",
      summary_zh: "今天最值得看的是 1.31 补丁和网络策略文档，两者都直接影响集群网络行为。",
      reason: "同一天同时出现补丁和网络文档更新，并且都有明确行动项。",
      importance: "high",
      updated_at: "2026-03-10T12:00:00Z",
      evidence_items: [
        {
          id: "github-release:kubernetes/kubernetes:v1.31.3",
          title_zh: "Kubernetes 1.31.3 最新补丁",
          summary_zh: "这是最新补丁。",
          urgency: "high",
          source: "github_release",
          url: "https://example.com/v1.31.3",
        },
        {
          id: "docs-feed:kubernetes:docs:https://example.com/docs/network",
          title_zh: "网络策略文档更新",
          summary_zh: "文档强调了网络策略和 CNI 相关行为。",
          urgency: "medium",
          source: "docs_feed",
          url: "https://example.com/docs/network",
          category: "网络",
        },
      ],
    },
  ],
  recent_project_updates: [
    {
      project_id: "cilium",
      project_name: "Cilium",
      latest_published_at: "2026-03-10T13:00:00Z",
      highest_urgency: "high",
      items: [
        {
          id: "github-release:cilium/cilium:v1.20.0-pre.0",
          title_zh: "Cilium 1.20 预发布",
          summary_zh: "新增 KCNP 和 BackendTLSPolicy。",
          urgency: "high",
          source: "github_release",
          url: "https://example.com/cilium",
          version: "v1.20.0-pre.0",
        },
      ],
    },
  ],
  daily_digest_history: [
    {
      date: "2026-03-10",
      project_count: 8,
      high_importance_count: 5,
      updated_at: "2026-03-10T01:00:00Z",
    },
    {
      date: "2026-03-09",
      project_count: 6,
      high_importance_count: 3,
      updated_at: "2026-03-09T01:00:00Z",
    },
  ],
  sources: [
    {
      id: "kubernetes/kubernetes",
      title: "kubernetes/kubernetes",
      total_items: 1,
      stable_items: 1,
      highest_urgency: "medium",
      kind: "repo",
    },
  ],
  groups: [
    {
      id: "kubernetes/kubernetes",
      title: "kubernetes/kubernetes",
      items: [
        {
          id: "github-release:kubernetes/kubernetes:v1.31.0",
          title_zh: "Kubernetes 1.31 网络推荐变化",
          summary_zh: "Kubernetes 1.31 推荐使用 nftables 路径。",
          detail_sections: [
            {
              title: "核心变化点",
              bullets: ["推荐使用 nftables 路径", "需要评估 kube-proxy 模式和节点兼容性"],
            },
          ],
          impact_points: ["Kubernetes 网络插件和节点网络配置"],
          action_items: ["检查当前插件兼容性并评估调整计划。"],
          urgency: "medium",
          tags: ["kubernetes", "networking", "nftables"],
          is_stable: true,
          title: "Kubernetes v1.31.0",
          url: "https://example.com/v1.31.0",
          version: "v1.31.0",
        },
      ],
    },
  ],
  projects: [
    {
      id: "kubernetes",
      name: "Kubernetes",
      github_url: "https://github.com/kubernetes/kubernetes",
      docs_url: "https://kubernetes.io/zh-cn/docs/home/",
      tech_categories: ["架构", "调度", "网络", "升级"],
      focus_topics: ["虚拟化"],
      release_area: {
        enabled: true,
        items: [
          {
            id: "github-release:kubernetes/kubernetes:v1.31.3",
            title_zh: "Kubernetes 1.31.3 最新补丁",
            summary_zh: "这是最新补丁。",
            detail_sections: [{ title: "核心变化点", bullets: ["最新变化"] }],
            impact_points: ["Kubernetes 集群"],
            action_items: ["优先验证。"],
            urgency: "high",
            tags: ["kubernetes", "gpu", "大模型训练"],
            is_stable: true,
            title: "Kubernetes v1.31.3",
            url: "https://example.com/v1.31.3",
            version: "v1.31.3",
            published_at: "2026-03-12T10:00:00Z",
          },
          {
            id: "github-release:kubernetes/kubernetes:v1.31.2",
            title_zh: "Kubernetes 1.31.2 次新补丁",
            summary_zh: "这是次新补丁，涉及 containerd 与 CRI-O 兼容性修正。",
            detail_sections: [{ title: "核心变化点", bullets: ["次新变化"] }],
            impact_points: ["Kubernetes 集群"],
            action_items: ["继续验证。"],
            urgency: "medium",
            tags: ["kubernetes"],
            is_stable: true,
            title: "Kubernetes v1.31.2",
            url: "https://example.com/v1.31.2",
            version: "v1.31.2",
            published_at: "2026-03-11T10:00:00Z",
          },
          {
            id: "github-release:kubernetes/kubernetes:v1.31.1",
            title_zh: "Kubernetes 1.31.1 补丁说明",
            summary_zh: "这是第三新的补丁。",
            detail_sections: [{ title: "核心变化点", bullets: ["第三新变化"] }],
            impact_points: ["Kubernetes 集群"],
            action_items: ["安排升级。"],
            urgency: "low",
            tags: ["kubernetes"],
            is_stable: true,
            title: "Kubernetes v1.31.1",
            url: "https://example.com/v1.31.1",
            version: "v1.31.1",
            published_at: "2026-03-10T10:00:00Z",
          },
          {
            id: "github-release:kubernetes/kubernetes:v1.31.0",
            title_zh: "Kubernetes 1.31 网络推荐变化",
            summary_zh: "Kubernetes 1.31 推荐使用 nftables 路径。",
            detail_sections: [
              {
                title: "核心变化点",
                bullets: ["推荐使用 nftables 路径", "需要评估 kube-proxy 模式和节点兼容性"],
              },
            ],
            impact_points: ["Kubernetes 网络插件和节点网络配置"],
            action_items: ["检查当前插件兼容性并评估调整计划。"],
            urgency: "medium",
            tags: ["kubernetes", "networking", "nftables"],
            is_stable: true,
            title: "Kubernetes v1.31.0",
            url: "https://example.com/v1.31.0",
            version: "v1.31.0",
            published_at: "2026-03-09T10:00:00Z",
          },
        ],
      },
      docs_area: {
        enabled: true,
        categories: [
          {
            category: "网络",
            items: [
              {
                id: "docs-feed:kubernetes:docs:https://example.com/docs/network",
                title_zh: "网络策略文档更新",
                summary_zh: "文档强调了网络策略和 CNI 相关行为。",
                detail_sections: [{ title: "核心变化点", bullets: ["网络策略行为说明"] }],
                impact_points: ["Kubernetes 网络层"],
                action_items: ["检查网络策略配置。"],
                urgency: "low",
                tags: ["kubernetes", "network"],
                is_stable: true,
                title: "Network Policies",
                url: "https://example.com/docs/network",
              },
            ],
          },
        ],
      },
    },
  ],
};

const projectsPayload = [
  {
    id: "openclaw",
    name: "OpenClaw",
    github_url: "https://github.com/openclaw/openclaw",
    docs_url: "https://openclaw.dev/docs",
    tech_categories: ["AI工具"],
    focus_topics: ["Agent", "大模型推理部署"],
  },
];

const configPayload = {
  sync_interval_minutes: 60,
  llm: {
    active_provider: "packy",
    reasoning_effort: "xhigh",
    disable_response_storage: true,
    packy: {
      provider: "primary-gateway",
      api_url: "https://gateway.example.com/v1/messages",
      model: "claude-opus-4-6",
      protocol: "",
      api_key_configured: true,
    },
    openai: {
      provider: "OpenAI",
      api_url: "https://code.swpumc.cn/v1/responses",
      model: "gpt-5.4",
      protocol: "openai-responses",
      api_key_configured: true,
    },
  },
  assistant: {
    enabled: true,
    default_mode: "live",
    default_project_ids: ["openclaw"],
    default_categories: ["网络"],
    default_timeframe: "14d",
    max_evidence_items: 3,
    max_source_items: 4,
    retrieval: {
      release_weight: 1,
      docs_weight: 1.2,
    },
    live_search: {
      enabled: true,
      provider: "duckduckgo",
      max_results: 5,
      max_pages: 3,
    },
    prompts: {
      classification: "classify prompt",
      answer: "answer prompt",
    },
  },
};

const assistantPayload = {
  report_markdown:
    "## 结论摘要\n\nOpenClaw 近 30 天保持高频更新，重点集中在安全修复、会话稳定性和多模态能力演进。\n\n## 主要方向\n\n- 修复 Telegram SSRF 与 WebSocket 相关风险\n- 补强会话与状态一致性\n- 强化多模态记忆索引与模型接入\n",
  report_outline: ["结论摘要", "主要方向", "关键证据", "建议下一步"],
  evidence: [
    {
      id: "docs-feed:openclaw:docs:https://example.com/network",
      title: "OpenClaw 网络文档更新",
      summary: "新增网络策略与路由说明。",
      source: "docs_feed",
      project_id: "openclaw",
      project_name: "OpenClaw",
      category: "网络",
      urgency: "medium",
      url: "https://example.com/network",
      published_at: "2026-03-10T08:00:00Z",
      relation_to_query: "primary_project",
    },
  ],
  next_steps: ["检查网络策略默认值。", "验证现有备份脚本。"],
  sources: [
    {
      title: "OpenClaw 网络文档更新",
      url: "https://example.com/network",
      source: "docs_feed",
      project_name: "OpenClaw",
    },
    {
      title: "OpenClaw blog post",
      url: "https://example.com/blog/openclaw",
      source: "web_search",
      project_name: "web",
    },
  ],
  search_trace: [
    {
      query: "openclaw recent release notes",
      url: "https://example.com/blog/openclaw",
      fetch_mode: "http",
      matched_entity: "openclaw",
    },
  ],
  applied_plan: {
    intent: "project_update_summary",
    primary_entities: ["openclaw"],
    related_entities: [],
    timeframe: "30d",
    search_queries: ["openclaw recent release notes"],
  },
  applied_filters: {
    mode: "live",
    project_ids: ["openclaw"],
    categories: ["网络"],
    timeframe: "30d",
  },
};

const syncStatusPayload = {
  status: "running",
  run_kind: "manual",
  phase: "incremental",
  message: "正在抓取 GitHub releases",
  started_at: "2026-03-10T04:10:00Z",
  finished_at: null,
  last_heartbeat_at: "2026-03-10T04:10:10Z",
  current_label: "cilium/cilium",
  processed_sources: 1,
  total_sources: 8,
  new_events: 2,
  analyzed_events: 1,
  failed_events: 0,
  skipped_events: 4,
  last_incremental_metrics: {
    new_events: 9,
    analyzed_events: 7,
    failed_events: 1,
    skipped_events: 4,
    total_sources: 26,
    processed_sources: 26,
    finished_at: "2026-03-15T02:31:00Z",
  },
  heartbeat_age_seconds: 10,
  is_stalled: false,
  error: "",
  result: {},
};

const syncRunsPayload = [
  {
    id: "run_2026-03-10T04:10:00Z_manual",
    run_kind: "manual",
    status: "running",
    phase: "incremental",
    message: "正在抓取 GitHub releases",
    started_at: "2026-03-10T04:10:00Z",
    finished_at: null,
    last_heartbeat_at: "2026-03-10T04:10:10Z",
    metrics: { total_sources: 8, processed_sources: 1, new_events: 2, analyzed_events: 1, failed_events: 0, skipped_events: 4 },
  },
];

const syncRunDetailPayload = {
  ...syncRunsPayload[0],
  sources: [
    {
      kind: "repo",
      label: "cilium/cilium",
      status: "success",
      metrics: { new_events: 1, analyzed_events: 1, failed_events: 0 },
      events: [
        {
          event_id: "github-release:cilium/cilium:v1.20.0-pre.0",
          status: "analyzed",
          title: "Cilium 1.20 预发布",
          version: "v1.20.0-pre.0",
          published_at: "2026-03-10T13:00:00Z",
          analysis: {
            summary_zh: "新增 KCNP 和 BackendTLSPolicy。",
          },
        },
      ],
    },
  ],
};

const docsProjectsPayload = [
  {
    project_id: "kubernetes",
    project_name: "Kubernetes",
    docs_url: "https://kubernetes.io/zh-cn/docs/home/",
    page_count: 12,
    last_synced_at: "2026-03-12T10:00:00Z",
    latest_initial_read: {
      id: "docs-feed:kubernetes:initial",
      event_kind: "docs_initial_read",
      title_zh: "Kubernetes 首次文档解读",
      summary_zh: "覆盖网络与升级章节。",
      published_at: "2026-03-11T09:00:00Z",
      changed_page_count: 3,
    },
    latest_diff_update: {
      id: "docs-feed:kubernetes:diff",
      event_kind: "docs_diff_update",
      title_zh: "Kubernetes 网络文档更新",
      summary_zh: "更新了网络策略说明。",
      published_at: "2026-03-12T10:00:00Z",
      changed_page_count: 1,
    },
  },
];

const docsProjectDetailPayload = {
  project_id: "kubernetes",
  project_name: "Kubernetes",
  docs_url: "https://kubernetes.io/zh-cn/docs/home/",
  page_count: 12,
  last_synced_at: "2026-03-12T10:00:00Z",
  initial_read: {
    id: "docs-feed:kubernetes:initial",
    event_kind: "docs_initial_read",
    title_zh: "Kubernetes 首次文档解读",
    summary_zh: "覆盖网络与升级章节。",
    published_at: "2026-03-11T09:00:00Z",
    analysis_mode: "initial_read",
    changed_pages: [{ page_id: "network-page", title_after: "Network", change_type: "added" }],
  },
  latest_update: {
    id: "docs-feed:kubernetes:diff",
    event_kind: "docs_diff_update",
    title_zh: "Kubernetes 网络文档更新",
    summary_zh: "更新了网络策略说明。",
    published_at: "2026-03-12T10:00:00Z",
    analysis_mode: "diff_update",
    changed_pages: [{ page_id: "network-page", title_after: "Network", change_type: "changed" }],
  },
  recent_events: [],
  page_stats: {
    total_pages: 12,
    changed_pages: 1,
    last_synced_at: "2026-03-12T10:00:00Z",
  },
};

const docsEventsPayload = [
  {
    id: "docs-feed:kubernetes:diff",
    event_kind: "docs_diff_update",
    title_zh: "Kubernetes 网络文档更新",
    summary_zh: "更新了网络策略说明。",
    published_at: "2026-03-12T10:00:00Z",
    urgency: "high",
    doc_summary: "本次主要补充网络策略默认行为。",
    doc_key_points: ["建议先看 network policy 章节"],
    diff_highlights: ["新增默认行为说明"],
    reading_guide: ["先读 Network 页面 diff"],
    changed_pages: [{ page_id: "network-page", title_after: "Network", change_type: "changed" }],
  },
  {
    id: "docs-feed:kubernetes:initial",
    event_kind: "docs_initial_read",
    title_zh: "Kubernetes 首次文档解读",
    summary_zh: "覆盖网络与升级章节。",
    published_at: "2026-03-11T09:00:00Z",
    urgency: "medium",
    doc_summary: "先关注网络与升级章节。",
    doc_key_points: ["阅读文档入口"],
    diff_highlights: [],
    reading_guide: ["先读网络章节"],
    changed_pages: [{ page_id: "network-page", title_after: "Network", change_type: "added" }],
  },
];

const docsPagesPayload = [
  {
    id: "network-page",
    title: "Network",
    summary: "网络策略与 CNI 行为。",
    category: "网络",
    extractor_hint: "furo",
    latest_change: { change_type: "changed" },
    is_recently_changed: true,
  },
];

const docsPageDiffPayload = {
  page: docsPagesPayload[0],
  latest_diff: {
    change_type: "changed",
    added_blocks: ["新增默认行为说明。"],
    removed_blocks: ["删除旧版提示。"],
  },
  history: [],
};

function createFetchMock({
  docsProjects = docsProjectsPayload,
  docsProjectDetail = docsProjectDetailPayload,
  docsEvents = docsEventsPayload,
  docsPages = docsPagesPayload,
  docsPageDiff = docsPageDiffPayload,
  docsPageDiffById = null,
} = {}) {
  return vi.fn((url, options) => {
    const requestUrl = String(url);

    if (requestUrl.includes("/api/dashboard")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(dashboardPayload),
      });
    }

    const pageDiffMatch = requestUrl.match(/\/api\/docs\/projects\/kubernetes\/pages\/([^/]+)\/diff$/);
    if (pageDiffMatch) {
      const payload = docsPageDiffById?.[pageDiffMatch[1]] || docsPageDiff;
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(payload),
      });
    }

    if (requestUrl.includes("/api/docs/projects/kubernetes/pages")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(docsPages),
      });
    }

    if (requestUrl.includes("/api/docs/projects/kubernetes/events")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(docsEvents),
      });
    }

    if (requestUrl.includes("/api/docs/projects/kubernetes")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(docsProjectDetail),
      });
    }

    if (requestUrl.includes("/api/docs/projects")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(docsProjects),
      });
    }

    if (requestUrl.includes("/api/projects") && !options?.method) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(projectsPayload),
      });
    }

    if (requestUrl.includes("/api/config") && !options?.method) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(configPayload),
      });
    }

    if (requestUrl.includes("/api/projects") && options?.method === "POST") {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            id: "codex",
            name: "Codex",
            github_url: "https://github.com/openai/codex",
            docs_url: "https://platform.openai.com/docs",
          }),
      });
    }

    if (requestUrl.includes("/api/sync") && options?.method === "POST") {
      return Promise.resolve({
        ok: true,
        status: 202,
        json: () => Promise.resolve(syncStatusPayload),
      });
    }

    if (requestUrl.includes("/api/sync/status")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(syncStatusPayload),
      });
    }

    if (requestUrl.includes("/api/sync/runs/") && !requestUrl.endsWith("/api/sync/runs")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(syncRunDetailPayload),
      });
    }

    if (requestUrl.includes("/api/sync/runs")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(syncRunsPayload),
      });
    }

    if (requestUrl.includes("/api/assistant/query") && options?.method === "POST") {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(assistantPayload),
      });
    }

    if (requestUrl.includes("/api/config") && options?.method === "PUT") {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(configPayload),
      });
    }

    return Promise.reject(new Error(`unexpected request: ${url}`));
  });
}

describe("App", () => {
  beforeEach(() => {
    global.fetch = createFetchMock();
  });

  it("renders Chinese insight cards and stable labels from backend data", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Kubernetes 今日重点：1.31 补丁与网络策略")).toBeInTheDocument();
    });

    expect(screen.getByText("架构师")).toBeInTheDocument();
    expect(screen.getByText("开源情报站")).toBeInTheDocument();
    expect(screen.getAllByText("开源动态、中文结论、同步日志").length).toBeGreaterThan(0);
    expect(screen.getByText("情报值班台")).toBeInTheDocument();
    expect(screen.getAllByText("日报").length).toBeGreaterThan(0);
    expect(screen.getAllByText("情报监控").length).toBeGreaterThan(0);
    expect(screen.getAllByText("AI 控制台").length).toBeGreaterThan(0);
    expect(screen.getAllByText("文档解读").length).toBeGreaterThan(0);
    expect(screen.getAllByText("配置中心").length).toBeGreaterThan(0);
    expect(screen.queryByText("版本变化直接讲人话")).not.toBeInTheDocument();
    expect(screen.getByText("情报值班台")).toBeInTheDocument();
    expect(screen.getAllByAltText("品牌头像").length).toBeGreaterThan(0);
    expect(screen.getByText("重点结论")).toBeInTheDocument();
    expect(screen.getByText("运行快照")).toBeInTheDocument();
    expect(screen.getByText("固定日报放首页，增量变化看提醒，项目下钻放到情报监控页。")).toBeInTheDocument();
    expect(document.querySelector(".homepage-topline")).not.toBeNull();
    expect(screen.getByText("先看今天最值得跟进的项目和运行信号。")).toBeInTheDocument();
    expect(screen.getByText("增量快讯")).toBeInTheDocument();
    expect(screen.getByText("日报归档")).toBeInTheDocument();
    expect(screen.getAllByText("关键依据").length).toBeGreaterThan(0);
    expect(screen.getAllByText("最近抓取成功").length).toBeGreaterThan(0);
    expect(screen.getAllByText("最近日报生成").length).toBeGreaterThan(0);
    expect(screen.getByText("调度状态")).toBeInTheDocument();
    expect(screen.getByText("2026-03-10")).toBeInTheDocument();
    expect(screen.queryByText("Sync")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "同步监控" }));
    expect(screen.getByRole("heading", { name: "同步监控", level: 1 })).toBeInTheDocument();
    expect(screen.getByText("同步雷达")).toBeInTheDocument();
    expect(screen.getAllByText("Signal Radar").length).toBeGreaterThan(0);
    expect(screen.getByText("正在抓取 GitHub releases")).toBeInTheDocument();
    expect(screen.getByText("cilium/cilium")).toBeInTheDocument();
    expect(screen.getByText("1 / 8")).toBeInTheDocument();
      expect(screen.getByText("心跳状态")).toBeInTheDocument();
      expect(screen.getByText("运行中")).toBeInTheDocument();
      expect(screen.getByText("失败数")).toBeInTheDocument();
      expect(screen.getByText("跳过")).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: "查看日志" })[0]);
    await waitFor(() => {
      expect(screen.getByRole("dialog", { name: "同步日志" })).toBeInTheDocument();
    });
    const logDialog = screen.getByRole("dialog", { name: "同步日志" });
    expect(screen.getByText("Cilium 1.20 预发布")).toBeInTheDocument();
    expect(screen.getByText("新增 KCNP 和 BackendTLSPolicy。")).toBeInTheDocument();
    expect(within(logDialog).getByRole("button", { name: "跳过" })).toBeInTheDocument();
    expect(screen.queryByText(/\*\*核心变化点/)).not.toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "情报监控" })[0]);
    expect(screen.getByText("按项目跟踪版本、文档与分析结论")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "架构" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "虚拟化" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "GPU" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "网络" })).toBeInTheDocument();
    expect(screen.getAllByText("ReleaseNote 区").length).toBeGreaterThan(0);
    expect(screen.getByText("文档区")).toBeInTheDocument();
    expect(screen.getAllByText("网络").length).toBeGreaterThan(0);
    expect(screen.getByText("网络策略文档更新")).toBeInTheDocument();
    expect(document.querySelector('section.project-panel[data-project-id="kubernetes"]')).not.toBeNull();
    expect(screen.getByText("快速定位")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Kubernetes" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ReleaseNote 区" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "网络" })).toBeInTheDocument();
    expect(screen.getAllByText("虚拟化").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "展开更多" }));
    expect(screen.getByText(formatZhDateTime("2026-03-12T10:00:00Z"))).toBeInTheDocument();
    expect(screen.getByText("Kubernetes 1.31 网络推荐变化")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "查看详情" })[0]);
    expect(screen.getByText("优先验证。")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "架构" }));
    expect(document.querySelector('section.project-panel[data-project-id="kubernetes"]')).not.toBeNull();
    fireEvent.click(screen.getAllByRole("button", { name: "打开文档视图" })[0]);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "文档解读", level: 1 })).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText("当前页面快照")).toBeInTheDocument();
    });
    expect(screen.getAllByText("Kubernetes 网络文档更新").length).toBeGreaterThan(0);
    fireEvent.click(screen.getAllByRole("button", { name: "情报监控" })[0]);
    fireEvent.click(screen.getByRole("button", { name: "AI工具" }));
    expect(screen.getByText("当前筛选下没有匹配内容。")).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: "配置中心" })[0]);
    expect(screen.getAllByText("配置中心").length).toBeGreaterThan(0);
    expect(screen.getAllByText("OpenClaw").length).toBeGreaterThan(0);
    expect(screen.getAllByText("AI工具").length).toBeGreaterThan(0);
    expect(screen.getAllByText("大模型推理部署").length).toBeGreaterThan(0);
    expect(screen.getByText("新增项目时只填 GitHub URL 和官方文档 URL，后端会接管后续分析链路。")).toBeInTheDocument();
    expect(screen.getByText("AI 能力管理")).toBeInTheDocument();
    expect(screen.getByText("Assistant 全局配置")).toBeInTheDocument();
    expect(screen.getByDisplayValue("14d")).toBeInTheDocument();
    expect(screen.queryByLabelText("默认模式")).not.toBeInTheDocument();
  });

  it("shows sync monitor page in navigation", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("日报首页")).toBeInTheDocument();
    });

    const monitorTab = screen.getAllByRole("button", { name: "同步监控" })[0];
    fireEvent.click(monitorTab);

    expect(screen.getByRole("heading", { name: "同步监控", level: 1 })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText("日报首页")).not.toBeInTheDocument();
    });
    expect(screen.getByText("同步雷达")).toBeInTheDocument();
  });

  it("shows sync actions only on sync monitor page", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("日报首页")).toBeInTheDocument();
    });

    expect(screen.queryByRole("button", { name: "立即同步" })).not.toBeInTheDocument();
    expect(screen.queryByText("同步雷达")).not.toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: "同步监控" })[0]);

    expect(screen.getByRole("button", { name: "立即同步" })).toBeInTheDocument();
    expect(screen.getByText("同步雷达")).toBeInTheDocument();
  });

  it("shows dedicated docs view in navigation", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Kubernetes 今日重点：1.31 补丁与网络策略")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "文档解读" })[0]);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "文档解读", level: 1 })).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText("当前页面快照")).toBeInTheDocument();
    });
    expect(screen.getByText("文档事件流")).toBeInTheDocument();
    expect(screen.getByText("最近更新 diff")).toBeInTheDocument();
  });

  it("keeps initial-read pages stable and uses linked page ids for selection", async () => {
    const initialOnlyPages = [
      {
        id: "storage-page",
        title: "Storage",
        summary: "存储章节概览。",
        category: "存储",
        extractor_hint: "furo",
        latest_change: null,
        is_recently_changed: false,
      },
      {
        id: "network-page",
        title: "Network",
        summary: "网络策略与 CNI 行为。",
        category: "网络",
        extractor_hint: "furo",
        latest_change: null,
        is_recently_changed: false,
      },
    ];
    const initialOnlyDetail = {
      ...docsProjectDetailPayload,
      latest_update: null,
      page_stats: {
        total_pages: 2,
        changed_pages: 0,
        last_synced_at: "2026-03-12T10:00:00Z",
      },
      initial_read: {
        ...docsProjectDetailPayload.initial_read,
        changed_pages: [{ page_id: "network-page", title_after: "Network", change_type: "added" }],
      },
    };
    const initialOnlyEvents = [
      {
        id: "docs-feed:kubernetes:initial",
        event_kind: "docs_initial_read",
        title_zh: "Kubernetes 首次文档解读",
        summary_zh: "覆盖网络与存储章节。",
        published_at: "2026-03-11T09:00:00Z",
        urgency: "medium",
        doc_summary: "先关注网络与存储章节。",
        doc_key_points: ["阅读文档入口"],
        diff_highlights: [],
        reading_guide: ["先读网络章节"],
        changed_pages: [{ page_id: "network-page", title_after: "Network", change_type: "added" }],
      },
    ];

    global.fetch = createFetchMock({
      docsProjectDetail: initialOnlyDetail,
      docsEvents: initialOnlyEvents,
      docsPages: initialOnlyPages,
      docsPageDiffById: {
        "network-page": {
          page: initialOnlyPages[1],
          latest_diff: null,
          history: [],
        },
        "storage-page": {
          page: initialOnlyPages[0],
          latest_diff: null,
          history: [],
        },
      },
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Kubernetes 今日重点：1.31 补丁与网络策略")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "文档解读" })[0]);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "文档解读", level: 1 })).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Network", level: 3 })).toBeInTheDocument();
    });

    const pagesPanel = screen.getByText("当前页面快照").closest("section");
    expect(within(pagesPanel).getAllByText("稳定")).toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: /Storage/ }));
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Storage", level: 3 })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Network.*新增/ }));
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Network", level: 3 })).toBeInTheDocument();
    });
  });

  it("renders structured docs highlights and reading guides from live analyses", async () => {
    global.fetch = createFetchMock({
      docsEvents: [
        {
          ...docsEventsPayload[0],
          diff_highlights: [
            { highlight: "首读只覆盖首页，需要继续补抓 Security 页面。", page_id: "network-page", title: "Incus" },
          ],
          reading_guide: [
            { step: 1, focus: "先读 Incus 首页", reason: "建立产品定位" },
            { step: 2, focus: "再读 Security", reason: "确认安全边界" },
          ],
        },
      ],
      docsProjectDetail: {
        ...docsProjectDetailPayload,
        recent_events: [],
      },
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Kubernetes 今日重点：1.31 补丁与网络策略")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "文档解读" })[0]);

    await waitFor(() => {
      expect(screen.getByText("首读只覆盖首页，需要继续补抓 Security 页面。")).toBeInTheDocument();
    });
    expect(screen.getByText("先读 Incus 首页：建立产品定位")).toBeInTheDocument();
    expect(screen.getByText("再读 Security：确认安全边界")).toBeInTheDocument();
  });

  it("creates a project from github and docs urls", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Kubernetes 今日重点：1.31 补丁与网络策略").length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getAllByRole("button", { name: "配置中心" })[0]);

    await waitFor(() => {
      expect(screen.getAllByText("OpenClaw").length).toBeGreaterThan(0);
    });

    fireEvent.change(screen.getAllByLabelText("项目名")[0], { target: { value: "Codex" } });
    fireEvent.change(screen.getAllByLabelText("GitHub URL")[0], {
      target: { value: "https://github.com/openai/codex" },
    });
    fireEvent.change(screen.getAllByLabelText("官方文档 URL")[0], {
      target: { value: "https://platform.openai.com/docs" },
    });
    fireEvent.click(screen.getAllByRole("button", { name: "新增项目" })[0]);

    await waitFor(() => {
      expect(screen.getAllByText("Codex").length).toBeGreaterThan(0);
    });
  });

  it("submits AI capability settings with provider switching", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Kubernetes 今日重点：1.31 补丁与网络策略")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "配置中心" })[0]);

    await waitFor(() => {
      expect(screen.getByText("AI 能力管理")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("当前主供应商"), {
      target: { value: "openai" },
    });
    fireEvent.change(screen.getByLabelText("OpenAI 模型"), {
      target: { value: "gpt-5.4" },
    });
    fireEvent.change(screen.getByLabelText("OpenAI 协议"), {
      target: { value: "openai-responses" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存 AI 配置" }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/config",
        expect.objectContaining({
          method: "PUT",
        }),
      );
    });

    const updateCall = global.fetch.mock.calls.find(
      ([url, options]) => url === "/api/config" && options?.method === "PUT",
    );
    const payload = JSON.parse(updateCall[1].body);

    expect(payload.llm.active_provider).toBe("openai");
    expect(payload.llm.openai.model).toBe("gpt-5.4");
    expect(payload.llm.openai.protocol).toBe("openai-responses");
    expect(payload.llm.disable_response_storage).toBe(true);
  });

  it("submits AI provider enable toggles", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Kubernetes 今日重点：1.31 补丁与网络策略")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "配置中心" })[0]);

    await waitFor(() => {
      expect(screen.getByText("AI 能力管理")).toBeInTheDocument();
    });

    const packyToggle = screen.getByLabelText("启用 Packy 通道");
    const openaiToggle = screen.getByLabelText("启用 OpenAI 通道");

    expect(packyToggle).toBeChecked();
    expect(openaiToggle).toBeChecked();

    fireEvent.click(openaiToggle);
    fireEvent.click(screen.getByRole("button", { name: "保存 AI 配置" }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/config",
        expect.objectContaining({
          method: "PUT",
        }),
      );
    });

    const updateCall = global.fetch.mock.calls.find(
      ([url, options]) => url === "/api/config" && options?.method === "PUT",
    );
    const payload = JSON.parse(updateCall[1].body);

    expect(payload.llm.packy.enabled).toBe(true);
    expect(payload.llm.openai.enabled).toBe(false);
  });

  it("submits AI console query with local filters and renders answer evidence and sources", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Kubernetes 今日重点：1.31 补丁与网络策略")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "AI 控制台" })[0]);

    expect(screen.getByLabelText("问题输入")).toBeInTheDocument();
    expect(screen.getByLabelText("项目筛选")).toBeInTheDocument();
    expect(screen.getByLabelText("技术分类")).toBeInTheDocument();
    expect(screen.getByLabelText("时间范围")).toBeInTheDocument();
    expect(screen.queryByLabelText("问答模式")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("问题输入"), {
      target: { value: "OpenClaw 最近网络相关有什么变化？" },
    });
    fireEvent.change(screen.getByLabelText("时间范围"), {
      target: { value: "30d" },
    });
    fireEvent.click(screen.getByRole("button", { name: "发起查询" }));

    await waitFor(() => {
    expect(screen.getByRole("heading", { name: "结论摘要" })).toBeInTheDocument();
    });

    expect(screen.getAllByText("关键依据").length).toBeGreaterThan(0);
    expect(screen.getAllByText("OpenClaw 网络文档更新").length).toBeGreaterThan(0);
    expect(screen.getByText("研究计划")).toBeInTheDocument();
    expect(screen.getByText("检索链路")).toBeInTheDocument();
    expect(screen.getByText("OpenClaw 近 30 天保持高频更新，重点集中在安全修复、会话稳定性和多模态能力演进。")).toBeInTheDocument();
    expect(screen.getByText(`发布时间 ${formatZhDateTime("2026-03-10T08:00:00Z")}`)).toBeInTheDocument();
    expect(screen.getByText("关联: 直接命中目标项目")).toBeInTheDocument();
    expect(screen.getByText("实时来源")).toBeInTheDocument();
    expect(screen.getByText("OpenClaw blog post")).toBeInTheDocument();
    expect(screen.getByText("openclaw recent release notes")).toBeInTheDocument();
  });
});
