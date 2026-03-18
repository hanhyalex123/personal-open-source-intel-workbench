import { useEffect, useMemo, useRef, useState } from "react";

import { clearSyncRuns, fetchSyncRun, fetchSyncRuns } from "../lib/api";
import { runKindLabel } from "../lib/syncJobs";

const FILTERS = [
  { id: "all", label: "全部" },
  { id: "new", label: "新增" },
  { id: "analyzed", label: "已分析" },
  { id: "failed", label: "失败" },
  { id: "skipped", label: "跳过" },
];

function formatDate(value) {
  if (!value) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function statusLabel(status) {
  if (status === "running") return "运行中";
  if (status === "failed") return "失败";
  if (status === "success") return "完成";
  return "空闲";
}

function eventStatusLabel(event) {
  if (event.status === "failed") return "失败";
  if (event.status === "analyzed") return "已分析";
  if (event.status === "skipped") return "跳过";
  return "新增";
}

function eventMatchesFilter(event, filter) {
  if (filter === "new") return event.is_new;
  if (filter === "analyzed") return event.status === "analyzed";
  if (filter === "failed") return event.status === "failed";
  if (filter === "skipped") return event.status === "skipped";
  return true;
}

export default function SyncLogDrawer({ open, onClose, currentRunId, initialFilter = "all" }) {
  const [activeTab, setActiveTab] = useState("current");
  const [filter, setFilter] = useState(initialFilter);
  const [runs, setRuns] = useState([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [runsError, setRunsError] = useState("");
  const [historyRunId, setHistoryRunId] = useState(null);
  const [runDetail, setRunDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [selectedSourceLabel, setSelectedSourceLabel] = useState("");
  const detailRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    setActiveTab("current");
    setFilter(initialFilter || "all");
  }, [open, initialFilter]);

  useEffect(() => {
    setSelectedEvent(null);
    setSelectedSourceLabel("");
  }, [runDetail?.id]);

  useEffect(() => {
    if (!open) return;
    let active = true;
    setRunsLoading(true);
    setRunsError("");
    fetchSyncRuns(undefined, 20)
      .then((payload) => {
        if (!active) return;
        setRuns(payload);
      })
      .catch((error) => {
        if (!active) return;
        setRunsError(error instanceof Error ? error.message : "同步日志读取失败");
      })
      .finally(() => {
        if (!active) return;
        setRunsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [open]);

  useEffect(() => {
    if (!open || activeTab !== "history") return;
    if (!historyRunId && runs.length) {
      setHistoryRunId(runs[0].id);
    }
  }, [open, activeTab, historyRunId, runs]);

  const fallbackRunId = currentRunId || runs[0]?.id || null;
  const activeRunId = activeTab === "history" ? historyRunId || fallbackRunId : fallbackRunId;

  useEffect(() => {
    if (!open) return;
    if (!activeRunId) {
      setRunDetail(null);
      return;
    }
    let active = true;
    setDetailLoading(true);
    setDetailError("");
    fetchSyncRun(activeRunId)
      .then((payload) => {
        if (!active) return;
        setRunDetail(payload);
      })
      .catch((error) => {
        if (!active) return;
        setDetailError(error instanceof Error ? error.message : "同步日志读取失败");
      })
      .finally(() => {
        if (!active) return;
        setDetailLoading(false);
      });
    return () => {
      active = false;
    };
  }, [open, activeRunId]);

  const filteredSources = useMemo(() => {
    if (!runDetail?.sources) return [];
    return runDetail.sources.map((source) => {
      const events = source.events || [];
      const filteredEvents = events.filter((event) => eventMatchesFilter(event, filter));
      return { ...source, filteredEvents };
    });
  }, [runDetail, filter]);

  function handleSelectEvent(event, sourceLabel) {
    setSelectedEvent(event);
    setSelectedSourceLabel(sourceLabel);
    if (detailRef.current?.scrollIntoView) {
      detailRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  const selectedSummary = selectedEvent?.analysis?.summary_zh || selectedEvent?.analysis?.summary || "";
  const selectedActions = selectedEvent?.analysis?.action_items || [];
  const selectedEventId = selectedEvent?.event_id;

  async function handleClear() {
    try {
      setRunsLoading(true);
      await clearSyncRuns();
      setRuns([]);
      setRunDetail(null);
      setHistoryRunId(null);
    } catch (error) {
      setRunsError(error instanceof Error ? error.message : "清空同步日志失败");
    } finally {
      setRunsLoading(false);
    }
  }

  if (!open) return null;

  return (
    <div className="sync-log-drawer" role="dialog" aria-modal="true" aria-label="同步日志">
      <button className="sync-log-overlay" type="button" onClick={onClose} aria-label="关闭日志" />
      <section className="sync-log-panel">
        <header className="sync-log-panel__header">
          <div>
            <p className="section-kicker">Radar Logs</p>
            <h2>同步日志</h2>
          </div>
          <div className="sync-log-panel__actions">
            <button className="secondary-button" type="button" onClick={handleClear} disabled={runsLoading}>
              清空日志
            </button>
            <button className="sync-log-panel__close" type="button" onClick={onClose} aria-label="关闭">
              关闭
            </button>
          </div>
        </header>

        <div className="sync-log-panel__tabs" role="tablist" aria-label="同步日志视图">
          <button
            className={`sync-log-tab ${activeTab === "current" ? "sync-log-tab--active" : ""}`}
            type="button"
            role="tab"
            aria-selected={activeTab === "current"}
            onClick={() => setActiveTab("current")}
          >
            本次同步
          </button>
          <button
            className={`sync-log-tab ${activeTab === "history" ? "sync-log-tab--active" : ""}`}
            type="button"
            role="tab"
            aria-selected={activeTab === "history"}
            onClick={() => setActiveTab("history")}
          >
            历史同步
          </button>
        </div>

        <div className="sync-log-panel__body">
          {runsLoading ? <p className="sync-log-panel__hint">正在读取同步日志...</p> : null}
          {runsError ? <p className="sync-log-panel__error">{runsError}</p> : null}

          {!runsLoading && !runs.length ? <div className="sync-log-panel__empty">暂无同步日志</div> : null}

          {activeTab === "history" && runs.length ? (
            <div className="sync-log-history">
              {runs.map((run) => (
                <button
                  key={run.id}
                  type="button"
                  className={`sync-log-history__item ${run.id === (historyRunId || fallbackRunId) ? "is-active" : ""}`}
                  onClick={() => setHistoryRunId(run.id)}
                >
                  <div>
                    <strong>{formatDate(run.started_at)}</strong>
                    <span>{runKindLabel(run.run_kind)}</span>
                  </div>
                  <span className={`pill pill--${run.status === "failed" ? "high" : "stable"}`}>{statusLabel(run.status)}</span>
                </button>
              ))}
            </div>
          ) : null}

          {detailLoading ? <p className="sync-log-panel__hint">正在加载同步详情...</p> : null}
          {detailError ? <p className="sync-log-panel__error">{detailError}</p> : null}

          {runDetail ? (
            <section className="sync-log-summary">
              <div>
                <span>运行类型</span>
                <strong>{runKindLabel(runDetail.run_kind)}</strong>
              </div>
              <div>
                <span>状态</span>
                <strong>{statusLabel(runDetail.status)}</strong>
              </div>
              <div>
                <span>开始时间</span>
                <strong>{formatDate(runDetail.started_at)}</strong>
              </div>
              <div>
                <span>结束时间</span>
                <strong>{formatDate(runDetail.finished_at)}</strong>
              </div>
              <div>
                <span>来源</span>
                <strong>{`${runDetail.metrics?.processed_sources ?? 0} / ${runDetail.metrics?.total_sources ?? 0}`}</strong>
              </div>
              <div>
                <span>新增</span>
                <strong>{runDetail.metrics?.new_events ?? 0}</strong>
              </div>
              <div>
                <span>已分析</span>
                <strong>{runDetail.metrics?.analyzed_events ?? 0}</strong>
              </div>
              <div>
                <span>失败</span>
                <strong>{runDetail.metrics?.failed_events ?? 0}</strong>
              </div>
              <div>
                <span>跳过</span>
                <strong>{runDetail.metrics?.skipped_events ?? 0}</strong>
              </div>
            </section>
          ) : null}

          {runDetail ? (
            <section className="sync-log-filter">
              {FILTERS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`sync-log-filter__item ${filter === item.id ? "is-active" : ""}`}
                  onClick={() => setFilter(item.id)}
                >
                  {item.label}
                </button>
              ))}
            </section>
          ) : null}

          {runDetail ? (
            <section
              ref={detailRef}
              className="sync-log-detail card-tier--focus"
              data-testid="sync-log-detail"
            >
              <div className="sync-log-detail__header">
                <h3>观测详情</h3>
                {selectedEvent ? (
                  <button className="sync-log-detail__clear" type="button" onClick={() => setSelectedEvent(null)}>
                    清除
                  </button>
                ) : null}
              </div>
              {!selectedEvent ? (
                <p className="sync-log-panel__hint">点击任意事件的“查看详情”进行观测。</p>
              ) : (
                <div className="sync-log-detail__body">
                  <div className="sync-log-detail__row">
                    <span>标题</span>
                    <strong>{selectedEvent.title || selectedEvent.event_id}</strong>
                  </div>
                  <div className="sync-log-detail__row">
                    <span>状态</span>
                    <strong>{eventStatusLabel(selectedEvent)}</strong>
                  </div>
                  <div className="sync-log-detail__row">
                    <span>版本</span>
                    <strong>{selectedEvent.version || "暂无"}</strong>
                  </div>
                  <div className="sync-log-detail__row">
                    <span>时间</span>
                    <strong>{selectedEvent.published_at ? formatDate(selectedEvent.published_at) : "暂无"}</strong>
                  </div>
                  <div className="sync-log-detail__row">
                    <span>来源</span>
                    <strong>{selectedSourceLabel || "未知"}</strong>
                  </div>
                  {selectedEvent.url ? (
                    <div className="sync-log-detail__row">
                      <span>链接</span>
                      <a href={selectedEvent.url} target="_blank" rel="noreferrer">
                        查看原文
                      </a>
                    </div>
                  ) : null}
                  <div className="sync-log-detail__row">
                    <span>模型</span>
                    <strong>{selectedEvent.model || "未知"}</strong>
                  </div>
                  <div className="sync-log-detail__row">
                    <span>提供商</span>
                    <strong>{selectedEvent.provider || "未知"}</strong>
                  </div>
                  {selectedEvent.used_fallback ? (
                    <div className="sync-log-detail__row">
                      <span>备用模型</span>
                      <strong>{selectedEvent.fallback_model || "未知"}</strong>
                    </div>
                  ) : null}
                  {selectedSummary ? (
                    <div className="sync-log-detail__row sync-log-detail__row--stack">
                      <span>结论摘要</span>
                      <p>{selectedSummary}</p>
                    </div>
                  ) : null}
                  {selectedActions.length ? (
                    <div className="sync-log-detail__row sync-log-detail__row--stack">
                      <span>建议动作</span>
                      <ul>
                        {selectedActions.map((action, index) => (
                          <li key={`${action}-${index}`}>{action}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {selectedEvent.error ? (
                    <div className="sync-log-detail__row sync-log-detail__row--stack">
                      <span>错误</span>
                      <p className="sync-log-detail__error">{selectedEvent.error}</p>
                    </div>
                  ) : null}
                  <details className="sync-log-detail__raw">
                    <summary>原始 JSON</summary>
                    <pre>{JSON.stringify(selectedEvent, null, 2)}</pre>
                  </details>
                </div>
              )}
            </section>
          ) : null}

          {runDetail ? (
            <section className="sync-log-sources">
              {filteredSources.map((source) => (
                <div key={`${source.kind}-${source.label}`} className="sync-log-source">
                  <div className="sync-log-source__header">
                    <div>
                      <strong>{source.label}</strong>
                      <span>{source.kind === "docs" ? "文档来源" : "GitHub Releases"}</span>
                    </div>
                    <span className={`pill pill--${source.status === "failed" ? "high" : "stable"}`}>
                      {statusLabel(source.status)}
                    </span>
                  </div>
                  <div className="sync-log-source__meta">
                    <span>新增 {source.metrics?.new_events ?? 0}</span>
                    <span>已分析 {source.metrics?.analyzed_events ?? 0}</span>
                    <span>失败 {source.metrics?.failed_events ?? 0}</span>
                    <span>跳过 {source.metrics?.skipped_events ?? 0}</span>
                  </div>
                  {source.error ? <p className="sync-log-source__error">{source.error}</p> : null}
                  <div className="sync-log-events">
                    {(source.filteredEvents || []).map((event) => {
                      const isSelected = selectedEventId && selectedEventId === event.event_id;
                      return (
                        <div key={event.event_id} className={`sync-log-event ${isSelected ? "is-active" : ""}`}>
                        <div className="sync-log-event__meta">
                          <span className={`pill pill--${event.status === "failed" ? "high" : "low"}`}>
                            {eventStatusLabel(event)}
                          </span>
                          {event.version ? <span>{event.version}</span> : null}
                          {event.published_at ? <span>{formatDate(event.published_at)}</span> : null}
                          <button
                            className="sync-log-event__detail"
                            type="button"
                            onClick={() => handleSelectEvent(event, source.label)}
                          >
                            查看详情
                          </button>
                        </div>
                        <div className="sync-log-event__copy">
                          <strong>{event.title}</strong>
                          {event.model || event.provider ? (
                            <p>{`模型: ${event.model || "未知"}${event.provider ? ` · ${event.provider}` : ""}${event.route_alias ? ` · ${event.route_alias}` : ""}`}</p>
                          ) : null}
                          {event.used_fallback ? <p>{`备用模型: ${event.fallback_model || "未知"}${event.fallback_route_alias ? ` · ${event.fallback_route_alias}` : ""}`}</p> : null}
                          {event.analysis?.summary_zh ? <p>{event.analysis.summary_zh}</p> : null}
                          {event.error ? <p>{event.error}</p> : null}
                        </div>
                      </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </section>
          ) : null}
        </div>
      </section>
    </div>
  );
}
