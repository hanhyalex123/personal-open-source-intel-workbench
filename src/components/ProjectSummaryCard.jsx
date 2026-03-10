import { projectThemeStyle } from "../lib/projectTheme";

function formatDate(value) {
  if (!value) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function importanceLabel(level) {
  if (level === "high") return "高关注";
  if (level === "medium") return "持续关注";
  return "低波动";
}

export default function ProjectSummaryCard({ item }) {
  return (
    <article
      className="project-summary-card"
      data-project-id={item.project_id}
      style={projectThemeStyle(item.project_id)}
    >
      <header className="project-summary-card__header">
        <div>
          <p className="section-kicker">Project Intel</p>
          <h2>{item.project_name}</h2>
        </div>
        <div className={`pill pill--${item.importance || "low"}`}>{importanceLabel(item.importance)}</div>
      </header>

      <div className="project-summary-card__body">
        <h3>{item.headline}</h3>
        <p className="project-summary-card__summary">{item.summary_zh}</p>
        <p className="project-summary-card__reason">{item.reason}</p>
      </div>

      <section className="project-summary-card__evidence">
        <div className="project-summary-card__section-head">
          <h4>关键依据</h4>
          <span>{formatDate(item.updated_at)}</span>
        </div>
        <div className="project-summary-card__evidence-list">
          {(item.evidence_items || []).map((evidence) => (
            <article key={evidence.id} className="project-evidence-row">
              <div className="project-evidence-row__meta">
                <span className={`pill pill--${evidence.urgency || "low"}`}>{evidence.category || evidence.version || evidence.source}</span>
              </div>
              <div className="project-evidence-row__copy">
                <strong>{evidence.title_zh}</strong>
                <p>{evidence.summary_zh}</p>
              </div>
              {evidence.url ? (
                <a href={evidence.url} target="_blank" rel="noreferrer" className="insight-link">
                  来源
                </a>
              ) : null}
            </article>
          ))}
        </div>
      </section>
    </article>
  );
}
