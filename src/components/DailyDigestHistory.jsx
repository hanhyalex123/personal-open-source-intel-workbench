function digestLabel(item) {
  return `${item.project_count} 个项目，${item.high_importance_count} 个高关注`;
}

export default function DailyDigestHistory({ history, selectedDate = "", loading = false, onSelectDate }) {
  if (!history.length) {
    return <div className="empty-state">历史日报会在每日生成后归档到这里。</div>;
  }

  return (
    <div className="digest-history-list">
      {history.map((item) => {
        const isActive = item.date === selectedDate;
        return (
          <button
            key={item.date}
            type="button"
            className={`digest-history-button ${isActive ? "digest-history-button--active" : ""}`.trim()}
            aria-label={`查看 ${item.date} 日报`}
            onClick={() => onSelectDate?.(item.date)}
            disabled={loading && isActive}
          >
            <strong>{item.date}</strong>
            <span>{digestLabel(item)}</span>
          </button>
        );
      })}
    </div>
  );
}
