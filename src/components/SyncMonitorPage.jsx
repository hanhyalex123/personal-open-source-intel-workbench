import SyncStatusPanel from "./SyncStatusPanel";

export default function SyncMonitorPage({ status, onOpenLogs }) {
  return (
    <section className="sync-monitor-page">
      <div className="sync-monitor-intro">
        <div>
          <p className="section-kicker">Radar</p>
          <h2>同步监控</h2>
          <p>同步状态、来源进度与日志入口集中在这里。</p>
        </div>
        <button className="secondary-button" type="button" onClick={() => onOpenLogs?.("all")}>
          查看日志
        </button>
      </div>

      <SyncStatusPanel status={status} onOpenLogs={onOpenLogs} />
    </section>
  );
}
