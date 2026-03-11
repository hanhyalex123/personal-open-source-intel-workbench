function formatDate(value) {
  if (!value) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function urgencyLabel(level) {
  if (level === "high") return "高优先级";
  if (level === "medium") return "持续关注";
  return "一般更新";
}

export default function IncrementalUpdateList({ updates }) {
  if (!updates.length) {
    return <div className="empty-state">日报生成后还没有新的项目变化。</div>;
  }

  return (
    <div className="incremental-update-list">
      {updates.map((project) => (
        <article key={project.project_id} className="incremental-project-card">
          <header className="incremental-project-card__header">
            <div>
              <p className="section-kicker">Project Update</p>
              <h3>{project.project_name}</h3>
            </div>
            <div className={`pill pill--${project.highest_urgency || "low"}`}>{urgencyLabel(project.highest_urgency)}</div>
          </header>
          <p className="incremental-project-card__timestamp">最近变化：{formatDate(project.latest_published_at)}</p>
          <div className="incremental-project-card__items">
            {project.items.map((item) => (
              <article key={item.id} className="incremental-update-row">
                <div className="incremental-update-row__meta">
                  <span className={`pill pill--${item.urgency || "low"}`}>{item.version || item.category || item.source}</span>
                </div>
                <div className="incremental-update-row__copy">
                  <strong>{item.title_zh}</strong>
                  <p>{item.summary_zh}</p>
                </div>
                {item.url ? (
                  <a href={item.url} target="_blank" rel="noreferrer" className="insight-link">
                    来源
                  </a>
                ) : null}
              </article>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}
