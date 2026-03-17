import HelpTip from "./HelpTip";
import { jobDisplayInfo, resolveRunMetrics, runKindLabel } from "../lib/syncJobs";

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

export default function SyncStatusPanel({ run, liveStatus, onOpenLogs }) {
  if (!run) {
    return null;
  }

  const activeStatus = liveStatus && (!run.id || liveStatus.run_id === run.id) ? liveStatus : null;
  const metrics = resolveRunMetrics(run, activeStatus);
  const state = jobDisplayInfo(run, activeStatus);
  const currentLabel = activeStatus?.current_label || run.current_label || "暂无";
  const phaseMessage = activeStatus?.message || run.message || "等待中";
  const heartbeatState = activeStatus || run;
  const totalNote = `本 Job 合计${!metrics.new_events && !metrics.analyzed_events && !metrics.failed_events && metrics.skipped_events ? " · 无新增变化" : ""}`;

  return (
    <section className={`sync-status-panel sync-status-panel--${run.status} ${activeStatus?.is_stalled ? "sync-status-panel--stalled" : ""}`}>
      <div className="sync-status-panel__header">
        <div className="sync-panel-title">
          <h2>当前</h2>
          <HelpTip label="当前说明" text="查看本次运行状态、阶段和指标。" />
        </div>
        <div className="sync-status-panel__actions">
          <button className="secondary-button" type="button" onClick={() => onOpenLogs?.("all")}>
            查看日志
          </button>
          <div className={`pill pill--${state.tone}`}>{state.label}</div>
        </div>
      </div>

      <div className="sync-status-panel__grid">
        <div className="sync-status-metric">
          <span>Job 类型</span>
          <strong>{runKindLabel(run.run_kind)}</strong>
        </div>
        <div className="sync-status-metric">
          <span>当前阶段</span>
          <strong>{phaseMessage}</strong>
        </div>
        <div className="sync-status-metric">
          <span>当前项目</span>
          <strong>{currentLabel}</strong>
        </div>
        <div className="sync-status-metric">
          <span>来源进度</span>
          <strong>{`${metrics.processed_sources || 0} / ${metrics.total_sources || 0}`}</strong>
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
          <strong>{metricValue(metrics.new_events, "0")}</strong>
        </button>
        <button
          className="sync-status-metric sync-status-metric--button"
          type="button"
          onClick={() => onOpenLogs?.("analyzed")}
          aria-label="已分析"
        >
          <span>已分析</span>
          <strong>{metricValue(metrics.analyzed_events, "0")}</strong>
        </button>
        <button
          className="sync-status-metric sync-status-metric--button"
          type="button"
          onClick={() => onOpenLogs?.("failed")}
          aria-label="失败"
        >
          <span>失败数</span>
          <strong>{metricValue(metrics.failed_events, "0")}</strong>
        </button>
        <button
          className="sync-status-metric sync-status-metric--button"
          type="button"
          onClick={() => onOpenLogs?.("skipped")}
          aria-label="跳过"
        >
          <span>跳过</span>
          <strong>{metricValue(metrics.skipped_events, "0")}</strong>
        </button>
      </div>

      <p className="sync-status-panel__note">{totalNote}</p>

      <div className="sync-status-panel__grid sync-status-panel__grid--compact">
        <div className="sync-status-metric">
          <span>心跳状态</span>
          <strong>{heartbeatLabel(heartbeatState)}</strong>
        </div>
        <div className="sync-status-metric">
          <span>最后心跳</span>
          <strong>{formatDate(activeStatus?.last_heartbeat_at || run.last_heartbeat_at)}</strong>
        </div>
        <div className="sync-status-metric">
          <span>开始时间</span>
          <strong>{formatDate(run.started_at)}</strong>
        </div>
        <div className="sync-status-metric">
          <span>结束时间</span>
          <strong>{formatDate(run.finished_at)}</strong>
        </div>
      </div>

      {(activeStatus?.error || run.error) ? <p className="sync-status-panel__error">{activeStatus?.error || run.error}</p> : null}
    </section>
  );
}
