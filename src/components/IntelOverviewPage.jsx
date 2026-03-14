import brandAvatar from "../assets/brand-avatar-anime.png";
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

function CoverIcon({ children }) {
  return (
    <span className="cover-icon" aria-hidden="true">
      {children}
    </span>
  );
}

function SnapshotRow({ icon, label, value, hint }) {
  return (
    <div className="snapshot-row">
      <div className="snapshot-row__label">
        <CoverIcon>{icon}</CoverIcon>
        <div>
          <span>{label}</span>
          {hint ? <p>{hint}</p> : null}
        </div>
      </div>
      <strong>{value}</strong>
    </div>
  );
}

function SnapshotStat({ label, value }) {
  return (
    <div className="snapshot-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SectionHeading({ icon, kicker, title, copy }) {
  return (
    <div className="intel-section__header">
      <div>
        <div className="section-kicker section-kicker--icon">
          <CoverIcon>{icon}</CoverIcon>
          <span>{kicker}</span>
        </div>
        <h2>{title}</h2>
      </div>
      <p className="intel-section__copy">{copy}</p>
    </div>
  );
}

export default function IntelOverviewPage({ overview, homepageProjects, recentProjectUpdates, dailyDigestHistory }) {
  const [featuredProject, ...otherProjects] = homepageProjects || [];

  return (
    <div className="intel-page">
      <section className="hero-card hero-card--cover homepage-topline">
        <div className="homepage-topline__lead">
          <div className="hero-masthead">
            <div className="hero-masthead__meta">
              <p className="eyebrow">情报值班台</p>
              <span className="hero-tag">Open Source Desk</span>
            </div>
          </div>

          <div className="hero-brandline">
            <img className="brand-avatar brand-avatar--hero" src={brandAvatar} alt="品牌头像" />
            <div>
              <strong>架构师开源情报站</strong>
              <p>把开源动态转成可执行的中文结论</p>
            </div>
          </div>

          <div className="homepage-headline homepage-headline--simple">
            <h1>日报首页</h1>
            <p className="hero-text">固定日报放首页，增量变化看提醒，项目下钻放到情报监控页。</p>
            <p className="homepage-headline__note">先看今天最值得跟进的项目和运行信号。</p>
          </div>

          <div className="homepage-feature">
            <div className="homepage-feature__header">
              <div>
                <p className="section-kicker">重点结论</p>
                <h2>先看今天最值得处理的项目</h2>
              </div>
              <p>把主结论直接放进首页首屏，不再等你往下翻。</p>
            </div>
            {featuredProject ? (
              <div className="homepage-feature__card">
                <ProjectSummaryCard item={featuredProject} />
              </div>
            ) : (
              <div className="empty-state">当前还没有可展示的项目摘要。</div>
            )}
          </div>
        </div>

        <aside className="homepage-topline__aside">
          <section className="homepage-snapshot">
            <div className="homepage-snapshot__header">
              <div>
                <p className="section-kicker">运行快照</p>
                <h2>当前班次</h2>
              </div>
              <span className="homepage-snapshot__status">
                {overview?.scheduler?.running ? "调度在线" : "调度离线"}
              </span>
            </div>

            <div className="homepage-snapshot__rows">
              <SnapshotRow
                icon="◎"
                label="最近抓取成功"
                value={formatDate(overview?.last_fetch_success_at || overview?.last_sync_at)}
              />
              <SnapshotRow
                icon="◌"
                label="最近日报生成"
                value={formatDate(overview?.last_daily_digest_at || overview?.last_daily_summary_at)}
              />
              <SnapshotRow
                icon="▣"
                label="调度状态"
                value={overview?.scheduler?.running ? "已开启" : "未开启"}
                hint={overview?.scheduler?.interval_minutes ? `${overview.scheduler.interval_minutes} 分钟一次` : "等待设置"}
              />
            </div>

            <div className="homepage-snapshot__stats">
              <SnapshotStat label="结论总数" value={overview?.total_items ?? 0} />
              <SnapshotStat label="项目数" value={homepageProjects.length} />
              <SnapshotStat
                label="最近抓取成功"
                value={formatDate(overview?.last_incremental_analysis_at || overview?.last_fetch_success_at)}
              />
              <SnapshotStat label="最近日报生成" value={formatDate(overview?.last_daily_digest_at)} />
            </div>
          </section>
        </aside>
      </section>

      {otherProjects.length ? (
        <section className="intel-section">
          <SectionHeading
            icon="◆"
            kicker="Daily Digest"
            title="更多结论"
            copy="首页首屏已经固定展示主结论，其余项目继续按摘要往下排。"
          />
          <div className="project-summary-stack">
            {otherProjects.map((item) => (
              <ProjectSummaryCard key={item.id || item.project_id} item={item} />
            ))}
          </div>
        </section>
      ) : null}

      <section className="homepage-lower-grid">
        <section className="intel-section">
          <SectionHeading
            icon="◈"
            kicker="Incremental Watch"
            title="增量快讯"
            copy="日报生成后出现的新变化统一放这里，方便快速扫一遍。"
          />
          <IncrementalUpdateList updates={recentProjectUpdates} />
        </section>

        <section className="intel-section">
          <SectionHeading
            icon="▤"
            kicker="Archive"
            title="日报归档"
            copy="每天只保留一版日报，往期结论在这里回看。"
          />
          <DailyDigestHistory history={dailyDigestHistory} />
        </section>
      </section>
    </div>
  );
}
