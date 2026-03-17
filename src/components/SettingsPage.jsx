import { useEffect, useState } from "react";

import { FOCUS_CATEGORIES, FOCUS_TOPIC_OPTIONS } from "../lib/focusTags";
import HelpTip from "./HelpTip";

const CATEGORY_OPTIONS = ["", ...FOCUS_CATEGORIES];

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
  }, [config]);
  const packyEffective = config?.llm?.packy;
  const openaiEffective = config?.llm?.openai;

  async function handleLlmSubmit(event) {
    event.preventDefault();
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
          api_key: llmForm.openai.apiKey,
          provider: llmForm.openai.provider,
          api_url: llmForm.openai.apiUrl,
          model: llmForm.openai.model,
          protocol: llmForm.openai.protocol,
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

  return (
    <section className="settings-page">
      <section className="settings-panel">
        <SettingsSectionHeader title="模型" help="切换主供应商并维护两套模型网关。" />

        <form className="assistant-config-form" onSubmit={handleLlmSubmit}>
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

          <label className="assistant-config-form__toggle">
            <input
              type="checkbox"
              checked={llmForm.disableResponseStorage}
              onChange={(event) => setLlmForm((current) => ({ ...current, disableResponseStorage: event.target.checked }))}
            />
            <span>禁用响应存档</span>
          </label>

          <div className="assistant-config-form__full assistant-config-form__toggle-row">
            <label className="assistant-config-form__toggle">
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
            <label className="assistant-config-form__toggle">
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
            <strong>主通道</strong>
            <span>{llmForm.activeProvider === "packy" ? "Packy" : "OpenAI"}</span>
          </div>

          <div className="llm-provider-grid assistant-config-form__full">
            <section
              className={`llm-provider-card card-tier--focus ${llmForm.activeProvider === "packy" ? "llm-provider-card--active" : ""}`}
            >
              <div className="llm-provider-card__header">
                <div>
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
                  <h3>OpenAI</h3>
                </div>
                <span className="llm-provider-card__badge">{llmForm.activeProvider === "openai" ? "主通道" : "备用"}</span>
              </div>
              <div className="llm-provider-card__status">{llmForm.openai.apiKeyConfigured ? "已配置" : "未配置"}</div>
              <EffectiveConfig data={openaiEffective} />
              <div className="assistant-config-form llm-provider-card__form">
                <label className="assistant-config-form__full">
                  <span>OpenAI API Key</span>
                  <input
                    type="password"
                    aria-label="OpenAI API Key"
                    value={llmForm.openai.apiKey}
                    onChange={(event) =>
                      setLlmForm((current) => ({
                        ...current,
                        openai: { ...current.openai, apiKey: event.target.value },
                      }))
                    }
                    placeholder="留空时沿用 OPENAI_API_KEY"
                  />
                </label>
                <label>
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
                <label>
                  <span>OpenAI API URL</span>
                  <input
                    aria-label="OpenAI API URL"
                    value={llmForm.openai.apiUrl}
                    onChange={(event) =>
                      setLlmForm((current) => ({
                        ...current,
                        openai: { ...current.openai, apiUrl: event.target.value },
                      }))
                    }
                  />
                </label>
                <label>
                  <span>OpenAI 模型</span>
                  <input
                    aria-label="OpenAI 模型"
                    value={llmForm.openai.model}
                    onChange={(event) =>
                      setLlmForm((current) => ({
                        ...current,
                        openai: { ...current.openai, model: event.target.value },
                      }))
                    }
                  />
                </label>
                <label>
                  <span>OpenAI 协议</span>
                  <input
                    aria-label="OpenAI 协议"
                    value={llmForm.openai.protocol}
                    onChange={(event) =>
                      setLlmForm((current) => ({
                        ...current,
                        openai: { ...current.openai, protocol: event.target.value },
                      }))
                    }
                    placeholder="例如 openai-responses"
                  />
                </label>
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

        <form className="assistant-config-form" onSubmit={handleAssistantSubmit}>
          <label className="assistant-config-form__toggle">
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

          <label>
            <span>默认时间范围</span>
            <input
              aria-label="默认时间范围"
              value={assistantForm.defaultTimeframe}
              onChange={(event) => setAssistantForm((current) => ({ ...current, defaultTimeframe: event.target.value }))}
            />
          </label>

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

          <label className="assistant-config-form__toggle">
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

          <label>
            <span>抓取页数</span>
            <input
              type="number"
              aria-label="抓取页数"
              value={assistantForm.liveSearchMaxPages}
              onChange={(event) => setAssistantForm((current) => ({ ...current, liveSearchMaxPages: event.target.value }))}
            />
          </label>

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

          <button className="primary-button" type="submit" disabled={savingConfig}>
            {savingConfig ? "保存中..." : "保存 Assistant 配置"}
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
