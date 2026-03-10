import { useEffect, useState } from "react";

const CATEGORY_OPTIONS = ["", "网络", "存储", "调度", "架构", "安全", "升级", "运行时", "可观测性"];
const MODE_OPTIONS = [
  { value: "local", label: "local" },
  { value: "hybrid", label: "hybrid" },
  { value: "live", label: "live" },
];

export default function AIConsolePage({ projects, assistantConfig, onQuery }) {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("hybrid");
  const [projectId, setProjectId] = useState("");
  const [category, setCategory] = useState("");
  const [timeframe, setTimeframe] = useState("14d");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setMode(assistantConfig?.default_mode || "hybrid");
    setProjectId(assistantConfig?.default_project_ids?.[0] || "");
    setCategory(assistantConfig?.default_categories?.[0] || "");
    setTimeframe(assistantConfig?.default_timeframe || "14d");
  }, [assistantConfig]);

  const localSources = (result?.sources || []).filter((item) => item.source !== "web_search");
  const liveSources = (result?.sources || []).filter((item) => item.source === "web_search");

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = await onQuery({
        query,
        mode,
        project_ids: projectId ? [projectId] : [],
        categories: category ? [category] : [],
        timeframe,
      });
      setResult(payload);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "查询失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="assistant-page">
      <section className="assistant-query-panel">
        <div className="assistant-page__hero">
          <p className="section-kicker">Project Knowledge Assistant</p>
          <h2>AI 控制台</h2>
          <p>支持 local / hybrid / live 三种模式。默认先查本地知识，必要时补实时网页搜索，再组织成结构化答案。</p>
        </div>

        <form className="assistant-form" onSubmit={handleSubmit}>
          <label className="assistant-field">
            <span>问题输入</span>
            <textarea
              aria-label="问题输入"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="例如：OpenClaw 最近网络相关有什么变化？"
              rows={4}
            />
          </label>

          <label className="assistant-field">
            <span>问答模式</span>
            <select aria-label="问答模式" value={mode} onChange={(event) => setMode(event.target.value)}>
              {MODE_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="assistant-field">
            <span>项目筛选</span>
            <select aria-label="项目筛选" value={projectId} onChange={(event) => setProjectId(event.target.value)}>
              <option value="">全部项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>

          <label className="assistant-field">
            <span>技术分类</span>
            <select aria-label="技术分类" value={category} onChange={(event) => setCategory(event.target.value)}>
              {CATEGORY_OPTIONS.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || "全部分类"}
                </option>
              ))}
            </select>
          </label>

          <label className="assistant-field">
            <span>时间范围</span>
            <input aria-label="时间范围" value={timeframe} onChange={(event) => setTimeframe(event.target.value)} />
          </label>

          <button className="primary-button" type="submit" disabled={loading || !query.trim() || !assistantConfig?.enabled}>
            {loading ? "查询中..." : "发起查询"}
          </button>
        </form>

        {!assistantConfig?.enabled ? <div className="error-banner">Assistant 当前被禁用，请先在配置中心开启。</div> : null}
        {error ? <div className="error-banner">{error}</div> : null}
      </section>

      <section className="assistant-response-panel">
        {!result ? (
          <div className="assistant-empty">
            <h3>等待提问</h3>
            <p>先输入问题，再结合项目、分类和时间范围触发本地 assistant 检索。</p>
          </div>
        ) : (
          <div className="assistant-response">
            <section className="assistant-answer">
              <p className="section-kicker">Answer</p>
              <h3>回答</h3>
              <p>{result.answer}</p>
            </section>

            <section className="assistant-result-block">
              <h3>检索模式</h3>
              <p>{result.applied_filters?.mode || mode}</p>
            </section>

            <section className="assistant-result-block">
              <h3>关键依据</h3>
              <div className="assistant-evidence-list">
                {result.evidence.map((item) => (
                  <article key={item.id} className="assistant-evidence-card">
                    <strong>{item.title}</strong>
                    <p>{item.summary}</p>
                    <span>
                      {item.project_name} / {item.source}
                    </span>
                  </article>
                ))}
              </div>
            </section>

            <section className="assistant-result-block">
              <h3>建议下一步</h3>
              <ul className="assistant-bullet-list">
                {result.next_steps.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>

            <section className="assistant-result-block">
              <h3>来源</h3>
              <div className="assistant-evidence-list">
                {localSources.map((item) => (
                  <article key={item.url} className="assistant-evidence-card">
                    <strong>{item.title}</strong>
                    <span>{item.project_name} / {item.source}</span>
                    <a href={item.url} target="_blank" rel="noreferrer">
                      查看原文
                    </a>
                  </article>
                ))}
              </div>
            </section>

            {liveSources.length ? (
              <section className="assistant-result-block">
                <h3>实时来源</h3>
                <div className="assistant-evidence-list">
                  {liveSources.map((item) => (
                    <article key={item.url} className="assistant-evidence-card">
                      <strong>{item.title}</strong>
                      <span>{item.source}</span>
                      <a href={item.url} target="_blank" rel="noreferrer">
                        查看原文
                      </a>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}
          </div>
        )}
      </section>
    </section>
  );
}
