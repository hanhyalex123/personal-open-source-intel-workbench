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
  const [assistantForm, setAssistantForm] = useState({
    enabled: true,
    defaultMode: "hybrid",
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
    setAssistantForm({
      enabled: config?.assistant?.enabled ?? true,
      defaultMode: config?.assistant?.default_mode || "hybrid",
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

  async function handleAssistantSubmit(event) {
    event.preventDefault();
    await onConfigSave({
      assistant: {
        enabled: assistantForm.enabled,
        default_mode: assistantForm.defaultMode,
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
            <span>默认模式</span>
            <select
              aria-label="默认模式"
              value={assistantForm.defaultMode}
              onChange={(event) => setAssistantForm((current) => ({ ...current, defaultMode: event.target.value }))}
            >
              <option value="local">local</option>
              <option value="hybrid">hybrid</option>
              <option value="live">live</option>
            </select>
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
