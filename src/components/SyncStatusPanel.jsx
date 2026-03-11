function formatDate(value) {
  if (!value) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function statusLabel(status) {
  if (status === "running") return "同步中";
  if (status === "failed") return "同步失败";
  if (status === "success") return "同步完成";
  return "空闲";
}

export default function SyncStatusPanel({ status }) {
  if (!status || status.status === "idle") {
    return null;
  }

  return (
    <section className={`sync-status-panel sync-status-panel--${status.status}`}>
      <div className="sync-status-panel__header">
        <div>
          <p className="section-kicker">Sync</p>
          <h2>同步状态</h2>
        </div>
        <div className={`pill pill--${status.status === "failed" ? "high" : status.status === "success" ? "stable" : "medium"}`}>
          {statusLabel(status.status)}
        </div>
      </div>

      <div className="sync-status-panel__grid">
        <div className="sync-status-metric">
          <span>当前阶段</span>
          <strong>{status.message || "等待中"}</strong>
        </div>
        <div className="sync-status-metric">
          <span>当前项目</span>
          <strong>{status.current_label || "暂无"}</strong>
        </div>
        <div className="sync-status-metric">
          <span>来源进度</span>
          <strong>{`${status.processed_sources || 0} / ${status.total_sources || 0}`}</strong>
        </div>
        <div className="sync-status-metric">
          <span>新增事件</span>
          <strong>{status.new_events || 0}</strong>
        </div>
        <div className="sync-status-metric">
          <span>已分析</span>
          <strong>{status.analyzed_events || 0}</strong>
        </div>
        <div className="sync-status-metric">
          <span>最后心跳</span>
          <strong>{formatDate(status.last_heartbeat_at)}</strong>
        </div>
      </div>

      {status.error ? <p className="sync-status-panel__error">{status.error}</p> : null}
    </section>
  );
}
