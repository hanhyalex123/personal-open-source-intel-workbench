import { startTransition, useEffect, useMemo, useState } from "react";

import {
  fetchDocsEvents,
  fetchDocsPageDiff,
  fetchDocsPages,
  fetchDocsProject,
  fetchDocsProjects,
} from "../lib/api";
import HelpTip from "./HelpTip";

function formatDate(value) {
  if (!value) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function modeLabel(mode) {
  if (mode === "docs_initial_read") return "首读";
  if (mode === "docs_diff_update") return "更新";
  return "变更";
}

function changeTypeLabel(changeType) {
  if (changeType === "added") return "新增";
  if (changeType === "removed") return "删除";
  if (changeType === "changed") return "改写";
  return "稳定";
}

function urgencyWeight(value) {
  if (value === "high") return 3;
  if (value === "medium") return 2;
  if (value === "low") return 1;
  return 0;
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

function isEmptyAnalysisPlaceholder(value) {
  return (value || "").trim() === "模型返回空响应，未能生成结构化分析。";
}

function hasChineseText(value) {
  if (typeof value !== "string") return false;
  const text = value.trim();
  if (!text || isEmptyAnalysisPlaceholder(text)) return false;
  return /[\u3400-\u9fff\uf900-\ufaff]/.test(text);
}

function readableText(...values) {
  for (const value of values) {
    if (typeof value !== "string") continue;
    const text = value.trim();
    if (!text || isEmptyAnalysisPlaceholder(text) || !hasChineseText(text)) continue;
    return text;
  }
  return "";
}

function sortPages(pages, events) {
  const eventByPageId = new Map();
  for (const event of events) {
    for (const page of event.changed_pages || []) {
      if (!page?.page_id || eventByPageId.has(page.page_id)) continue;
      eventByPageId.set(page.page_id, event);
    }
  }

  return [...pages].sort((left, right) => {
    const leftEvent = eventByPageId.get(left.id);
    const rightEvent = eventByPageId.get(right.id);

    const recentDelta = Number(Boolean(right.is_recently_changed)) - Number(Boolean(left.is_recently_changed));
    if (recentDelta !== 0) return recentDelta;

    const urgencyDelta = urgencyWeight(rightEvent?.urgency) - urgencyWeight(leftEvent?.urgency);
    if (urgencyDelta !== 0) return urgencyDelta;

    const rightPublished = new Date(rightEvent?.published_at || 0).getTime();
    const leftPublished = new Date(leftEvent?.published_at || 0).getTime();
    if (rightPublished !== leftPublished) return rightPublished - leftPublished;

    return left.title.localeCompare(right.title, "zh-CN");
  });
}

function buildDeepResearchPrompt(projectName, pageTitle, pageSummary, relatedEvent, pageDiff) {
  const added = (pageDiff?.latest_diff?.added_blocks || []).join("；") || "暂无新增摘要";
  const removed = (pageDiff?.latest_diff?.removed_blocks || []).join("；") || "暂无删除摘要";
  const eventTitle = relatedEvent?.title_zh || "无关联事件";
  return `请基于 ${projectName} 项目的文档页面 ${pageTitle} 做深入研究。页面摘要：${pageSummary || "暂无摘要"}。关联事件：${eventTitle}。新增：${added}。删除：${removed}。请给出背景、影响、风险和后续建议。`;
}

function ReadingSection({ title, children }) {
  return (
    <section className="docs-copy-block">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

export default function DocsWorkbenchPage({
  initialProjectId = "",
  highlightedEventId = "",
  onSelectProject,
  onStartResearch,
}) {
  const [projects, setProjects] = useState([]);
  const [detail, setDetail] = useState(null);
  const [events, setEvents] = useState([]);
  const [pages, setPages] = useState([]);
  const [pageDiff, setPageDiff] = useState(null);
  const [mode, setMode] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState(initialProjectId);
  const [selectedPageId, setSelectedPageId] = useState("");
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingDiff, setLoadingDiff] = useState(false);
  const [deepReadOpen, setDeepReadOpen] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialProjectId) {
      setSelectedProjectId(initialProjectId);
    }
  }, [initialProjectId]);

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

        const sortedPages = sortPages(pagesPayload, eventsPayload);
        const highlightedPageId = highlightedEventId
          ? eventsPayload.find((event) => event.id === highlightedEventId)?.changed_pages?.[0]?.page_id
          : "";

        const preferredPageId =
          highlightedPageId ||
          sortedPages.find((page) => page.is_recently_changed)?.id ||
          detailPayload.latest_update?.changed_pages?.[0]?.page_id ||
          detailPayload.initial_read?.changed_pages?.[0]?.page_id ||
          sortedPages[0]?.id ||
          "";

        startTransition(() => {
          setDetail(detailPayload);
          setEvents(eventsPayload);
          setPages(sortedPages);
          setSelectedPageId(preferredPageId);
          setDeepReadOpen(false);
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

  useEffect(() => {
    setDeepReadOpen(false);
  }, [selectedPageId]);

  const selectedPage = useMemo(() => pages.find((page) => page.id === selectedPageId) || pageDiff?.page || pages[0] || null, [pages, pageDiff, selectedPageId]);

  const relatedEvents = useMemo(
    () => events.filter((event) => (event.changed_pages || []).some((page) => page.page_id === selectedPage?.id)),
    [events, selectedPage?.id],
  );

  const primaryEvent = relatedEvents[0] || null;
  const addedBlocks = pageDiff?.latest_diff?.added_blocks || [];
  const removedBlocks = pageDiff?.latest_diff?.removed_blocks || [];
  const diffHighlights = (primaryEvent?.diff_highlights || [])
    .map(formatDiffHighlight)
    .filter((item) => hasChineseText(item));
  const readingGuide = (primaryEvent?.reading_guide || [])
    .map(formatReadingGuideItem)
    .filter((item) => hasChineseText(item));
  const keyPoints = (primaryEvent?.doc_key_points || []).filter((item) => hasChineseText(item));
  const sourceLine = `来源：${formatDate(primaryEvent?.published_at || detail?.last_synced_at)}${primaryEvent ? ` / ${primaryEvent.id}` : ""}`;

  function handleResearch() {
    if (!selectedPage) return;
    onStartResearch?.({
      projectId: selectedProjectId,
      projectName: detail?.project_name || projects.find((item) => item.project_id === selectedProjectId)?.project_name || "",
      query: buildDeepResearchPrompt(
        detail?.project_name || projects.find((item) => item.project_id === selectedProjectId)?.project_name || "",
        selectedPage.title,
        selectedPage.summary,
        primaryEvent,
        pageDiff,
      ),
    });
  }

  return (
    <section className="docs-workbench-page">
      <div className="docs-workbench-intro">
        <div className="settings-panel__title">
          <h2>页面</h2>
          <HelpTip label="页面说明" text="先看最近哪页变了，再看详细解读和深读。" />
        </div>
        <div className="docs-mode-toggle">
          {[
            { id: "", label: "全部" },
            { id: "docs_initial_read", label: "首读" },
            { id: "docs_diff_update", label: "更新" },
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
      {!loadingProjects && !projects.length ? <div className="empty-state">当前没有接入文档项目。</div> : null}

      {!loadingProjects && projects.length ? (
        <div className="docs-workbench-layout">
          <aside className="docs-project-rail">
            <section className="docs-project-rail__inner">
              <h2>项目</h2>
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
            </section>
          </aside>

          <div className="docs-workbench-main">
            {loadingDetail ? <div className="empty-state">正在读取文档详情...</div> : null}

            {!loadingDetail && detail ? (
              <div className="docs-reading-layout">
                <section className="docs-pages-panel">
                  <div className="docs-panel-header">
                    <h2>页面</h2>
                    <span>{pages.length} 页</span>
                  </div>
                  <div className="docs-pages-list">
                    {pages.map((page) => {
                      const event = events.find((item) => (item.changed_pages || []).some((changedPage) => changedPage.page_id === page.id));
                      const teaser = readableText(event?.doc_summary, event?.summary_zh, page.summary) || "先看页面摘要与 diff。";
                      const time = event?.published_at || detail.last_synced_at;
                      return (
                        <button
                          key={page.id}
                          type="button"
                          className={`docs-pages-list__item ${selectedPageId === page.id ? "docs-pages-list__item--active" : ""}`}
                          onClick={() => setSelectedPageId(page.id)}
                        >
                          <div>
                            <strong>{page.title}</strong>
                          <p>{teaser}</p>
                          </div>
                          <div className="docs-pages-list__meta">
                            <span>{modeLabel(event?.event_kind)}</span>
                            <span>{changeTypeLabel(page.latest_change?.change_type)}</span>
                            <span>{formatDate(time)}</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </section>

                <section className="docs-reading-panel">
                  <div className="docs-panel-header">
                    <h2>解读</h2>
                    {selectedPage ? <span>{selectedPage.title}</span> : null}
                  </div>

                  {selectedPage ? (
                    <>
                      <section className="docs-reading-hero">
                        <div>
                          <p className="section-kicker">{changeTypeLabel(selectedPage.latest_change?.change_type)}</p>
                          <h3>{selectedPage.title}</h3>
                        </div>
                        <div className="docs-page-diff__meta">
                          <span>{selectedPage.category || "未分类"}</span>
                          <span>{selectedPage.extractor_hint || "docs"}</span>
                        </div>
                      </section>

                      <div className="docs-reading-grid">
                        <ReadingSection title="变化">
                          <p>
                            {readableText(
                              diffHighlights[0],
                              primaryEvent?.doc_summary,
                              primaryEvent?.summary_zh,
                              selectedPage.summary,
                            ) || "先看页面摘要与 diff。"}
                          </p>
                        </ReadingSection>

                        <ReadingSection title="影响">
                          <p>{readableText(keyPoints[0], selectedPage.summary) || "这页暂无额外影响说明。"}</p>
                        </ReadingSection>

                        <ReadingSection title="建议">
                          {readingGuide.length ? (
                            <ul>
                              {readingGuide.slice(0, deepReadOpen ? readingGuide.length : 1).map((item) => (
                                <li key={item}>{item}</li>
                              ))}
                            </ul>
                          ) : (
                            <p>{readableText(primaryEvent?.summary_zh) || "先看这页 diff，再决定是否继续深读。"}</p>
                          )}
                        </ReadingSection>

                        <ReadingSection title="Diff">
                          {loadingDiff ? (
                            <p>正在读取页面 diff...</p>
                          ) : (
                            <div className="docs-page-diff__columns">
                              <div>
                                <strong>新增</strong>
                                <ul>
                                  {addedBlocks.length ? addedBlocks.map((item) => <li key={item}>{item}</li>) : <li>这页暂无 diff 记录。</li>}
                                </ul>
                              </div>
                              <div>
                                <strong>删除</strong>
                                <ul>
                                  {removedBlocks.length ? removedBlocks.map((item) => <li key={item}>{item}</li>) : <li>这页暂无删除摘要。</li>}
                                </ul>
                              </div>
                            </div>
                          )}
                        </ReadingSection>
                      </div>

                      <ReadingSection title="关联">
                        <div className="docs-related-meta">
                          <p>{sourceLine}</p>
                          {primaryEvent ? (
                            <p>{readableText(primaryEvent.title_zh) || "关联事件暂无中文标题。"}</p>
                          ) : (
                            <p>当前页面暂无关联事件，直接使用页面摘要和 diff。</p>
                          )}
                        </div>
                      </ReadingSection>

                      {deepReadOpen ? (
                        <ReadingSection title="深读">
                          <div className="docs-deep-read">
                            <p>{readableText(primaryEvent?.doc_summary, selectedPage.summary) || "先看页面摘要与 diff。"}</p>
                            {readingGuide.length > 1 ? (
                              <ul>
                                {readingGuide.slice(1).map((item) => (
                                  <li key={item}>{item}</li>
                                ))}
                              </ul>
                            ) : null}
                            {diffHighlights.length > 1 ? (
                              <ul>
                                {diffHighlights.slice(1).map((item) => (
                                  <li key={item}>{item}</li>
                                ))}
                              </ul>
                            ) : null}
                          </div>
                        </ReadingSection>
                      ) : null}

                      <div className="docs-reading-actions">
                        <button type="button" className="secondary-button" onClick={() => setDeepReadOpen((current) => !current)}>
                          深读
                        </button>
                        <button type="button" className="primary-button" onClick={handleResearch}>
                          去研究
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="empty-state">选择页面后，这里会展示详细解读。</div>
                  )}
                </section>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}
