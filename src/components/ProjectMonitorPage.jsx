import { useEffect, useMemo, useState } from "react";

import InsightCard from "./InsightCard";
import { projectThemeStyle } from "../lib/projectTheme";
import { FOCUS_CATEGORIES, FOCUS_TOPIC_OPTIONS } from "../lib/focusTags";

function sectionId(...parts) {
  return parts
    .filter(Boolean)
    .join("-")
    .replace(/[^a-zA-Z0-9-_]/g, "-")
    .replace(/-+/g, "-")
    .toLowerCase();
}

function CollapsibleItemGrid({ title, items, sectionAnchorId }) {
  const [expanded, setExpanded] = useState(false);
  const visibleItems = expanded ? items : items.slice(0, 3);
  const hasMore = items.length > 3;

  return (
    <section className="project-subsection" id={sectionAnchorId}>
      <div className="project-subsection__header">
        <h3>{title}</h3>
        {hasMore ? (
          <button className="secondary-button" type="button" onClick={() => setExpanded((current) => !current)}>
            {expanded ? "收起" : "展开更多"}
          </button>
        ) : null}
      </div>
      <div className="project-card-grid">
        {visibleItems.map((item) => (
          <InsightCard key={item.id} item={item} compact />
        ))}
      </div>
    </section>
  );
}

function ProjectPanel({ project }) {
  const releaseId = sectionId("project", project.id, "release");
  const docsId = sectionId("project", project.id, "docs");

  return (
    <section
      className="project-panel"
      id={sectionId("project", project.id)}
      data-project-id={project.id}
      style={projectThemeStyle(project.id)}
    >
      <header className="project-panel__header">
        <div>
          <p className="section-kicker">Project</p>
          <h2>{project.name}</h2>
          <p className="project-panel__copy">单项目下钻视图，保留版本区和文档区的操作上下文。</p>
        </div>
        <div className="project-panel__links">
          <a href={project.github_url} target="_blank" rel="noreferrer">
            GitHub
          </a>
          {project.docs_url ? (
            <a href={project.docs_url} target="_blank" rel="noreferrer">
              Docs
            </a>
          ) : null}
        </div>
      </header>

      {project.release_area?.enabled ? (
        <CollapsibleItemGrid title="ReleaseNote 区" items={project.release_area.items || []} sectionAnchorId={releaseId} />
      ) : null}

      {project.docs_area?.enabled ? (
        <section className="project-subsection" id={docsId}>
          <div className="project-subsection__header">
            <h3>文档区</h3>
          </div>
          <div className="docs-category-stack">
            {(project.docs_area.categories || []).map((category) => (
              <section
                key={category.category}
                className="docs-category"
                id={sectionId("project", project.id, "docs", category.category)}
              >
                <CollapsibleItemGrid title={category.category} items={category.items} />
              </section>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}

function FilterBar({ categoryOptions, topicOptions, selectedCategory, selectedTopic, onCategoryChange, onTopicChange }) {
  return (
    <section className="monitor-filter-bar">
      <div className="monitor-filter-group">
        <span>技术分类</span>
        <div className="monitor-filter-pills">
          {categoryOptions.map((option) => (
            <button
              key={option}
              type="button"
              className={`monitor-filter-pill ${selectedCategory === option ? "monitor-filter-pill--active" : ""}`}
              onClick={() => onCategoryChange(selectedCategory === option ? "" : option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
      <div className="monitor-filter-group">
        <span>关注主题</span>
        <div className="monitor-filter-pills">
          {topicOptions.map((option) => (
            <button
              key={option}
              type="button"
              className={`monitor-filter-pill ${selectedTopic === option ? "monitor-filter-pill--active" : ""}`}
              onClick={() => onTopicChange(selectedTopic === option ? "" : option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

function ProjectOutline({ projectSections, activeSectionId }) {
  return (
    <aside className="project-outline">
      <div className="project-outline__inner">
        <p className="section-kicker">Navigator</p>
        <h3>快速定位</h3>
        <div className="project-outline__list">
          {projectSections.map((project) => {
            const projectRootId = sectionId("project", project.id);
            const releaseId = sectionId("project", project.id, "release");

            return (
              <section
                key={project.id}
                className={`project-outline__group ${activeSectionId?.startsWith(projectRootId) ? "project-outline__group--active" : ""}`}
                style={projectThemeStyle(project.id)}
              >
                <a
                  href={`#${projectRootId}`}
                  className={`project-outline__project-link ${activeSectionId === projectRootId ? "project-outline__link--active" : ""}`}
                >
                  {project.name}
                </a>
                <div className="project-outline__children">
                  {project.release_area?.enabled ? (
                    <a
                      href={`#${releaseId}`}
                      className={`project-outline__child-link ${activeSectionId === releaseId ? "project-outline__link--active" : ""}`}
                    >
                      ReleaseNote 区
                    </a>
                  ) : null}
                  {(project.docs_area?.categories || []).map((category) => {
                    const categoryId = sectionId("project", project.id, "docs", category.category);
                    return (
                      <a
                        key={category.category}
                        href={`#${categoryId}`}
                        className={`project-outline__child-link ${activeSectionId === categoryId ? "project-outline__link--active" : ""}`}
                      >
                        {category.category}
                      </a>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </aside>
  );
}

function useActiveProjectSection(projectSections) {
  const [activeSectionId, setActiveSectionId] = useState("");

  useEffect(() => {
    const ids = [];
    for (const project of projectSections) {
      ids.push(sectionId("project", project.id));
      if (project.release_area?.enabled) {
        ids.push(sectionId("project", project.id, "release"));
      }
      for (const category of project.docs_area?.categories || []) {
        ids.push(sectionId("project", project.id, "docs", category.category));
      }
    }

    const elements = ids
      .map((id) => document.getElementById(id))
      .filter(Boolean);

    if (!elements.length) {
      return undefined;
    }

    if (typeof window === "undefined" || typeof window.IntersectionObserver === "undefined") {
      setActiveSectionId(elements[0].id);
      return undefined;
    }

    const observer = new window.IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => right.intersectionRatio - left.intersectionRatio);
        if (visible[0]?.target?.id) {
          setActiveSectionId(visible[0].target.id);
        }
      },
      {
        rootMargin: "-20% 0px -65% 0px",
        threshold: [0.1, 0.4, 0.7],
      },
    );

    for (const element of elements) {
      observer.observe(element);
    }

    setActiveSectionId(elements[0].id);

    return () => {
      observer.disconnect();
    };
  }, [projectSections]);

  return activeSectionId;
}

export default function ProjectMonitorPage({ projectSections }) {
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");

  const topicOptions = useMemo(() => {
    const labels = new Set();
    for (const project of projectSections) {
      for (const topic of project.focus_topics || []) {
        labels.add(topic);
      }
    }
    return FOCUS_TOPIC_OPTIONS.filter((topic) => labels.has(topic));
  }, [projectSections]);

  const filteredProjectSections = useMemo(() => {
    return projectSections
      .map((project) => {
        if (selectedCategory && !(project.tech_categories || []).includes(selectedCategory)) {
          return null;
        }
        if (selectedTopic && !(project.focus_topics || []).includes(selectedTopic)) {
          return null;
        }

        const releaseItems = (project.release_area?.items || []).filter((item) => {
          return true;
        });

        const docsCategories = (project.docs_area?.categories || [])
          .map((category) => ({
            ...category,
            items: (category.items || []).filter((item) => {
              return true;
            }),
          }))
          .filter((category) => category.items.length > 0);

        return {
          ...project,
          release_area: {
            ...(project.release_area || {}),
            items: releaseItems,
          },
          docs_area: {
            ...(project.docs_area || {}),
            categories: docsCategories,
          },
        };
      })
      .filter(Boolean)
      .filter((project) => (project.release_area?.items || []).length > 0 || (project.docs_area?.categories || []).length > 0);
  }, [projectSections, selectedCategory, selectedTopic]);

  const activeSectionId = useActiveProjectSection(filteredProjectSections);

  return (
    <section className="project-monitor-page">
      <div className="project-monitor-intro">
        <p className="section-kicker">Monitoring</p>
        <h2>情报监控</h2>
        <p>按项目跟踪版本、文档与分析结论。</p>
      </div>

      <FilterBar
        categoryOptions={FOCUS_CATEGORIES}
        topicOptions={topicOptions}
        selectedCategory={selectedCategory}
        selectedTopic={selectedTopic}
        onCategoryChange={setSelectedCategory}
        onTopicChange={setSelectedTopic}
      />

      {!filteredProjectSections.length ? <div className="empty-state">当前筛选下没有匹配内容。</div> : null}

      <div className="project-monitor-layout">
        <div className="project-sections">
          {filteredProjectSections.map((project) => (
            <ProjectPanel key={project.id} project={project} />
          ))}
        </div>
        <ProjectOutline projectSections={filteredProjectSections} activeSectionId={activeSectionId} />
      </div>
    </section>
  );
}
