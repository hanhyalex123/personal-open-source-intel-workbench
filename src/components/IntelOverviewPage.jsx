import ProjectSummaryCard from "./ProjectSummaryCard";

function formatDate(value) {
  if (!value) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function StatCard({ label, value, hint }) {
  return (
    <div className="stat-card">
      <p>{label}</p>
      <strong>{value}</strong>
      {hint ? <span>{hint}</span> : null}
    </div>
  );
}

function urgencyLabel(level) {
  if (level === "high") return "高";
  if (level === "medium") return "中";
  return "低";
}

function sourceDescription(source) {
  if (source.kind === "docs") {
    return "表示这个文档来源下，已经有多少条页面更新被抓取并整理成中文结论。";
  }
  return "表示这个项目来源下，已经有多少条版本或变更信息被抓取并整理成中文结论。";
}

function collectCategoryCards(projectSections) {
  const counts = new Map();
  for (const project of projectSections) {
    for (const category of project.docs_area?.categories || []) {
      counts.set(category.category, (counts.get(category.category) || 0) + (category.items?.length || 0));
    }
  }
  return Array.from(counts.entries()).map(([category, count]) => ({ category, count }));
}

export default function IntelOverviewPage({ overview, homepageProjects, sources, projectSections }) {
  const categoryCards = collectCategoryCards(projectSections);

  return (
    <div className="intel-page">
      <section className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">Daily Intel</p>
          <h1>每日项目情报</h1>
          <p className="hero-text">每个项目只保留今天最值得你看的 AI 摘要和关键依据。</p>
        </div>

        <div className="hero-actions">
          <div className="sync-note">
            <span>最近同步</span>
            <strong>{formatDate(overview?.last_sync_at)}</strong>
          </div>
          <div className="sync-note">
            <span>日报刷新</span>
            <strong>{formatDate(overview?.last_daily_summary_at)}</strong>
          </div>
        </div>
      </section>

      <section className="stat-grid">
        <StatCard label="结论总数" value={overview?.total_items ?? 0} />
        <StatCard label="项目数" value={projectSections.length} />
        <StatCard
          label="后台调度"
          value={overview?.scheduler?.running ? "已开启" : "未开启"}
          hint={overview?.scheduler?.interval_minutes ? `${overview.scheduler.interval_minutes} 分钟一次` : ""}
        />
      </section>

      <section className="intel-section">
        <div className="intel-section__header">
          <div>
            <p className="section-kicker">Project Daily Brief</p>
            <h2>项目摘要卡</h2>
          </div>
          <p className="intel-section__copy">首页按项目汇总，不再平铺全局时间流。每张卡只保留今天最值得看的情报。</p>
        </div>
        <div className="project-summary-stack">
          {homepageProjects.length ? (
            homepageProjects.map((item) => <ProjectSummaryCard key={item.id || item.project_id} item={item} />)
          ) : (
            <div className="empty-state">当前还没有可展示的项目摘要。</div>
          )}
        </div>
      </section>

      <div className="intel-grid">
        <section className="intel-section">
          <div className="intel-section__header">
            <div>
              <p className="section-kicker">Categories</p>
              <h2>技术分类</h2>
            </div>
            <p className="intel-section__copy">把文档变化按技术域聚起来，和项目监控页的逐项目视角做明确区分。</p>
          </div>
          <div className="category-grid">
            {categoryCards.length ? (
              categoryCards.map((item) => (
                <article key={item.category} className="category-card">
                  <strong>{item.category}</strong>
                  <span>{item.count} 条关联结论</span>
                </article>
              ))
            ) : (
              <div className="empty-state">当前还没有分类化的文档结论。</div>
            )}
          </div>
        </section>

        <section className="intel-section">
          <div className="intel-section__header">
            <div>
              <p className="section-kicker">Source Status</p>
              <h2>来源状态</h2>
            </div>
            <p className="intel-section__copy">这里不是评分，数字表示这个来源下已经完成中文分析的更新条目数。</p>
          </div>
          <div className="coverage-list">
            {sources.map((source) => (
              <article key={source.id} className="coverage-card coverage-card--status">
                <div className="coverage-card__intro">
                  <p className="source-overview-card__kind">{source.kind === "docs" ? "Docs" : "Repo"}</p>
                  <h3>{source.title}</h3>
                  <p className="coverage-card__summary">{sourceDescription(source)}</p>
                </div>
                <div className="coverage-card__metric-grid">
                  <div className="coverage-metric">
                    <span>已分析更新</span>
                    <strong>{source.total_items}</strong>
                  </div>
                  <div className="coverage-metric">
                    <span>固定结论</span>
                    <strong>{source.stable_items}</strong>
                  </div>
                  <div className="coverage-metric">
                    <span>当前优先级</span>
                    <strong>{urgencyLabel(source.highest_urgency)}</strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
