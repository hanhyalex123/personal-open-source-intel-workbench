import SyncStatusPanel from "./SyncStatusPanel";
import SyncJobList from "./SyncJobList";

export default function SyncMonitorPage({ primaryRun, runs, selectedRunId, liveStatus, onSelectRun, onOpenLogs }) {
  return (
    <section className="sync-monitor-page">
      <div className="sync-monitor-toolbar">
        <button className="secondary-button" type="button" onClick={() => onOpenLogs?.("all")}>
          查看日志
        </button>
      </div>

      <SyncStatusPanel run={primaryRun} liveStatus={liveStatus} onOpenLogs={onOpenLogs} />
      <SyncJobList
        runs={runs}
        selectedRunId={selectedRunId}
        liveStatus={liveStatus}
        onSelectRun={onSelectRun}
      />
    </section>
  );
}
