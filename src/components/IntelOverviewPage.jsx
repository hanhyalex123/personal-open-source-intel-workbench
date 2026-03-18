import { useState } from "react";

import brandAvatar from "../assets/brand-icon.png";
import { fetchDailyDigestArchive } from "../lib/api";
import ArchiveDigestPanel from "./ArchiveDigestPanel";
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

export default function IntelOverviewPage({
  overview,
  homepageProjects,
  projectBoard,
  recentProjectUpdates,
  dailyDigestHistory,
  onOpenDocs,
}) {
  const [selectedDigestDate, setSelectedDigestDate] = useState("");
  const [archiveDigest, setArchiveDigest] = useState(null);
  const [archiveLoading, setArchiveLoading] = useState(false);
  const [archiveError, setArchiveError] = useState("");
  const [featuredProject, ...otherProjects] = homepageProjects || [];
  const schedulerRunning = overview?.scheduler?.running;

  async function handleSelectDigest(digestDate) {
    if (!digestDate) return;
    setSelectedDigestDate(digestDate);
    setArchiveLoading(true);
    setArchiveError("");
    try {
      const payload = await fetchDailyDigestArchive(digestDate);
      setArchiveDigest(payload);
    } catch (loadError) {
      setArchiveDigest(null);
      setArchiveError(loadError instanceof Error ? loadError.message : "历史日报读取失败");
    } finally {
      setArchiveLoading(false);
    }
  }

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
              <HelpTip label="头条说明" text="当前窗口内最值得先读的项目结论。" />
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
            <CoverSectionHeader title="状态" help="抓取、分析和日报的最近运行时间。" />
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
        </aside>
      </section>

      <section className="cover-section">
        <CoverSectionHeader title="快讯" help="日报后新增。" />
        <IncrementalUpdateList updates={recentProjectUpdates} onOpenDocs={onOpenDocs} />
      </section>

      <section className="cover-section">
        <CoverSectionHeader title="项目榜" help="30天变化，合并 release + 文档。" />
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

      <section className="cover-section cover-section--archive">
        <CoverSectionHeader title="归档" help="历史日报。" />
        <DailyDigestHistory
          history={dailyDigestHistory}
          selectedDate={selectedDigestDate}
          loading={archiveLoading}
          onSelectDate={handleSelectDigest}
        />
        <ArchiveDigestPanel
          digestDate={selectedDigestDate}
          payload={archiveDigest}
          loading={archiveLoading}
          error={archiveError}
        />
      </section>
    </div>
  );
}
