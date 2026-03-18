import brandAvatar from "../assets/brand-icon.png";
import DailyDigestHistory from "./DailyDigestHistory";
import HelpTip from "./HelpTip";
import IncrementalUpdateList from "./IncrementalUpdateList";
import ProjectSummaryCard from "./ProjectSummaryCard";
import ProjectRankBoard from "./ProjectRankBoard";

function formatDate(value) {
  if (!value) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function PulseItem({ label, value, hint }) {
  return (
    <article className="cover-pulse-item">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <p>{hint}</p> : null}
    </article>
  );
}

function CoverSectionHeader({ title, help }) {
  return (
    <header className="cover-section-header">
      <div className="cover-section-header__title">
        <h2>{title}</h2>
        {help ? <HelpTip label={`${title}说明`} text={help} /> : null}
      </div>
    </header>
  );
}

export default function IntelOverviewPage({ overview, homepageProjects, projectBoard, recentProjectUpdates, dailyDigestHistory }) {
  const [featuredProject, ...otherProjects] = homepageProjects || [];
  const schedulerRunning = overview?.scheduler?.running;

  return (
    <div className="cover-page">
      <section className="cover-hero">
        <div className="cover-hero__headline">
          <div className="cover-masthead">
            <div>
              <h2>架构师开源情报站</h2>
            </div>
            <div className={`cover-status ${schedulerRunning ? "cover-status--live" : "cover-status--quiet"}`}>
              {schedulerRunning ? "在线" : "离线"}
            </div>
          </div>

          <div className="cover-headline">
            <div className="cover-headline__title">
              <h1>头条</h1>
              <HelpTip label="头条说明" text="查看今天最值得先看的项目结论。" />
            </div>
            <div className="cover-avatar">
              <img className="brand-avatar brand-avatar--hero" src={brandAvatar} alt="品牌头像" />
            </div>
          </div>

          <div className="cover-lead-story">
            {featuredProject ? (
              <ProjectSummaryCard item={featuredProject} />
            ) : (
              <div className="empty-state">当前还没有生成可上封面的项目结论。</div>
            )}
          </div>
        </div>

        <aside className="cover-hero__rail">
          <section className="cover-pulse">
            <CoverSectionHeader title="状态" help="确认调度、抓取和日报是否正常。" />
            <div className="cover-pulse__grid">
              <PulseItem label="最近抓取成功" value={formatDate(overview?.last_fetch_success_at || overview?.last_sync_at)} />
              <PulseItem label="最近日报生成" value={formatDate(overview?.last_daily_digest_at || overview?.last_daily_summary_at)} />
              <PulseItem
                label="调度状态"
                value={schedulerRunning ? "已开启" : "未开启"}
                hint={overview?.scheduler?.interval_minutes ? `${overview.scheduler.interval_minutes} 分钟一次` : ""}
              />
              <PulseItem label="最近分析完成" value={formatDate(overview?.last_incremental_analysis_at || overview?.last_analysis_at)} />
            </div>
          </section>

          <section className="cover-brief">
            <CoverSectionHeader title="入口" help="常用页面入口。" />
            <div className="cover-brief__list">
              <article>
                <strong>线索台</strong>
              </article>
              <article>
                <strong>专题库</strong>
              </article>
              <article>
                <strong>文档台</strong>
              </article>
            </div>
          </section>
        </aside>
      </section>

      <section className="cover-section">
        <CoverSectionHeader title="项目榜" help="只看日报候选项目，先判断现在该看谁。" />
        <ProjectRankBoard items={projectBoard} />
      </section>

      {otherProjects.length ? (
        <section className="cover-section">
          <CoverSectionHeader title="专题" help="继续跟进的项目。" />
          <div className="cover-secondary-grid">
            {otherProjects.map((item) => (
              <ProjectSummaryCard key={item.id || item.project_id} item={item} />
            ))}
          </div>
        </section>
      ) : null}

      <section className="cover-lower-grid">
        <section className="cover-section">
          <CoverSectionHeader title="快讯" help="最近增量变化。" />
          <IncrementalUpdateList updates={recentProjectUpdates} />
        </section>

        <section className="cover-section cover-section--archive">
          <CoverSectionHeader title="归档" help="查看历史日报。" />
          <DailyDigestHistory history={dailyDigestHistory} />
        </section>
      </section>
    </div>
  );
}
