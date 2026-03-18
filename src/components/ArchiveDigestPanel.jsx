import ProjectSummaryCard from "./ProjectSummaryCard";

export default function ArchiveDigestPanel({ digestDate, payload, loading, error }) {
  if (!digestDate) {
    return null;
  }

  return (
    <section className="archive-digest-panel">
      <header className="archive-digest-panel__header">
        <div>
          <h2>归档详情</h2>
          <p>{digestDate}</p>
        </div>
      </header>

      {loading ? <div className="empty-state">正在读取这一天的日报...</div> : null}
      {!loading && error ? <div className="empty-state">{error}</div> : null}
      {!loading && !error && !(payload?.summaries || []).length ? (
        <div className="empty-state">这一天还没有可展示的日报摘要。</div>
      ) : null}

      {!loading && !error && (payload?.summaries || []).length ? (
        <div className="archive-digest-panel__grid">
          {payload.summaries.map((item) => (
            <ProjectSummaryCard key={item.id || `${digestDate}:${item.project_id}`} item={item} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
