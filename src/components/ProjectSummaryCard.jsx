import { postReadEvent } from "../lib/api";
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

function hasChineseText(value) {
  if (typeof value !== "string") return false;
  const text = value.trim();
  if (!text) return false;
  return /[\u3400-\u9fff\uf900-\ufaff]/.test(text);
}

function fallbackEvidenceTitle(projectName, source) {
  if (source === "docs_feed") return `${projectName} 文档更新`;
  if (source === "github_release") return `${projectName} 版本更新`;
  return `${projectName} 项目更新`;
}

function resolveReadEventId(item) {
  return item?.evidence_items?.[0]?.id || item?.evidence_ids?.[0] || item?.id || "";
}

export default function ProjectSummaryCard({ item }) {
  const projectName = item.project_name || "项目";
  const headline = hasChineseText(item.headline) ? item.headline : `${projectName} 今日重点`;
  const summary = hasChineseText(item.summary_zh)
    ? item.summary_zh
    : "今天检测到新的项目变化，建议查看最新中文解读。";
  const reason = hasChineseText(item.reason)
    ? item.reason
    : "当前证据的中文摘要不足，已回退为中文提示。";
  const handleReadEvent = () => {
    if (!item?.project_id) return;
    const eventId = resolveReadEventId(item);
    if (!eventId) return;
    postReadEvent({ project_id: item.project_id, event_id: eventId }).catch(() => {});
  };
  return (
    <article
      className="project-summary-card"
      data-project-id={item.project_id}
      style={projectThemeStyle(item.project_id)}
      onClick={handleReadEvent}
    >
      <header className="project-summary-card__header">
        <div>
          <p className="section-kicker">Project Intel</p>
          <h2>{item.project_name}</h2>
        </div>
        <div className={`pill pill--${item.importance || "low"}`}>{importanceLabel(item.importance)}</div>
      </header>

      <div className="project-summary-card__body">
        <h3>{headline}</h3>
        <p className="project-summary-card__summary">{summary}</p>
        <p className="project-summary-card__reason">{reason}</p>
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
                <strong>
                  {hasChineseText(evidence.title_zh)
                    ? evidence.title_zh
                    : fallbackEvidenceTitle(projectName, evidence.source)}
                </strong>
                <p>
                  {hasChineseText(evidence.summary_zh)
                    ? evidence.summary_zh
                    : "该条证据的中文解读暂不可用，建议进入详情查看页面变化。"}
                </p>
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
