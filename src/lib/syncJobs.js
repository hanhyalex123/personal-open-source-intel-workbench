export function runKindLabel(runKind) {
  if (runKind === "manual-incremental") return "手动增量同步";
  if (runKind === "manual-digest") return "手动日报生成";
  if (runKind === "scheduled-incremental") return "定时增量同步";
  if (runKind === "scheduled-digest") return "定时日报生成";
  if (runKind === "manual") return "手动同步";
  return "未知 Job";
}

export function selectPrimaryJob(runs) {
  if (!Array.isArray(runs) || !runs.length) return null;
  return runs.find((run) => run.status === "running") || runs[0];
}

export function resolveRunMetrics(run, liveStatus) {
  const metrics = run?.metrics || {};
  const statusMatchesRun = liveStatus && (!run?.id || liveStatus.run_id === run.id);
  if (!statusMatchesRun) {
    return {
      total_sources: metrics.total_sources ?? 0,
      processed_sources: metrics.processed_sources ?? 0,
      new_events: metrics.new_events ?? 0,
      analyzed_events: metrics.analyzed_events ?? 0,
      failed_events: metrics.failed_events ?? 0,
      skipped_events: metrics.skipped_events ?? 0,
    };
  }
  return {
    total_sources: liveStatus.total_sources ?? metrics.total_sources ?? 0,
    processed_sources: liveStatus.processed_sources ?? metrics.processed_sources ?? 0,
    new_events: liveStatus.new_events ?? metrics.new_events ?? 0,
    analyzed_events: liveStatus.analyzed_events ?? metrics.analyzed_events ?? 0,
    failed_events: liveStatus.failed_events ?? metrics.failed_events ?? 0,
    skipped_events: liveStatus.skipped_events ?? metrics.skipped_events ?? 0,
  };
}

export function jobDisplayInfo(run, liveStatus) {
  if (!run) {
    return { label: "暂无 Job", tone: "ghost" };
  }

  const statusMatchesRun = liveStatus && (!run?.id || liveStatus.run_id === run.id);
  const status = statusMatchesRun ? liveStatus.status || run.status : run.status;
  const isStalled = Boolean(statusMatchesRun && liveStatus.is_stalled);
  const failedEvents = resolveRunMetrics(run, liveStatus).failed_events;

  if (isStalled) return { label: "可能卡住", tone: "high" };
  if (status === "failed") return { label: "Job 失败", tone: "high" };
  if (status === "success" && failedEvents > 0) return { label: "已完成，含失败项", tone: "medium" };
  if (status === "success") return { label: "已完成", tone: "stable" };
  if (status === "running") return { label: "运行中", tone: "medium" };
  return { label: "等待中", tone: "ghost" };
}
