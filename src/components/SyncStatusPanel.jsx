function formatDate(value) {
  if (!value) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function heartbeatLabel(status) {
  if (status?.is_stalled) return "心跳超时";
  if (status?.status === "running") return "运行中";
  if (status?.status === "failed") return "已失败";
  if (status?.status === "success") return "已完成";
  return "等待中";
}

function statusLabel(status) {
  if (status === "running") return "同步中";
  if (status === "failed") return "同步失败";
  if (status === "success") return "同步完成";
  return "空闲";
}

function metricValue(value, fallback = "暂无") {
  if (value === 0) return "0";
  if (!value) return fallback;
  return value;
}

export default function SyncStatusPanel({ status, onOpenLogs }) {
  if (!status || status.status === "idle") {
    return null;
  }

  const summary = status.last_incremental_metrics || null;
  const summaryNew = summary ? summary.new_events : status.new_events;
  const summaryAnalyzed = summary ? summary.analyzed_events : status.analyzed_events;
  const summaryFailed = summary ? summary.failed_events : status.failed_events;
  const skippedEvents = summary ? summary.skipped_events ?? 0 : status.skipped_events ?? 0;
  const totalNote = `本次合计（全来源）${!summaryNew && !summaryAnalyzed && !summaryFailed && skippedEvents ? " · 无新增变化" : ""}`;
  const stateText = status.is_stalled ? "可能卡住" : statusLabel(status.status);
  const pillTone = status.is_stalled ? "high" : status.status === "failed" ? "high" : status.status === "success" ? "stable" : "medium";

  return (
    <section className={`sync-status-panel sync-status-panel--${status.status} ${status.is_stalled ? "sync-status-panel--stalled" : ""}`}>
      <div className="sync-status-panel__header">
        <div>
          <div className="section-kicker section-kicker--icon">
            <span className="cover-icon" aria-hidden="true">◉</span>
            <span>Signal Radar</span>
          </div>
          <h2>同步雷达</h2>
        </div>
        <div className="sync-status-panel__actions">
          <button className="secondary-button" type="button" onClick={() => onOpenLogs?.("all")}>
            查看日志
          </button>
          <div className={`pill pill--${pillTone}`}>{stateText}</div>
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
      </div>

      <div className="sync-status-panel__grid sync-status-panel__grid--compact">
        <button
          className="sync-status-metric sync-status-metric--button"
          type="button"
          onClick={() => onOpenLogs?.("new")}
          aria-label="新增"
        >
          <span>新增事件</span>
          <strong>{metricValue(summaryNew, "0")}</strong>
        </button>
        <button
          className="sync-status-metric sync-status-metric--button"
          type="button"
          onClick={() => onOpenLogs?.("analyzed")}
          aria-label="已分析"
        >
          <span>已分析</span>
          <strong>{metricValue(summaryAnalyzed, "0")}</strong>
        </button>
        <button
          className="sync-status-metric sync-status-metric--button"
          type="button"
          onClick={() => onOpenLogs?.("failed")}
          aria-label="失败"
        >
          <span>失败数</span>
          <strong>{metricValue(summaryFailed, "0")}</strong>
        </button>
        <button
          className="sync-status-metric sync-status-metric--button"
          type="button"
          onClick={() => onOpenLogs?.("skipped")}
          aria-label="跳过"
        >
          <span>跳过</span>
          <strong>{metricValue(skippedEvents, "0")}</strong>
        </button>
      </div>

      <p className="sync-status-panel__note">{totalNote.replace("本次合计（全来源）", "本次合计（最近一次增量）")}</p>

      <div className="sync-status-panel__grid sync-status-panel__grid--compact">
        <div className="sync-status-metric">
          <span>心跳状态</span>
          <strong>{heartbeatLabel(status)}</strong>
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
