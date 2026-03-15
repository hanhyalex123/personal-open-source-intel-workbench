import { startTransition, useEffect, useMemo, useState } from "react";

import {
  fetchDocsEvents,
  fetchDocsPageDiff,
  fetchDocsPages,
  fetchDocsProject,
  fetchDocsProjects,
} from "../lib/api";

function formatDate(value) {
  if (!value) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function modeLabel(mode) {
  if (mode === "docs_initial_read") return "首读解读";
  if (mode === "docs_diff_update") return "更新 diff";
  return "文档事件";
}

function changeTypeLabel(changeType) {
  if (changeType === "added") return "新增";
  if (changeType === "removed") return "删除";
  return "改写";
}

function formatDiffHighlight(item) {
  if (typeof item === "string") return item;
  if (!item || typeof item !== "object") return "";
  return item.highlight || item.summary || item.title || item.page_id || "";
}

function formatReadingGuideItem(item) {
  if (typeof item === "string") return item;
  if (!item || typeof item !== "object") return "";
  const focus = item.focus || item.target || item.title || "";
  const reason = item.reason || item.why || item.summary || "";
  if (focus && reason) {
    return `${focus}：${reason}`;
  }
  return focus || reason || "";
}

function eventListKey(prefix, item, index) {
  if (typeof item === "string") return `${prefix}-${item}`;
  if (!item || typeof item !== "object") return `${prefix}-${index}`;
  return `${prefix}-${item.page_id || item.step || item.title || item.focus || item.target || item.highlight || index}`;
}

function EventDigestCard({ title, event, emptyText }) {
  return (
    <section className="docs-digest-card">
      <div className="docs-digest-card__header">
        <p className="section-kicker">{title}</p>
        {event?.published_at ? <span>{formatDate(event.published_at)}</span> : null}
      </div>
      {event ? (
        <>
          <h3>{event.title_zh}</h3>
          <p>{event.summary_zh}</p>
          {event.changed_page_count ? <strong>关联页面 {event.changed_page_count} 个</strong> : null}
        </>
      ) : (
        <p>{emptyText}</p>
      )}
    </section>
  );
}

function EventDetails({ event, onSelectPage }) {
  if (!event) {
    return <div className="empty-state">请选择一条文档事件查看解读。</div>;
  }

  return (
    <section className="docs-event-detail">
      <div className="docs-event-detail__header">
        <div>
          <p className="section-kicker">{modeLabel(event.event_kind)}</p>
          <h3>{event.title_zh}</h3>
        </div>
        <div className="docs-event-detail__meta">
          <span>{formatDate(event.published_at)}</span>
          <span className={`pill pill--${event.urgency || "low"}`}>{event.urgency || "low"}</span>
        </div>
      </div>

      <p className="docs-event-detail__summary">{event.summary_zh}</p>

      {event.doc_summary ? (
        <section className="docs-copy-block">
          <h4>文档概览</h4>
          <p>{event.doc_summary}</p>
        </section>
      ) : null}

      {(event.doc_key_points || []).length ? (
        <section className="docs-copy-block">
          <h4>关键点</h4>
          <ul>
            {event.doc_key_points.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {(event.diff_highlights || []).length ? (
        <section className="docs-copy-block">
          <h4>Diff 解读</h4>
          <ul>
            {event.diff_highlights.map((item, index) => (
              <li key={eventListKey("highlight", item, index)}>{formatDiffHighlight(item)}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {(event.reading_guide || []).length ? (
        <section className="docs-copy-block">
          <h4>阅读建议</h4>
          <ol>
            {event.reading_guide.map((item, index) => (
              <li key={eventListKey("guide", item, index)}>{formatReadingGuideItem(item)}</li>
            ))}
          </ol>
        </section>
      ) : null}

      {(event.changed_pages || []).length ? (
        <section className="docs-copy-block">
          <h4>关联页面</h4>
          <div className="docs-linked-pages">
            {event.changed_pages.map((page) => (
              <button key={`${event.id}-${page.page_id || page.url}`} type="button" onClick={() => onSelectPage(page.page_id)}>
                <strong>{page.title_after || page.title || page.url}</strong>
                <span>{changeTypeLabel(page.change_type || "changed")}</span>
              </button>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}

function PageDiffPanel({ detail, loading }) {
  if (loading) {
    return <div className="empty-state">正在读取页面 diff...</div>;
  }

  if (!detail?.page) {
    return <div className="empty-state">选择页面后，这里会展示最新 diff 和阅读上下文。</div>;
  }

  const diff = detail.latest_diff;

  return (
    <section className="docs-page-diff">
      <div className="docs-page-diff__header">
        <div>
          <p className="section-kicker">Page Diff</p>
          <h3>{detail.page.title}</h3>
        </div>
        <div className="docs-page-diff__meta">
          <span>{detail.page.category || "未分类"}</span>
          <span>{detail.page.extractor_hint}</span>
        </div>
      </div>

      <p>{detail.page.summary}</p>

      {diff ? (
        <div className="docs-page-diff__columns">
          <section className="docs-copy-block">
            <h4>新增内容</h4>
            <ul>
              {(diff.added_blocks || []).length ? (
                diff.added_blocks.map((item) => <li key={item}>{item}</li>)
              ) : (
                <li>暂无新增段落摘要。</li>
              )}
            </ul>
          </section>
          <section className="docs-copy-block">
            <h4>移除内容</h4>
            <ul>
              {(diff.removed_blocks || []).length ? (
                diff.removed_blocks.map((item) => <li key={item}>{item}</li>)
              ) : (
                <li>暂无移除段落摘要。</li>
              )}
            </ul>
          </section>
        </div>
      ) : (
        <div className="empty-state">这个页面目前还没有可展示的 diff 记录。</div>
      )}
    </section>
  );
}

export default function DocsWorkbenchPage({ initialProjectId = "", highlightedEventId = "", onSelectProject }) {
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(initialProjectId);
  const [detail, setDetail] = useState(null);
  const [events, setEvents] = useState([]);
  const [pages, setPages] = useState([]);
  const [pageDiff, setPageDiff] = useState(null);
  const [mode, setMode] = useState("");
  const [activeEventId, setActiveEventId] = useState(highlightedEventId);
  const [selectedPageId, setSelectedPageId] = useState("");
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingDiff, setLoadingDiff] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialProjectId) {
      setSelectedProjectId(initialProjectId);
    }
    if (highlightedEventId) {
      setActiveEventId(highlightedEventId);
    }
  }, [initialProjectId, highlightedEventId]);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    async function loadProjects() {
      setLoadingProjects(true);
      try {
        const payload = await fetchDocsProjects(controller.signal);
        if (!active) return;
        startTransition(() => {
          setProjects(payload);
          setSelectedProjectId((current) => current || initialProjectId || payload[0]?.project_id || "");
          setError("");
        });
      } catch (loadError) {
        if (loadError.name !== "AbortError" && active) {
          setError(loadError instanceof Error ? loadError.message : "文档项目读取失败");
        }
      } finally {
        if (active) {
          setLoadingProjects(false);
        }
      }
    }

    loadProjects();
    return () => {
      active = false;
      controller.abort();
    };
  }, [initialProjectId]);

  useEffect(() => {
    if (!selectedProjectId) {
      return undefined;
    }

    onSelectProject?.(selectedProjectId);
    let active = true;
    const controller = new AbortController();

    async function loadProject() {
      setLoadingDetail(true);
      try {
        const [detailPayload, eventsPayload, pagesPayload] = await Promise.all([
          fetchDocsProject(selectedProjectId, controller.signal),
          fetchDocsEvents(selectedProjectId, mode, controller.signal),
          fetchDocsPages(selectedProjectId, controller.signal),
        ]);
        if (!active) return;
        const preferredEventId =
          highlightedEventId && eventsPayload.some((item) => item.id === highlightedEventId)
            ? highlightedEventId
            : eventsPayload[0]?.id || "";
        const preferredEvent = eventsPayload.find((item) => item.id === preferredEventId);
        const preferredPageId =
          preferredEvent?.changed_pages?.[0]?.page_id || pagesPayload.find((item) => item.is_recently_changed)?.id || pagesPayload[0]?.id || "";
        startTransition(() => {
          setDetail(detailPayload);
          setEvents(eventsPayload);
          setPages(pagesPayload);
          setActiveEventId(preferredEventId);
          setSelectedPageId(preferredPageId);
          setError("");
        });
      } catch (loadError) {
        if (loadError.name !== "AbortError" && active) {
          setError(loadError instanceof Error ? loadError.message : "文档详情读取失败");
        }
      } finally {
        if (active) {
          setLoadingDetail(false);
        }
      }
    }

    loadProject();
    return () => {
      active = false;
      controller.abort();
    };
  }, [selectedProjectId, mode, highlightedEventId, onSelectProject]);

  useEffect(() => {
    if (!selectedProjectId || !selectedPageId) {
      setPageDiff(null);
      return undefined;
    }

    let active = true;
    const controller = new AbortController();

    async function loadPageDiff() {
      setLoadingDiff(true);
      try {
        const payload = await fetchDocsPageDiff(selectedProjectId, selectedPageId, controller.signal);
        if (!active) return;
        startTransition(() => {
          setPageDiff(payload);
          setError("");
        });
      } catch (loadError) {
        if (loadError.name !== "AbortError" && active) {
          setError(loadError instanceof Error ? loadError.message : "页面 diff 读取失败");
        }
      } finally {
        if (active) {
          setLoadingDiff(false);
        }
      }
    }

    loadPageDiff();
    return () => {
      active = false;
      controller.abort();
    };
  }, [selectedProjectId, selectedPageId]);

  const activeEvent = useMemo(() => events.find((item) => item.id === activeEventId) || events[0] || null, [events, activeEventId]);

  return (
    <section className="docs-workbench-page">
      <div className="docs-workbench-intro">
        <div>
          <p className="section-kicker">Docs Radar</p>
          <h2>文档解读</h2>
          <p>针对 Furo / Sphinx 风格文档保留首读结论、更新 diff 和单页变化脉络。</p>
        </div>
        <div className="docs-mode-toggle">
          {[
            { id: "", label: "全部" },
            { id: "docs_initial_read", label: "首读" },
            { id: "docs_diff_update", label: "更新 diff" },
          ].map((option) => (
            <button
              key={option.id || "all"}
              type="button"
              className={`monitor-filter-pill ${mode === option.id ? "monitor-filter-pill--active" : ""}`}
              onClick={() => setMode(option.id)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {loadingProjects ? <div className="empty-state">正在读取文档项目...</div> : null}

      {!loadingProjects && !projects.length ? <div className="empty-state">当前还没有接入文档源的项目。</div> : null}

      {!loadingProjects && projects.length ? (
        <div className="docs-workbench-layout">
          <aside className="docs-project-rail">
            <div className="docs-project-rail__inner">
              <p className="section-kicker">Projects</p>
              <h3>文档项目</h3>
              <div className="docs-project-rail__list">
                {projects.map((project) => (
                  <button
                    key={project.project_id}
                    type="button"
                    className={`docs-project-rail__item ${selectedProjectId === project.project_id ? "docs-project-rail__item--active" : ""}`}
                    onClick={() => setSelectedProjectId(project.project_id)}
                  >
                    <strong>{project.project_name}</strong>
                    <span>{project.page_count} 页</span>
                  </button>
                ))}
              </div>
            </div>
          </aside>

          <div className="docs-workbench-main">
            {loadingDetail ? <div className="empty-state">正在读取文档详情...</div> : null}

            {!loadingDetail && detail ? (
              <>
                <div className="docs-digest-grid">
                  <EventDigestCard title="首次完整解读" event={detail.initial_read} emptyText="该项目还没有完成首读。"/>
                  <EventDigestCard title="最近更新 diff" event={detail.latest_update} emptyText="最近还没有新的文档 diff。"/>
                </div>

                <section className="docs-stat-strip">
                  <div>
                    <span>总页面数</span>
                    <strong>{detail.page_stats?.total_pages ?? 0}</strong>
                  </div>
                  <div>
                    <span>最近变更页</span>
                    <strong>{detail.page_stats?.changed_pages ?? 0}</strong>
                  </div>
                  <div>
                    <span>最近同步</span>
                    <strong>{formatDate(detail.last_synced_at)}</strong>
                  </div>
                </section>

                <div className="docs-analysis-grid">
                  <section className="docs-events-panel">
                    <div className="docs-events-panel__header">
                      <div>
                        <p className="section-kicker">Event Stream</p>
                        <h3>文档事件流</h3>
                      </div>
                      <span>{events.length} 条</span>
                    </div>
                    <div className="docs-events-list">
                      {events.map((event) => (
                        <button
                          key={event.id}
                          type="button"
                          className={`docs-events-list__item ${activeEvent?.id === event.id ? "docs-events-list__item--active" : ""}`}
                          onClick={() => {
                            setActiveEventId(event.id);
                            if (event.changed_pages?.[0]?.page_id) {
                              setSelectedPageId(event.changed_pages[0].page_id);
                            }
                          }}
                        >
                          <div>
                            <strong>{event.title_zh}</strong>
                            <p>{event.summary_zh}</p>
                          </div>
                          <span>{modeLabel(event.event_kind)}</span>
                        </button>
                      ))}
                    </div>
                  </section>

                  <EventDetails
                    event={activeEvent}
                    onSelectPage={(pageId) => {
                      if (pageId) {
                        setSelectedPageId(pageId);
                      }
                    }}
                  />
                </div>

                <div className="docs-analysis-grid">
                  <section className="docs-pages-panel">
                    <div className="docs-events-panel__header">
                      <div>
                        <p className="section-kicker">Pages</p>
                        <h3>当前页面快照</h3>
                      </div>
                      <span>{pages.length} 页</span>
                    </div>
                    <div className="docs-pages-list">
                      {pages.map((page) => (
                        <button
                          key={page.id}
                          type="button"
                          className={`docs-pages-list__item ${selectedPageId === page.id ? "docs-pages-list__item--active" : ""}`}
                          onClick={() => setSelectedPageId(page.id)}
                        >
                          <div>
                            <strong>{page.title}</strong>
                            <p>{page.summary}</p>
                          </div>
                          <span>{page.latest_change ? changeTypeLabel(page.latest_change.change_type) : "稳定"}</span>
                        </button>
                      ))}
                    </div>
                  </section>

                  <PageDiffPanel detail={pageDiff} loading={loadingDiff} />
                </div>
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}
