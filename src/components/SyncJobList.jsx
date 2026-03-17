import HelpTip from "./HelpTip";
import { jobDisplayInfo, resolveRunMetrics, runKindLabel } from "../lib/syncJobs";

function formatDate(value) {
  if (!value) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function SyncJobList({ runs, selectedRunId, liveStatus, onSelectRun }) {
  if (!runs?.length) {
    return null;
  }

  return (
      <section className="sync-job-list">
      <div className="sync-job-list__header">
        <div className="sync-panel-title">
          <h2>历史</h2>
          <HelpTip label="历史说明" text="回看最近几次 Job。" />
        </div>
      </div>

      <div className="sync-job-list__items">
        {runs.map((run) => {
          const state = jobDisplayInfo(run, liveStatus);
          const metrics = resolveRunMetrics(run, liveStatus);

          return (
            <button
              key={run.id}
              className={`sync-job-list__item ${run.id === selectedRunId ? "is-active" : ""}`}
              type="button"
              onClick={() => onSelectRun?.(run.id)}
            >
              <div className="sync-job-list__headline">
                <div>
                  <strong>{runKindLabel(run.run_kind)}</strong>
                  <p>{run.message || "暂无说明"}</p>
                </div>
                <span className={`pill pill--${state.tone}`}>{state.label}</span>
              </div>
              <div className="sync-job-list__meta">
                <span>{formatDate(run.started_at)}</span>
                <span>{`来源 ${metrics.processed_sources ?? 0} / ${metrics.total_sources ?? 0}`}</span>
                <span>{`失败 ${metrics.failed_events ?? 0}`}</span>
                <span>{`跳过 ${metrics.skipped_events ?? 0}`}</span>
              </div>
              <div className="sync-job-list__actions">
                <span>{run.id}</span>
                <span className="sync-job-list__link">选择后查看日志</span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
