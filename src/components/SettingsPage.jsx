import { useEffect, useState } from "react";

import { FOCUS_CATEGORIES, FOCUS_TOPIC_OPTIONS } from "../lib/focusTags";

const CATEGORY_OPTIONS = ["", ...FOCUS_CATEGORIES];

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
      apiKey: "",
      provider: "",
      apiUrl: "",
      model: "",
      protocol: "",
      apiKeyConfigured: false,
    },
    openai: {
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
        apiKey: config?.llm?.packy?.api_key || "",
        provider: config?.llm?.packy?.provider || "",
        apiUrl: config?.llm?.packy?.api_url || "",
        model: config?.llm?.packy?.model || "",
        protocol: config?.llm?.packy?.protocol || "",
        apiKeyConfigured: config?.llm?.packy?.api_key_configured ?? false,
      },
      openai: {
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

  async function handleLlmSubmit(event) {
    event.preventDefault();
    await onConfigSave({
      llm: {
        active_provider: llmForm.activeProvider,
        reasoning_effort: llmForm.reasoningEffort,
        disable_response_storage: llmForm.disableResponseStorage,
        packy: {
          api_key: llmForm.packy.apiKey,
          provider: llmForm.packy.provider,
          api_url: llmForm.packy.apiUrl,
          model: llmForm.packy.model,
          protocol: llmForm.packy.protocol,
        },
        openai: {
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
        <div className="settings-panel__header">
          <div>
            <p className="section-kicker">AI Capability</p>
            <h2>AI 能力管理</h2>
          </div>
          <p className="settings-panel__copy">切换当前主供应商，并维护 Packy / OpenAI 两套网关参数。未显式保存主供应商时，服务端会自动选择已配置好 API key 的通道；字段留空时继续沿用容器环境变量。</p>
        </div>

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

          <div className="settings-inline-note assistant-config-form__full">
            <strong>{llmForm.activeProvider === "packy" ? "Packy" : "OpenAI"} 当前作为主通道。</strong>
            <span>未选中的另一套配置会作为备用通道参与 fallback；是否真正生效仍取决于服务端是否已配置对应 API key。</span>
          </div>

          <div className="llm-provider-grid assistant-config-form__full">
            <section className={`llm-provider-card ${llmForm.activeProvider === "packy" ? "llm-provider-card--active" : ""}`}>
              <div className="llm-provider-card__header">
                <div>
                  <p className="section-kicker">Provider A</p>
                  <h3>Packy</h3>
                </div>
                <span className="llm-provider-card__badge">{llmForm.activeProvider === "packy" ? "主通道" : "备用"}</span>
              </div>
              <p className="llm-provider-card__copy">{llmForm.packy.apiKeyConfigured ? "Packy API key 已就绪，可直接作为主通道或备用通道。" : "Packy API key 尚未配置；留空时会继续尝试读取服务端环境变量。"}</p>
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

            <section className={`llm-provider-card ${llmForm.activeProvider === "openai" ? "llm-provider-card--active" : ""}`}>
              <div className="llm-provider-card__header">
                <div>
                  <p className="section-kicker">Provider B</p>
                  <h3>OpenAI</h3>
                </div>
                <span className="llm-provider-card__badge">{llmForm.activeProvider === "openai" ? "主通道" : "备用"}</span>
              </div>
              <p className="llm-provider-card__copy">{llmForm.openai.apiKeyConfigured ? "OpenAI API key 已就绪，可直接切换为主通道。" : "OpenAI API key 尚未配置；留空时会继续尝试读取服务端 OPENAI_API_KEY。"}</p>
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
        <div className="settings-panel__header">
          <div>
            <p className="section-kicker">Assistant</p>
            <h2>Assistant 全局配置</h2>
          </div>
          <p className="settings-panel__copy">所有 AI 控制台 查询都先走这份本地配置，再进入 assistant 检索和组织回答。</p>
        </div>

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
          <div>
            <p className="section-kicker">Config Center</p>
            <h2>配置中心</h2>
          </div>
          <p className="project-admin__copy">新增项目时只填 GitHub URL 和官方文档 URL，后端会接管后续分析链路。</p>
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
