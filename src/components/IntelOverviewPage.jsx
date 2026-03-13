import DailyDigestHistory from "./DailyDigestHistory";
import IncrementalUpdateList from "./IncrementalUpdateList";
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

export default function IntelOverviewPage({ overview, homepageProjects, recentProjectUpdates, dailyDigestHistory }) {
  return (
    <div className="intel-page">
      <section className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">Daily Brief</p>
          <h1>日报首页</h1>
          <p className="hero-text">固定日报放首页，增量变化看提醒，项目下钻放到情报监控页。</p>
        </div>

        <div className="hero-actions">
          <div className="sync-note">
            <span>最近抓取成功</span>
            <strong>{formatDate(overview?.last_fetch_success_at || overview?.last_sync_at)}</strong>
          </div>
          <div className="sync-note">
            <span>最近日报生成</span>
            <strong>{formatDate(overview?.last_daily_digest_at || overview?.last_daily_summary_at)}</strong>
          </div>
        </div>
      </section>

      <section className="stat-grid">
        <StatCard label="结论总数" value={overview?.total_items ?? 0} />
        <StatCard label="项目数" value={homepageProjects.length} />
        <StatCard
          label="最近抓取成功"
          value={formatDate(overview?.last_incremental_analysis_at || overview?.last_fetch_success_at)}
        />
      </section>

      <section className="stat-grid stat-grid--secondary">
        <StatCard
          label="调度状态"
          value={overview?.scheduler?.running ? "已开启" : "未开启"}
          hint={overview?.scheduler?.interval_minutes ? `${overview.scheduler.interval_minutes} 分钟一次` : ""}
        />
        <StatCard label="最近日报生成" value={formatDate(overview?.last_daily_digest_at)} />
      </section>

      <section className="intel-section">
        <div className="intel-section__header">
          <div>
            <p className="section-kicker">Daily Digest</p>
            <h2>今日日报</h2>
          </div>
          <p className="intel-section__copy">每天固定生成一版，主要告诉你今天最值得看的项目结论。</p>
        </div>
        <div className="project-summary-stack">
          {homepageProjects.length ? (
            homepageProjects.map((item) => <ProjectSummaryCard key={item.id || item.project_id} item={item} />)
          ) : (
            <div className="empty-state">当前还没有可展示的项目摘要。</div>
          )}
        </div>
      </section>

      <section className="intel-section">
        <div className="intel-section__header">
          <div>
            <p className="section-kicker">Incremental Watch</p>
            <h2>增量提醒</h2>
          </div>
          <p className="intel-section__copy">日报生成后出现的新变化统一放这里，方便快速扫一遍。</p>
        </div>
        <IncrementalUpdateList updates={recentProjectUpdates} />
      </section>

      <section className="intel-section">
        <div className="intel-section__header">
          <div>
            <p className="section-kicker">Archive</p>
            <h2>日报归档</h2>
          </div>
          <p className="intel-section__copy">每天只保留一版日报，往期结论在这里回看。</p>
        </div>
        <DailyDigestHistory history={dailyDigestHistory} />
      </section>
    </div>
  );
}
