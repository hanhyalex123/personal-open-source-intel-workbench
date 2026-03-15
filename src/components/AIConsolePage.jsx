import { useEffect, useState } from "react";
import SimpleMarkdown from "./SimpleMarkdown";

const CATEGORY_OPTIONS = ["", "网络", "存储", "调度", "架构", "安全", "升级", "运行时", "可观测性"];

function formatDate(value) {
  if (!value) return "未知";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function relationLabel(value) {
  if (value === "primary_project") return "直接命中目标项目";
  if (value === "supports_primary_project") return "支撑目标项目判断";
  return "一般相关";
}

export default function AIConsolePage({ projects, assistantConfig, onQuery }) {
  const [query, setQuery] = useState("");
  const [projectId, setProjectId] = useState("");
  const [category, setCategory] = useState("");
  const [timeframe, setTimeframe] = useState("14d");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setProjectId(assistantConfig?.default_project_ids?.[0] || "");
    setCategory(assistantConfig?.default_categories?.[0] || "");
    setTimeframe(assistantConfig?.default_timeframe || "14d");
  }, [assistantConfig]);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = await onQuery({
        query,
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
          <p className="section-kicker">Live Research Assistant</p>
          <h2>AI 控制台</h2>
          <p>围绕公网信息做研究型问答。默认先规划问题，再抓取网页证据，最后输出 Markdown 研究报告。</p>
        </div>

        <form className="assistant-form" onSubmit={handleSubmit}>
          <label className="assistant-field">
            <span>问题输入</span>
            <textarea
              aria-label="问题输入"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="例如：openclaw最近更新了几次，主要方向是什么"
              rows={4}
            />
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
            {loading ? "研究中..." : "发起查询"}
          </button>
        </form>

        {!assistantConfig?.enabled ? <div className="error-banner">Assistant 当前被禁用，请先在配置中心开启。</div> : null}
        {error ? <div className="error-banner">{error}</div> : null}
      </section>

      <section className="assistant-response-panel">
        {!result ? (
          <div className="assistant-empty">
            <h3>等待提问</h3>
            <p>先输入问题，再让助手规划检索、抓取证据并输出研究报告。</p>
          </div>
        ) : (
          <div className="assistant-response">
            <section className="assistant-answer assistant-answer--report">
              <p className="section-kicker">Research Report</p>
              <h3>回答</h3>
              <div className="assistant-markdown">
                <SimpleMarkdown content={result.report_markdown} />
              </div>
            </section>

            <section className="assistant-result-block">
              <h3>研究计划</h3>
              <div className="assistant-plan-grid">
                <p>检索模式: {result.applied_filters?.mode || "live"}</p>
                <p>主项目: {(result.applied_plan?.primary_entities || []).join(" / ") || "未识别"}</p>
                <p>相关项目: {(result.applied_plan?.related_entities || []).join(" / ") || "无"}</p>
                <p>意图: {result.applied_plan?.intent || "general_research"}</p>
              </div>
            </section>

            <section className="assistant-result-block">
              <h3>关键依据</h3>
              <div className="assistant-evidence-list">
                {(result.evidence || []).map((item) => (
                  <article key={item.id} className="assistant-evidence-card">
                    <strong>{item.title}</strong>
                    <p>{item.summary}</p>
                    <span>{item.project_name} / {item.source}</span>
                    <span>发布时间 {formatDate(item.published_at)}</span>
                    <span>关联: {relationLabel(item.relation_to_query)}</span>
                  </article>
                ))}
              </div>
            </section>

            <section className="assistant-result-block">
              <h3>建议下一步</h3>
              <ul className="assistant-bullet-list">
                {(result.next_steps || []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>

            <section className="assistant-result-block">
              <h3>实时来源</h3>
              <div className="assistant-evidence-list">
                {(result.sources || []).map((item) => (
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

            <section className="assistant-result-block">
              <h3>检索链路</h3>
              <div className="assistant-evidence-list">
                {(result.search_trace || []).map((item) => (
                  <article key={`${item.query}-${item.url}`} className="assistant-evidence-card">
                    <strong>{item.query}</strong>
                    <span>{item.fetch_mode} / {item.matched_entity || "unmatched"}</span>
                    <a href={item.url} target="_blank" rel="noreferrer">
                      查看原文
                    </a>
                  </article>
                ))}
              </div>
            </section>
          </div>
        )}
      </section>
    </section>
  );
}
