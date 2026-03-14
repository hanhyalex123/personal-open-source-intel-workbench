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

function StatCard({ label, value, hint }) {
  return (
    <div className="stat-card">
      <div className="stat-card__label">
        <CoverIcon>◈</CoverIcon>
        <p>{label}</p>
      </div>
      <strong>{value}</strong>
      {hint ? <span>{hint}</span> : null}
    </div>
  );
}

function SignalNote({ icon, label, value }) {
  return (
    <div className="sync-note">
      <div className="sync-note__label">
        <CoverIcon>{icon}</CoverIcon>
        <span>{label}</span>
      </div>
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
  return (
    <div className="intel-page">
      <section className="hero-card hero-card--cover">
        <div className="hero-copy">
          <div className="hero-masthead">
            <div className="hero-masthead__meta">
              <p className="eyebrow">情报值班台</p>
              <span className="hero-tag">Open Source Desk</span>
            </div>
            <div className="hero-badge">
              <CoverIcon>◉</CoverIcon>
              <span>情报封面</span>
            </div>
          </div>
          <div className="hero-brandline">
            <span className="hero-brandline__seal" aria-hidden="true">
              情
            </span>
            <div>
              <strong>架构师开源情报站</strong>
              <p>把开源动态转成可执行的中文结论</p>
            </div>
          </div>
          <h1>日报首页</h1>
          <p className="hero-text">固定日报放首页，增量变化看提醒，项目下钻放到情报监控页。</p>
          <div className="hero-markers">
            <div className="hero-marker">
              <span>值班视角</span>
              <strong>先看最值得跟进的项目结论</strong>
            </div>
            <div className="hero-marker">
              <span>更新节奏</span>
              <strong>增量提醒与固定日报分层展示</strong>
            </div>
            <div className="hero-marker hero-marker--wide">
              <span>产品短宣言</span>
              <strong>开源动态、中文结论、同步日志</strong>
            </div>
          </div>
        </div>

        <div className="hero-actions">
          <SignalNote
            icon="◎"
            label="最近抓取成功"
            value={formatDate(overview?.last_fetch_success_at || overview?.last_sync_at)}
          />
          <SignalNote
            icon="◌"
            label="最近日报生成"
            value={formatDate(overview?.last_daily_digest_at || overview?.last_daily_summary_at)}
          />
          <div className="hero-sidecard">
            <div className="hero-sidecard__kicker">
              <CoverIcon>▣</CoverIcon>
              <span>同步信号</span>
            </div>
            <strong>{overview?.scheduler?.running ? "调度已开启" : "调度未开启"}</strong>
            <p>{overview?.scheduler?.interval_minutes ? `${overview.scheduler.interval_minutes} 分钟一次` : "等待设置"}</p>
          </div>
        </div>
      </section>

      <section className="intel-info-band">
        <div className="stat-grid">
          <StatCard label="结论总数" value={overview?.total_items ?? 0} />
          <StatCard label="项目数" value={homepageProjects.length} />
          <StatCard
            label="最近抓取成功"
            value={formatDate(overview?.last_incremental_analysis_at || overview?.last_fetch_success_at)}
          />
        </div>

        <div className="stat-grid stat-grid--secondary">
          <StatCard
            label="调度状态"
            value={overview?.scheduler?.running ? "已开启" : "未开启"}
            hint={overview?.scheduler?.interval_minutes ? `${overview.scheduler.interval_minutes} 分钟一次` : ""}
          />
          <StatCard label="最近日报生成" value={formatDate(overview?.last_daily_digest_at)} />
        </div>
      </section>

      <section className="intel-section">
        <SectionHeading
          icon="◆"
          kicker="Daily Digest"
          title="今日日报"
          copy="每天固定生成一版，主要告诉你今天最值得看的项目结论。"
        />
        <div className="project-summary-stack">
          {homepageProjects.length ? (
            homepageProjects.map((item) => <ProjectSummaryCard key={item.id || item.project_id} item={item} />)
          ) : (
            <div className="empty-state">当前还没有可展示的项目摘要。</div>
          )}
        </div>
      </section>

      <section className="intel-section">
        <SectionHeading
          icon="◈"
          kicker="Incremental Watch"
          title="增量提醒"
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
    </div>
  );
}
