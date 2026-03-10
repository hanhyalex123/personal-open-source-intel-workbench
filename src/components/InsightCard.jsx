import { useState } from "react";

function urgencyLabel(level) {
  if (level === "high") return "高优先级";
  if (level === "medium") return "中优先级";
  return "低优先级";
}

export default function InsightCard({ item, compact = false }) {
  const [expanded, setExpanded] = useState(false);
  const showExpanded = !compact || expanded;
  const previewTitle = item.detail_sections?.[0]?.title || "核心变化点";
  const previewBullets = item.detail_sections?.[0]?.bullets?.slice(0, 1) || [];
  const visibleTags = compact && !expanded ? (item.tags || []).slice(0, 4) : item.tags || [];
  const hiddenTagCount = compact && !expanded ? Math.max((item.tags || []).length - visibleTags.length, 0) : 0;

  return (
    <article className={`insight-card ${compact ? "insight-card--compact" : ""}`}>
      <div className="insight-card__meta">
        <span className={`pill pill--${item.urgency || "low"}`}>{urgencyLabel(item.urgency)}</span>
        {item.is_stable ? <span className="pill pill--stable">固定结论</span> : null}
        {item.version ? <span className="pill pill--ghost">{item.version}</span> : null}
      </div>

      <h3 className="insight-card__title">{item.title_zh}</h3>
      <p className="insight-card__summary">{item.summary_zh}</p>

      {compact && !expanded && previewBullets.length > 0 ? (
        <section className="insight-preview">
          <h4>{previewTitle}</h4>
          <ul>
            {previewBullets.map((bullet) => (
              <li key={bullet} title={bullet}>
                {bullet}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {showExpanded ? (
        <div className="insight-blocks">
          {(item.detail_sections || []).map((section) => (
            <section key={section.title} className="insight-block">
              <h4>{section.title}</h4>
              <ul>
                {(section.bullets || []).map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
            </section>
          ))}

          {item.impact_points?.length ? (
            <section className="insight-block">
              <h4>影响范围</h4>
              <ul>
                {item.impact_points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </section>
          ) : null}

          {item.action_items?.length ? (
            <section className="insight-block">
              <h4>建议动作</h4>
              <ol>
                {item.action_items.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ol>
            </section>
          ) : null}
        </div>
      ) : null}

      <div className="insight-card__footer">
        <div className="insight-tags">
          {visibleTags.map((tag) => (
            <span key={tag} className="insight-tag">
              {tag}
            </span>
          ))}
          {hiddenTagCount > 0 ? <span className="insight-tag insight-tag--more">+{hiddenTagCount}</span> : null}
        </div>
        <div className="insight-card__actions">
          {compact ? (
            <button className="inline-link" type="button" onClick={() => setExpanded((current) => !current)}>
              {expanded ? "收起详情" : "查看详情"}
            </button>
          ) : null}
          {item.url ? (
            <a href={item.url} target="_blank" rel="noreferrer" className="insight-link">
              查看来源
            </a>
          ) : null}
        </div>
      </div>
    </article>
  );
}
