import { useEffect, useState } from "react";

import { FOCUS_CATEGORIES, FOCUS_TOPIC_OPTIONS } from "../lib/focusTags";
import HelpTip from "./HelpTip";

const CATEGORY_OPTIONS = ["", ...FOCUS_CATEGORIES];

function normalizeOpenAIRoutes(openaiConfig = {}) {
  const rawRoutes = Array.isArray(openaiConfig?.routes) ? openaiConfig.routes : [];
  const baseRoute = {
    alias: openaiConfig?.model || "主路由",
    enabled: true,
    apiKey: openaiConfig?.api_key || "",
    apiUrl: openaiConfig?.api_url || "",
    model: openaiConfig?.model || "",
    protocol: openaiConfig?.protocol || "openai-responses",
    priority: 1,
  };
  const routes = (rawRoutes.length ? rawRoutes : [baseRoute]).map((route, index) => ({
    alias: route?.alias || (index === 0 ? "主路由" : "备用路由"),
    enabled: route?.enabled ?? true,
    apiKey: route?.api_key || route?.apiKey || (index === 0 ? openaiConfig?.api_key || "" : ""),
    apiUrl: route?.api_url || route?.apiUrl || openaiConfig?.api_url || "",
    model: route?.model || (index === 0 ? openaiConfig?.model || "" : ""),
    protocol: route?.protocol || (index === 0 ? openaiConfig?.protocol || "openai-responses" : openaiConfig?.protocol || "openai-responses"),
    priority: Number(route?.priority) || index + 1,
  }));
  if (routes.length < 2) {
    routes.push({
      alias: "备用路由",
      enabled: true,
      apiKey: "",
      apiUrl: routes[0]?.apiUrl || openaiConfig?.api_url || "",
      model: "",
      protocol: routes[0]?.protocol || openaiConfig?.protocol || "openai-responses",
      priority: 2,
    });
  }
  return routes
    .sort((left, right) => Number(left.priority || 0) - Number(right.priority || 0))
    .slice(0, 2);
}

function SummaryMetric({ label, value, tone = "default" }) {
  return (
    <article className={`console-summary-card console-summary-card--${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function sourceLabel(source) {
  if (source === "config") return "配置";
  if (source === "env") return "环境变量";
  return "未配置";
}

function EffectiveConfig({ data }) {
  const maskedKey = data?.api_key_masked || "";
  const keySource = sourceLabel(data?.api_key_source);
  return (
    <div className="llm-effective card-tier--hero">
      <p className="llm-effective__title">生效值</p>
      <div className="llm-effective__row">
        <span className="llm-effective__label">API Key</span>
        <strong className="llm-effective__value">{maskedKey || "未配置"}</strong>
        <span className="llm-effective__source">{`来源：${keySource}`}</span>
      </div>
      <div className="llm-effective__row">
        <span className="llm-effective__label">API URL</span>
        <strong className="llm-effective__value">{data?.effective_api_url || "未配置"}</strong>
      </div>
      <div className="llm-effective__row">
        <span className="llm-effective__label">模型</span>
        <strong className="llm-effective__value">{data?.effective_model || "未配置"}</strong>
      </div>
      <div className="llm-effective__row">
        <span className="llm-effective__label">协议</span>
        <strong className="llm-effective__value">{data?.effective_protocol || "未配置"}</strong>
      </div>
      <div className="llm-effective__row">
        <span className="llm-effective__label">供应商</span>
        <strong className="llm-effective__value">{data?.effective_provider || "未配置"}</strong>
      </div>
    </div>
  );
}

function SettingsSectionHeader({ title, help }) {
  return (
    <div className="settings-panel__header">
      <div className="settings-panel__title">
        <h2>{title}</h2>
        <HelpTip label={`${title}说明`} text={help} />
      </div>
    </div>
  );
}

function MustWatchTransfer({ projects, value, onChange }) {
  const [query, setQuery] = useState("");
  const [availableSelection, setAvailableSelection] = useState("");
  const [selectedSelection, setSelectedSelection] = useState("");
  const selectedIds = new Set(value);
  const normalizedQuery = query.trim().toLowerCase();
  const availableProjects = projects.filter((project) => {
    if (selectedIds.has(project.id)) {
      return false;
    }
    if (!normalizedQuery) {
      return true;
    }
    return (project.name || project.id).toLowerCase().includes(normalizedQuery);
  });
  const selectedProjects = value
    .map((projectId) => projects.find((project) => project.id === projectId) || { id: projectId, name: projectId })
    .filter(Boolean);

  useEffect(() => {
    if (availableSelection && !availableProjects.some((project) => project.id === availableSelection)) {
      setAvailableSelection("");
    }
  }, [availableProjects, availableSelection]);

  useEffect(() => {
    if (selectedSelection && !selectedProjects.some((project) => project.id === selectedSelection)) {
      setSelectedSelection("");
    }
  }, [selectedProjects, selectedSelection]);

  function addProject() {
    if (!availableSelection || selectedIds.has(availableSelection)) {
      return;
    }
    onChange([...value, availableSelection]);
    setSelectedSelection(availableSelection);
    setAvailableSelection("");
  }

  function removeProject() {
    if (!selectedSelection) {
      return;
    }
    onChange(value.filter((projectId) => projectId !== selectedSelection));
    setSelectedSelection("");
  }

  return (
    <div className="digest-transfer assistant-config-form__full">
      <div className="digest-transfer__panel">
        <div className="digest-transfer__panel-header">
          <strong>项目库</strong>
          <span>{availableProjects.length} 项</span>
        </div>
        <label className="digest-transfer__search">
          <span>搜索置顶项目</span>
          <input
            aria-label="搜索置顶项目"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="按项目名筛选"
          />
        </label>
        <div className="digest-transfer__list" role="listbox" aria-label="待选项目">
          {availableProjects.length ? (
            availableProjects.map((project) => (
              <button
                key={project.id}
                type="button"
                className={`digest-transfer__item ${availableSelection === project.id ? "digest-transfer__item--active" : ""}`}
                onClick={() => setAvailableSelection(project.id)}
              >
                {project.name || project.id}
              </button>
            ))
          ) : (
            <div className="digest-transfer__empty">没有匹配项目</div>
          )}
        </div>
      </div>

      <div className="digest-transfer__actions">
        <button type="button" className="digest-transfer__action" onClick={addProject} disabled={!availableSelection}>
          加入必看
        </button>
        <button type="button" className="digest-transfer__action" onClick={removeProject} disabled={!selectedSelection}>
          移出必看
        </button>
      </div>

      <div className="digest-transfer__panel">
        <div className="digest-transfer__panel-header">
          <strong>已置顶</strong>
          <span>{selectedProjects.length} 项</span>
        </div>
        <div className="digest-transfer__list" role="listbox" aria-label="已置顶项目">
          {selectedProjects.length ? (
            selectedProjects.map((project) => (
              <button
                key={project.id}
                type="button"
                className={`digest-transfer__item ${selectedSelection === project.id ? "digest-transfer__item--active" : ""}`}
                onClick={() => setSelectedSelection(project.id)}
              >
                {project.name || project.id}
              </button>
            ))
          ) : (
            <div className="digest-transfer__empty">还没有置顶项目</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage({
  config,
  projects,
  projectForm,
  setProjectForm,
  submittingProject,
  savingProjectMetadataId,
  savingConfig,
  onProjectSubmit,
  onProjectMetadataSave,
  onConfigSave,
}) {
  const [llmForm, setLlmForm] = useState({
    activeProvider: "packy",
    reasoningEffort: "",
    disableResponseStorage: false,
    packy: {
      enabled: true,
      apiKey: "",
      provider: "",
      apiUrl: "",
      model: "",
      protocol: "",
      apiKeyConfigured: false,
    },
    openai: {
      enabled: true,
      apiKey: "",
      provider: "OpenAI",
      apiUrl: "",
      model: "",
      protocol: "",
      apiKeyConfigured: false,
      routes: normalizeOpenAIRoutes(),
    },
  });
  const [assistantForm, setAssistantForm] = useState({
    enabled: true,
    defaultProjectId: "",
    defaultCategory: "",
    defaultTimeframe: "14d",
    maxEvidenceItems: 3,
    maxSourceItems: 4,
    liveSearchEnabled: true,
    liveSearchProvider: "duckduckgo",
    liveSearchMaxResults: 5,
    liveSearchMaxPages: 3,
    classificationPrompt: "",
    answerPrompt: "",
  });
  const [dailyRankingForm, setDailyRankingForm] = useState({
    importanceWeight: 0.45,
    recencyWeight: 0.25,
    evidenceWeight: 0.2,
    sourceWeight: 0.1,
    recencyHalfLifeDays: 3,
    readDecayDays: 2,
    readDecayFactor: 0.5,
    mmrLambda: 0.7,
    mmrDiversityKeys: "source,category,tags",
  });
  const [dailyDigestForm, setDailyDigestForm] = useState({
    mustWatchProjectIds: [],
    mustWatchDays: 30,
    emergingDays: 3,
  });

  useEffect(() => {
    setLlmForm({
      activeProvider: config?.llm?.active_provider || "packy",
      reasoningEffort: config?.llm?.reasoning_effort || "",
      disableResponseStorage: config?.llm?.disable_response_storage ?? false,
      packy: {
        enabled: config?.llm?.packy?.enabled ?? true,
        apiKey: config?.llm?.packy?.api_key || "",
        provider: config?.llm?.packy?.provider || "",
        apiUrl: config?.llm?.packy?.api_url || "",
        model: config?.llm?.packy?.model || "",
        protocol: config?.llm?.packy?.protocol || "",
        apiKeyConfigured: config?.llm?.packy?.api_key_configured ?? false,
      },
      openai: {
        enabled: config?.llm?.openai?.enabled ?? true,
        apiKey: config?.llm?.openai?.api_key || "",
        provider: config?.llm?.openai?.provider || "OpenAI",
        apiUrl: config?.llm?.openai?.api_url || "",
        model: config?.llm?.openai?.model || "",
        protocol: config?.llm?.openai?.protocol || "",
        apiKeyConfigured: config?.llm?.openai?.api_key_configured ?? false,
        routes: normalizeOpenAIRoutes(config?.llm?.openai),
      },
    });
    setAssistantForm({
      enabled: config?.assistant?.enabled ?? true,
      defaultProjectId: config?.assistant?.default_project_ids?.[0] || "",
      defaultCategory: config?.assistant?.default_categories?.[0] || "",
      defaultTimeframe: config?.assistant?.default_timeframe || "14d",
      maxEvidenceItems: config?.assistant?.max_evidence_items || 3,
      maxSourceItems: config?.assistant?.max_source_items || 4,
      liveSearchEnabled: config?.assistant?.live_search?.enabled ?? true,
      liveSearchProvider: config?.assistant?.live_search?.provider || "duckduckgo",
      liveSearchMaxResults: config?.assistant?.live_search?.max_results || 5,
      liveSearchMaxPages: config?.assistant?.live_search?.max_pages || 3,
      classificationPrompt: config?.assistant?.prompts?.classification || "",
      answerPrompt: config?.assistant?.prompts?.answer || "",
    });
    setDailyRankingForm({
      importanceWeight: config?.daily_ranking?.weights?.importance ?? 0.45,
      recencyWeight: config?.daily_ranking?.weights?.recency ?? 0.25,
      evidenceWeight: config?.daily_ranking?.weights?.evidence ?? 0.2,
      sourceWeight: config?.daily_ranking?.weights?.source ?? 0.1,
      recencyHalfLifeDays: config?.daily_ranking?.recency_half_life_days ?? 3,
      readDecayDays: config?.daily_ranking?.read_decay_days ?? 2,
      readDecayFactor: config?.daily_ranking?.read_decay_factor ?? 0.5,
      mmrLambda: config?.daily_ranking?.mmr_lambda ?? 0.7,
      mmrDiversityKeys: (config?.daily_ranking?.mmr_diversity_keys ?? ["source", "category", "tags"]).join(","),
    });
    setDailyDigestForm({
      mustWatchProjectIds: config?.daily_digest?.must_watch_project_ids ?? [],
      mustWatchDays: config?.daily_digest?.must_watch_days ?? 30,
      emergingDays: config?.daily_digest?.emerging_days ?? 3,
    });
  }, [config]);
  const packyEffective = config?.llm?.packy;
  const openaiEffective = config?.llm?.openai;
  const openaiPrimaryRoute = llmForm.openai.routes?.[0] || { alias: "主路由" };
  const openaiBackupRoute = llmForm.openai.routes?.[1] || { alias: "备用路由" };
  const openaiRouteChain = (llmForm.openai.routes || [])
    .filter((route) => route.enabled && route.model)
    .map((route) => route.model)
    .join(" -> ") || "未配置";

  function updateOpenAIRoute(index, patch) {
    setLlmForm((current) => {
      const routes = normalizeOpenAIRoutes(current.openai).map((route, routeIndex) =>
        routeIndex === index ? { ...route, ...patch, priority: routeIndex + 1 } : { ...route, priority: routeIndex + 1 },
      );
      const primaryRoute = routes[0] || {};
      return {
        ...current,
        openai: {
          ...current.openai,
          apiKey: primaryRoute.apiKey || "",
          apiUrl: primaryRoute.apiUrl || "",
          model: primaryRoute.model || "",
          protocol: primaryRoute.protocol || "",
          routes,
        },
      };
    });
  }

  async function handleLlmSubmit(event) {
    event.preventDefault();
    const openaiRoutes = (llmForm.openai.routes || []).map((route, index) => ({
      alias: route.alias || (index === 0 ? "主路由" : "备用路由"),
      enabled: route.enabled ?? true,
      api_key: route.apiKey,
      api_url: route.apiUrl,
      model: route.model,
      protocol: route.protocol,
      priority: index + 1,
    }));
    const primaryRoute = openaiRoutes[0] || {};
    await onConfigSave({
      llm: {
        active_provider: llmForm.activeProvider,
        reasoning_effort: llmForm.reasoningEffort,
        disable_response_storage: llmForm.disableResponseStorage,
        packy: {
          enabled: llmForm.packy.enabled,
          api_key: llmForm.packy.apiKey,
          provider: llmForm.packy.provider,
          api_url: llmForm.packy.apiUrl,
          model: llmForm.packy.model,
          protocol: llmForm.packy.protocol,
        },
        openai: {
          enabled: llmForm.openai.enabled,
          api_key: primaryRoute.api_key || "",
          provider: llmForm.openai.provider,
          api_url: primaryRoute.api_url || llmForm.openai.apiUrl,
          model: primaryRoute.model || llmForm.openai.model,
          protocol: primaryRoute.protocol || llmForm.openai.protocol,
          routes: openaiRoutes,
        },
      },
    });
  }

  async function handleAssistantSubmit(event) {
    event.preventDefault();
    await onConfigSave({
      assistant: {
        enabled: assistantForm.enabled,
        default_mode: "live",
        default_project_ids: assistantForm.defaultProjectId ? [assistantForm.defaultProjectId] : [],
        default_categories: assistantForm.defaultCategory ? [assistantForm.defaultCategory] : [],
        default_timeframe: assistantForm.defaultTimeframe,
        max_evidence_items: Number(assistantForm.maxEvidenceItems),
        max_source_items: Number(assistantForm.maxSourceItems),
        live_search: {
          enabled: assistantForm.liveSearchEnabled,
          provider: assistantForm.liveSearchProvider,
          max_results: Number(assistantForm.liveSearchMaxResults),
          max_pages: Number(assistantForm.liveSearchMaxPages),
        },
        prompts: {
          classification: assistantForm.classificationPrompt,
          answer: assistantForm.answerPrompt,
        },
      },
    });
  }

  function toNumber(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  async function handleDailyRankingSubmit(event) {
    event.preventDefault();
    const diversityKeys = dailyRankingForm.mmrDiversityKeys
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    await onConfigSave({
      daily_ranking: {
        weights: {
          importance: toNumber(dailyRankingForm.importanceWeight, 0.45),
          recency: toNumber(dailyRankingForm.recencyWeight, 0.25),
          evidence: toNumber(dailyRankingForm.evidenceWeight, 0.2),
          source: toNumber(dailyRankingForm.sourceWeight, 0.1),
        },
        recency_half_life_days: toNumber(dailyRankingForm.recencyHalfLifeDays, 3),
        read_decay_days: Math.max(0, Math.floor(toNumber(dailyRankingForm.readDecayDays, 2))),
        read_decay_factor: toNumber(dailyRankingForm.readDecayFactor, 0.5),
        mmr_lambda: toNumber(dailyRankingForm.mmrLambda, 0.7),
        mmr_diversity_keys: diversityKeys,
      },
    });
  }

  async function handleDailyDigestSubmit(event) {
    event.preventDefault();
    await onConfigSave({
      daily_digest: {
        must_watch_project_ids: dailyDigestForm.mustWatchProjectIds,
        emerging_project_ids: [],
        must_watch_days: Math.max(1, Math.floor(toNumber(dailyDigestForm.mustWatchDays, 30))),
        emerging_days: Math.max(1, Math.floor(toNumber(dailyDigestForm.emergingDays, 3))),
      },
    });
  }

  return (
    <section className="settings-page">
      <section className="settings-panel">
        <SettingsSectionHeader title="模型" help="切换主供应商并维护两套模型网关。" />

        <form className="assistant-config-form settings-console-form" onSubmit={handleLlmSubmit}>
          <div className="assistant-config-form__full console-summary-row">
            <SummaryMetric label="主通道" value={llmForm.activeProvider === "packy" ? "Packy" : "OpenAI"} tone="primary" />
            <SummaryMetric label="路由" value={openaiRouteChain} />
            <SummaryMetric label="存档" value={llmForm.disableResponseStorage ? "关闭" : "开启"} />
          </div>

          <div className="assistant-config-form__full settings-toolbar-grid">
            <label>
              <span>当前主供应商</span>
              <select
                aria-label="当前主供应商"
                value={llmForm.activeProvider}
                onChange={(event) => setLlmForm((current) => ({ ...current, activeProvider: event.target.value }))}
              >
                <option value="packy">Packy</option>
                <option value="openai">OpenAI</option>
              </select>
            </label>

            <label>
              <span>推理强度</span>
              <input
                aria-label="推理强度"
                value={llmForm.reasoningEffort}
                onChange={(event) => setLlmForm((current) => ({ ...current, reasoningEffort: event.target.value }))}
                placeholder="例如 xhigh"
              />
            </label>

            <label className="assistant-config-form__toggle settings-switch-tile">
              <input
                type="checkbox"
                checked={llmForm.disableResponseStorage}
                onChange={(event) => setLlmForm((current) => ({ ...current, disableResponseStorage: event.target.checked }))}
              />
              <span>禁用响应存档</span>
            </label>

            <label className="assistant-config-form__toggle settings-switch-tile">
              <input
                type="checkbox"
                checked={llmForm.packy.enabled}
                onChange={(event) =>
                  setLlmForm((current) => ({
                    ...current,
                    packy: { ...current.packy, enabled: event.target.checked },
                  }))
                }
              />
              <span>启用 Packy 通道</span>
            </label>

            <label className="assistant-config-form__toggle settings-switch-tile">
              <input
                type="checkbox"
                checked={llmForm.openai.enabled}
                onChange={(event) =>
                  setLlmForm((current) => ({
                    ...current,
                    openai: { ...current.openai, enabled: event.target.checked },
                  }))
                }
              />
              <span>启用 OpenAI 通道</span>
            </label>
          </div>

          <div className="settings-inline-note assistant-config-form__full">
            <strong>当前策略</strong>
            <span>先走 gpt-5.4，失败后自动切到 gpt-5.2；两条路由都失败时，任务会直接告警并中止。</span>
          </div>

          <div className="llm-provider-grid assistant-config-form__full settings-console-grid">
            <section
              className={`llm-provider-card card-tier--focus ${llmForm.activeProvider === "packy" ? "llm-provider-card--active" : ""}`}
            >
              <div className="llm-provider-card__header">
                <div>
                  <p className="section-kicker">Gateway</p>
                  <h3>Packy</h3>
                </div>
                <span className="llm-provider-card__badge">{llmForm.activeProvider === "packy" ? "主通道" : "备用"}</span>
              </div>
              <div className="llm-provider-card__status">{llmForm.packy.apiKeyConfigured ? "已配置" : "未配置"}</div>
              <EffectiveConfig data={packyEffective} />
              <div className="assistant-config-form llm-provider-card__form">
                <label className="assistant-config-form__full">
                  <span>Packy API Key</span>
                  <input
                    type="password"
                    aria-label="Packy API Key"
                    value={llmForm.packy.apiKey}
                    onChange={(event) =>
                      setLlmForm((current) => ({
                        ...current,
                        packy: { ...current.packy, apiKey: event.target.value },
                      }))
                    }
                    placeholder="留空时沿用 PACKY_API_KEY"
                  />
                </label>
                <label>
                  <span>Packy 供应商标识</span>
                  <input
                    aria-label="Packy 供应商标识"
                    value={llmForm.packy.provider}
                    onChange={(event) =>
                      setLlmForm((current) => ({
                        ...current,
                        packy: { ...current.packy, provider: event.target.value },
                      }))
                    }
                  />
                </label>
                <label>
                  <span>Packy API URL</span>
                  <input
                    aria-label="Packy API URL"
                    value={llmForm.packy.apiUrl}
                    onChange={(event) =>
                      setLlmForm((current) => ({
                        ...current,
                        packy: { ...current.packy, apiUrl: event.target.value },
                      }))
                    }
                  />
                </label>
                <label>
                  <span>Packy 模型</span>
                  <input
                    aria-label="Packy 模型"
                    value={llmForm.packy.model}
                    onChange={(event) =>
                      setLlmForm((current) => ({
                        ...current,
                        packy: { ...current.packy, model: event.target.value },
                      }))
                    }
                  />
                </label>
                <label>
                  <span>Packy 协议</span>
                  <input
                    aria-label="Packy 协议"
                    value={llmForm.packy.protocol}
                    onChange={(event) =>
                      setLlmForm((current) => ({
                        ...current,
                        packy: { ...current.packy, protocol: event.target.value },
                      }))
                    }
                    placeholder="例如 openai-chat"
                  />
                </label>
              </div>
            </section>

            <section
              className={`llm-provider-card card-tier--focus ${llmForm.activeProvider === "openai" ? "llm-provider-card--active" : ""}`}
            >
              <div className="llm-provider-card__header">
                <div>
                  <p className="section-kicker">Failover</p>
                  <h3>OpenAI</h3>
                </div>
                <span className="llm-provider-card__badge">{llmForm.activeProvider === "openai" ? "主通道" : "备用"}</span>
              </div>
              <div className="llm-provider-card__status">{llmForm.openai.apiKeyConfigured ? "已配置" : "未配置"}</div>
              <EffectiveConfig data={openaiEffective} />
              <div className="assistant-config-form llm-provider-card__form">
                <label className="assistant-config-form__full">
                  <span>OpenAI 供应商标识</span>
                  <input
                    aria-label="OpenAI 供应商标识"
                    value={llmForm.openai.provider}
                    onChange={(event) =>
                      setLlmForm((current) => ({
                        ...current,
                        openai: { ...current.openai, provider: event.target.value },
                      }))
                    }
                  />
                </label>
              </div>

              <div className="route-card-grid">
                <section className="route-card route-card--primary">
                  <header>
                    <strong>{openaiPrimaryRoute.model || openaiPrimaryRoute.alias || "主路由"}</strong>
                    <span>优先级 1</span>
                  </header>
                  <div className="assistant-config-form llm-provider-card__form route-card__form">
                    <label className="assistant-config-form__toggle settings-switch-tile assistant-config-form__full">
                      <input
                        type="checkbox"
                        checked={openaiPrimaryRoute.enabled ?? true}
                        onChange={(event) => updateOpenAIRoute(0, { enabled: event.target.checked })}
                      />
                      <span>主路由启用</span>
                    </label>
                    <label className="assistant-config-form__full">
                      <span>OpenAI API Key</span>
                      <input
                        type="password"
                        aria-label="OpenAI API Key"
                        value={openaiPrimaryRoute.apiKey || ""}
                        onChange={(event) => updateOpenAIRoute(0, { apiKey: event.target.value })}
                        placeholder="留空时沿用 OPENAI_API_KEY"
                      />
                    </label>
                    <label>
                      <span>OpenAI API URL</span>
                      <input
                        aria-label="OpenAI API URL"
                        value={openaiPrimaryRoute.apiUrl || ""}
                        onChange={(event) => updateOpenAIRoute(0, { apiUrl: event.target.value })}
                      />
                    </label>
                    <label>
                      <span>OpenAI 模型</span>
                      <input
                        aria-label="OpenAI 模型"
                        value={openaiPrimaryRoute.model || ""}
                        onChange={(event) => updateOpenAIRoute(0, { model: event.target.value })}
                      />
                    </label>
                    <label>
                      <span>OpenAI 协议</span>
                      <input
                        aria-label="OpenAI 协议"
                        value={openaiPrimaryRoute.protocol || ""}
                        onChange={(event) => updateOpenAIRoute(0, { protocol: event.target.value })}
                        placeholder="例如 openai-responses"
                      />
                    </label>
                  </div>
                </section>

                <section className="route-card route-card--secondary">
                  <header>
                    <strong>{openaiBackupRoute.model || openaiBackupRoute.alias || "备用路由"}</strong>
                    <span>优先级 2</span>
                  </header>
                  <div className="assistant-config-form llm-provider-card__form route-card__form">
                    <label className="assistant-config-form__toggle settings-switch-tile assistant-config-form__full">
                      <input
                        type="checkbox"
                        checked={openaiBackupRoute.enabled ?? true}
                        onChange={(event) => updateOpenAIRoute(1, { enabled: event.target.checked })}
                      />
                      <span>备用路由启用</span>
                    </label>
                    <label className="assistant-config-form__full">
                      <span>备用 API Key</span>
                      <input
                        type="password"
                        aria-label="备用 API Key"
                        value={openaiBackupRoute.apiKey || ""}
                        onChange={(event) => updateOpenAIRoute(1, { apiKey: event.target.value })}
                      />
                    </label>
                    <label>
                      <span>备用 API URL</span>
                      <input
                        aria-label="备用 API URL"
                        value={openaiBackupRoute.apiUrl || ""}
                        onChange={(event) => updateOpenAIRoute(1, { apiUrl: event.target.value })}
                      />
                    </label>
                    <label>
                      <span>备用模型</span>
                      <input
                        aria-label="备用模型"
                        value={openaiBackupRoute.model || ""}
                        onChange={(event) => updateOpenAIRoute(1, { model: event.target.value })}
                      />
                    </label>
                    <label>
                      <span>备用协议</span>
                      <input
                        aria-label="备用协议"
                        value={openaiBackupRoute.protocol || ""}
                        onChange={(event) => updateOpenAIRoute(1, { protocol: event.target.value })}
                      />
                    </label>
                  </div>
                </section>
              </div>
            </section>
          </div>

          <button className="primary-button" type="submit" disabled={savingConfig}>
            {savingConfig ? "保存中..." : "保存 AI 配置"}
          </button>
        </form>
      </section>

      <section className="settings-panel">
        <SettingsSectionHeader title="助手" help="设置 Assistant 默认筛选、搜索和 Prompt。" />

        <form className="assistant-config-form settings-console-form" onSubmit={handleAssistantSubmit}>
          <div className="assistant-config-form__full console-summary-row">
            <SummaryMetric label="状态" value={assistantForm.enabled ? "已启用" : "已关闭"} tone={assistantForm.enabled ? "primary" : "default"} />
            <SummaryMetric
              label="默认范围"
              value={`${assistantForm.defaultProjectId ? projects.find((project) => project.id === assistantForm.defaultProjectId)?.name || assistantForm.defaultProjectId : "全部项目"} / ${assistantForm.defaultTimeframe}`}
            />
            <SummaryMetric label="检索" value={assistantForm.liveSearchEnabled ? `${assistantForm.liveSearchProvider} · ${assistantForm.liveSearchMaxResults}` : "关闭"} />
          </div>

          <div className="settings-console-grid settings-console-grid--assistant assistant-config-form__full">
            <section className="console-card card-tier--focus">
              <div className="llm-provider-card__header">
                <div>
                  <p className="section-kicker">Scope</p>
                  <h3>默认范围</h3>
                </div>
              </div>
              <div className="assistant-config-form llm-provider-card__form route-card__form">
                <label className="assistant-config-form__toggle settings-switch-tile assistant-config-form__full">
                  <input
                    type="checkbox"
                    checked={assistantForm.enabled}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, enabled: event.target.checked }))}
                  />
                  <span>Assistant 已启用</span>
                </label>

                <label>
                  <span>默认项目</span>
                  <select
                    aria-label="默认项目"
                    value={assistantForm.defaultProjectId}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, defaultProjectId: event.target.value }))}
                  >
                    <option value="">全部项目</option>
                    {projects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  <span>默认分类</span>
                  <select
                    aria-label="默认分类"
                    value={assistantForm.defaultCategory}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, defaultCategory: event.target.value }))}
                  >
                    {CATEGORY_OPTIONS.map((item) => (
                      <option key={item || "all"} value={item}>
                        {item || "全部分类"}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="assistant-config-form__full">
                  <span>默认时间范围</span>
                  <input
                    aria-label="默认时间范围"
                    value={assistantForm.defaultTimeframe}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, defaultTimeframe: event.target.value }))}
                  />
                </label>
              </div>
            </section>

            <section className="console-card card-tier--focus">
              <div className="llm-provider-card__header">
                <div>
                  <p className="section-kicker">Retrieval</p>
                  <h3>检索</h3>
                </div>
              </div>
              <div className="assistant-config-form llm-provider-card__form route-card__form">
                <label>
                  <span>证据条数</span>
                  <input
                    type="number"
                    value={assistantForm.maxEvidenceItems}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, maxEvidenceItems: event.target.value }))}
                  />
                </label>

                <label>
                  <span>来源条数</span>
                  <input
                    type="number"
                    value={assistantForm.maxSourceItems}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, maxSourceItems: event.target.value }))}
                  />
                </label>

                <label className="assistant-config-form__toggle settings-switch-tile assistant-config-form__full">
                  <input
                    type="checkbox"
                    checked={assistantForm.liveSearchEnabled}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, liveSearchEnabled: event.target.checked }))}
                  />
                  <span>启用实时搜索</span>
                </label>

                <label>
                  <span>搜索提供方</span>
                  <input
                    aria-label="搜索提供方"
                    value={assistantForm.liveSearchProvider}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, liveSearchProvider: event.target.value }))}
                  />
                </label>

                <label>
                  <span>搜索结果数</span>
                  <input
                    type="number"
                    aria-label="搜索结果数"
                    value={assistantForm.liveSearchMaxResults}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, liveSearchMaxResults: event.target.value }))}
                  />
                </label>

                <label className="assistant-config-form__full">
                  <span>抓取页数</span>
                  <input
                    type="number"
                    aria-label="抓取页数"
                    value={assistantForm.liveSearchMaxPages}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, liveSearchMaxPages: event.target.value }))}
                  />
                </label>
              </div>
            </section>

            <section className="console-card card-tier--focus assistant-config-form__full">
              <div className="llm-provider-card__header">
                <div>
                  <p className="section-kicker">Prompt</p>
                  <h3>Prompt</h3>
                </div>
              </div>
              <div className="assistant-config-form">
                <label className="assistant-config-form__full">
                  <span>分类 Prompt</span>
                  <textarea
                    aria-label="分类 Prompt"
                    value={assistantForm.classificationPrompt}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, classificationPrompt: event.target.value }))}
                    rows={3}
                  />
                </label>

                <label className="assistant-config-form__full">
                  <span>回答 Prompt</span>
                  <textarea
                    aria-label="回答 Prompt"
                    value={assistantForm.answerPrompt}
                    onChange={(event) => setAssistantForm((current) => ({ ...current, answerPrompt: event.target.value }))}
                    rows={4}
                  />
                </label>
              </div>
            </section>
          </div>

          <button className="primary-button" type="submit" disabled={savingConfig}>
            {savingConfig ? "保存中..." : "保存 Assistant 配置"}
          </button>
        </form>
      </section>

      <section className="settings-panel">
        <SettingsSectionHeader title="日报分区" help="只维护老牌必看项目；近期更新会按窗口自动收录。" />

        <form className="assistant-config-form" onSubmit={handleDailyDigestSubmit}>
          <div className="settings-inline-note assistant-config-form__full">
            <strong>当前规则</strong>
            <span>{`置顶项目手动维护；近期更新会自动收录最近 ${dailyDigestForm.emergingDays || 3} 天内有变化、且不在置顶区的项目。`}</span>
          </div>

          <label className="assistant-config-form__full">
            <span>老牌必看项目</span>
            <MustWatchTransfer
              projects={projects}
              value={dailyDigestForm.mustWatchProjectIds}
              onChange={(mustWatchProjectIds) =>
                setDailyDigestForm((current) => ({
                  ...current,
                  mustWatchProjectIds,
                }))
              }
            />
          </label>

          <label>
            <span>老牌必看窗口（天）</span>
            <input
              type="number"
              step="1"
              min="1"
              aria-label="老牌必看窗口（天）"
              value={dailyDigestForm.mustWatchDays}
              onChange={(event) =>
                setDailyDigestForm((current) => ({ ...current, mustWatchDays: event.target.value }))
              }
            />
          </label>
          <label>
            <span>近期更新窗口（天）</span>
            <input
              type="number"
              step="1"
              min="1"
              aria-label="近期更新窗口（天）"
              value={dailyDigestForm.emergingDays}
              onChange={(event) =>
                setDailyDigestForm((current) => ({ ...current, emergingDays: event.target.value }))
              }
            />
          </label>

          <button className="primary-button" type="submit" disabled={savingConfig}>
            {savingConfig ? "保存中..." : "保存日报分区"}
          </button>
        </form>
      </section>

      <section className="settings-panel">
        <div className="settings-panel__header">
          <div>
            <p className="section-kicker">Ranking</p>
            <h2>日报排序</h2>
          </div>
          <p className="settings-panel__copy">调整日报排序权重与已读衰减规则，实时影响首页项目排位。</p>
        </div>

        <form className="assistant-config-form" onSubmit={handleDailyRankingSubmit}>
          <label>
            <span>重要度权重</span>
            <input
              type="number"
              step="0.05"
              aria-label="重要度权重"
              value={dailyRankingForm.importanceWeight}
              onChange={(event) =>
                setDailyRankingForm((current) => ({ ...current, importanceWeight: event.target.value }))
              }
            />
          </label>
          <label>
            <span>时效权重</span>
            <input
              type="number"
              step="0.05"
              aria-label="时效权重"
              value={dailyRankingForm.recencyWeight}
              onChange={(event) =>
                setDailyRankingForm((current) => ({ ...current, recencyWeight: event.target.value }))
              }
            />
          </label>
          <label>
            <span>证据权重</span>
            <input
              type="number"
              step="0.05"
              aria-label="证据权重"
              value={dailyRankingForm.evidenceWeight}
              onChange={(event) =>
                setDailyRankingForm((current) => ({ ...current, evidenceWeight: event.target.value }))
              }
            />
          </label>
          <label>
            <span>来源权重</span>
            <input
              type="number"
              step="0.05"
              aria-label="来源权重"
              value={dailyRankingForm.sourceWeight}
              onChange={(event) =>
                setDailyRankingForm((current) => ({ ...current, sourceWeight: event.target.value }))
              }
            />
          </label>
          <label>
            <span>时效半衰期（天）</span>
            <input
              type="number"
              step="1"
              aria-label="时效半衰期（天）"
              value={dailyRankingForm.recencyHalfLifeDays}
              onChange={(event) =>
                setDailyRankingForm((current) => ({ ...current, recencyHalfLifeDays: event.target.value }))
              }
            />
          </label>
          <label>
            <span>已读衰减天数</span>
            <input
              type="number"
              step="1"
              aria-label="已读衰减天数"
              value={dailyRankingForm.readDecayDays}
              onChange={(event) =>
                setDailyRankingForm((current) => ({ ...current, readDecayDays: event.target.value }))
              }
            />
          </label>
          <label>
            <span>已读衰减系数</span>
            <input
              type="number"
              step="0.05"
              aria-label="已读衰减系数"
              value={dailyRankingForm.readDecayFactor}
              onChange={(event) =>
                setDailyRankingForm((current) => ({ ...current, readDecayFactor: event.target.value }))
              }
            />
          </label>
          <label>
            <span>MMR λ</span>
            <input
              type="number"
              step="0.05"
              aria-label="MMR λ"
              value={dailyRankingForm.mmrLambda}
              onChange={(event) =>
                setDailyRankingForm((current) => ({ ...current, mmrLambda: event.target.value }))
              }
            />
          </label>
          <label className="assistant-config-form__full">
            <span>多样性维度</span>
            <input
              aria-label="多样性维度"
              value={dailyRankingForm.mmrDiversityKeys}
              onChange={(event) =>
                setDailyRankingForm((current) => ({ ...current, mmrDiversityKeys: event.target.value }))
              }
              placeholder="source,category,tags"
            />
          </label>

          <button className="primary-button" type="submit" disabled={savingConfig}>
            {savingConfig ? "保存中..." : "保存排序参数"}
          </button>
        </form>
      </section>

      <section className="settings-panel project-admin">
        <div className="project-admin__header">
          <div className="settings-panel__title">
            <h2>项目</h2>
            <HelpTip label="项目说明" text="维护项目来源、技术分类和关注主题。" />
          </div>
        </div>

        <form className="project-form" onSubmit={onProjectSubmit}>
          <label>
            <span>项目名</span>
            <input
              aria-label="项目名"
              value={projectForm.name}
              onChange={(event) => setProjectForm((current) => ({ ...current, name: event.target.value }))}
            />
          </label>
          <label>
            <span>GitHub URL</span>
            <input
              aria-label="GitHub URL"
              value={projectForm.githubUrl}
              onChange={(event) => setProjectForm((current) => ({ ...current, githubUrl: event.target.value }))}
            />
          </label>
          <label>
            <span>官方文档 URL</span>
            <input
              aria-label="官方文档 URL"
              value={projectForm.docsUrl}
              onChange={(event) => setProjectForm((current) => ({ ...current, docsUrl: event.target.value }))}
            />
          </label>
          <button className="primary-button" type="submit" disabled={submittingProject}>
            {submittingProject ? "新增中..." : "新增项目"}
          </button>
        </form>

        <div className="project-admin__list">
          {projects.map((project) => (
            <article key={project.id} className="project-chip">
              <strong>{project.name}</strong>
              <span>{project.github_url}</span>
              {project.docs_url ? <span>{project.docs_url}</span> : <span>无文档区</span>}
              <div className="project-chip__taxonomy">
                <label>
                  <span>技术分类</span>
                  <div className="project-chip__pill-row">
                    {FOCUS_CATEGORIES.map((category) => {
                      const selected = (project.tech_categories || []).includes(category);
                      return (
                        <button
                          key={category}
                          type="button"
                          className={`monitor-filter-pill ${selected ? "monitor-filter-pill--active" : ""}`}
                          onClick={() =>
                            onProjectMetadataSave(project.id, {
                              tech_categories: selected
                                ? (project.tech_categories || []).filter((item) => item !== category)
                                : [...(project.tech_categories || []), category],
                            })
                          }
                          disabled={savingProjectMetadataId === project.id}
                        >
                          {category}
                        </button>
                      );
                    })}
                  </div>
                </label>
                <label>
                  <span>关注主题</span>
                  <div className="project-chip__pill-row">
                    {FOCUS_TOPIC_OPTIONS.map((topic) => {
                      const selected = (project.focus_topics || []).includes(topic);
                      return (
                        <button
                          key={topic}
                          type="button"
                          className={`monitor-filter-pill ${selected ? "monitor-filter-pill--active" : ""}`}
                          onClick={() =>
                            onProjectMetadataSave(project.id, {
                              focus_topics: selected
                                ? (project.focus_topics || []).filter((item) => item !== topic)
                                : [...(project.focus_topics || []), topic],
                            })
                          }
                          disabled={savingProjectMetadataId === project.id}
                        >
                          {topic}
                        </button>
                      );
                    })}
                  </div>
                </label>
              </div>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
