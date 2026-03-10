import { useState } from "react";

import InsightCard from "./InsightCard";
import { projectThemeStyle } from "../lib/projectTheme";

function CollapsibleItemGrid({ title, items }) {
  const [expanded, setExpanded] = useState(false);
  const visibleItems = expanded ? items : items.slice(0, 3);
  const hasMore = items.length > 3;

  return (
    <section className="project-subsection">
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
  return (
    <section className="project-panel" data-project-id={project.id} style={projectThemeStyle(project.id)}>
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

      {project.release_area?.enabled ? <CollapsibleItemGrid title="ReleaseNote 区" items={project.release_area.items || []} /> : null}

      {project.docs_area?.enabled ? (
        <section className="project-subsection">
          <div className="project-subsection__header">
            <h3>文档区</h3>
          </div>
          <div className="docs-category-stack">
            {(project.docs_area.categories || []).map((category) => (
              <section key={category.category} className="docs-category">
                <CollapsibleItemGrid title={category.category} items={category.items} />
              </section>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}

export default function ProjectMonitorPage({ projectSections }) {
  return (
    <section className="project-monitor-page">
      <div className="project-monitor-intro">
        <p className="section-kicker">Project Stream</p>
        <h2>项目工作流视图</h2>
        <p>从总览切到单项目视角，逐个查看 ReleaseNote 与文档结论。</p>
      </div>

      <div className="project-sections">
        {projectSections.map((project) => (
          <ProjectPanel key={project.id} project={project} />
        ))}
      </div>
    </section>
  );
}
