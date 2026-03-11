function digestLabel(item) {
  return `${item.project_count} 个项目，${item.high_importance_count} 个高关注`;
}

export default function DailyDigestHistory({ history }) {
  if (!history.length) {
    return <div className="empty-state">历史日报会在每日生成后归档到这里。</div>;
  }

  return (
    <div className="digest-history-list">
      {history.map((item) => (
        <article key={item.date} className="digest-history-card">
          <strong>{item.date}</strong>
          <span>{digestLabel(item)}</span>
        </article>
      ))}
    </div>
  );
}
