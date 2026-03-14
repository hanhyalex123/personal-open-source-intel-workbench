import SyncStatusPanel from "./SyncStatusPanel";

export default function SyncMonitorPage({ status, onOpenLogs }) {
  return (
    <section className="sync-monitor-page">
      <div className="sync-monitor-intro sync-monitor-intro--cover">
        <div className="sync-monitor-intro__copy">
          <div className="section-kicker section-kicker--icon">
            <span className="cover-icon" aria-hidden="true">◉</span>
            <span>Signal Room</span>
          </div>
          <h2>同步监控</h2>
          <p>同步状态、来源进度与日志入口集中在这里，方便快速判断是否要下钻日志。</p>
        </div>
        <div className="sync-monitor-intro__meta">
          <div className="sync-monitor-intro__meta-card">
            <span className="cover-icon" aria-hidden="true">◎</span>
            <div>
              <strong>状态面板</strong>
              <p>看阶段、项目、来源进度</p>
            </div>
          </div>
          <div className="sync-monitor-intro__meta-card">
            <span className="cover-icon" aria-hidden="true">▣</span>
            <div>
              <strong>日志入口</strong>
              <p>点指标直接看新增、分析、失败、跳过</p>
            </div>
          </div>
        </div>
        <div className="sync-monitor-intro__action">
          <div className="sync-monitor-intro__action-label">Signal Radar</div>
          <button className="secondary-button" type="button" onClick={() => onOpenLogs?.("all")}>
            查看日志
          </button>
        </div>
      </div>

      <SyncStatusPanel status={status} onOpenLogs={onOpenLogs} />
    </section>
  );
}
