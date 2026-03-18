import { startTransition, useEffect, useMemo, useState } from "react";

import brandAvatar from "./assets/brand-icon.png";
import AIConsolePage from "./components/AIConsolePage";
import DocsWorkbenchPage from "./components/DocsWorkbenchPage";
import HelpTip from "./components/HelpTip";
import IntelOverviewPage from "./components/IntelOverviewPage";
import ProjectMonitorPage from "./components/ProjectMonitorPage";
import SettingsPage from "./components/SettingsPage";
import SyncLogDrawer from "./components/SyncLogDrawer";
import SyncMonitorPage from "./components/SyncMonitorPage";
import {
  createProject,
  fetchConfig,
  fetchDashboard,
  fetchProjects,
  fetchSyncRuns,
  fetchSyncStatus,
  queryAssistant,
  triggerSync,
  updateConfig,
  updateProject,
} from "./lib/api";
import { selectPrimaryJob } from "./lib/syncJobs";

const NAV_ITEMS = [
  { id: "cover", icon: "◌", label: "封面", title: "封面", help: "查看今日头条、系统状态和常用入口。" },
  { id: "clues", icon: "◎", label: "线索台", title: "线索台", help: "查看当前同步、历史 Job 和异常入口。" },
  { id: "topics", icon: "▣", label: "专题库", title: "专题库", help: "按项目和主题浏览长期变化。" },
  { id: "docsdesk", icon: "◫", label: "文档台", title: "文档台", help: "看页面变化、详细解读和深读入口。" },
  { id: "research", icon: "◇", label: "研究台", title: "研究台", help: "提问、看报告、查证据。" },
  { id: "settings", icon: "◧", label: "设置", title: "设置", help: "管理模型、助手和项目配置。" },
];

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [projects, setProjects] = useState([]);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncRuns, setSyncRuns] = useState([]);
  const [selectedSyncRunId, setSelectedSyncRunId] = useState("");
  const [submittingProject, setSubmittingProject] = useState(false);
  const [savingProjectMetadataId, setSavingProjectMetadataId] = useState("");
  const [savingConfig, setSavingConfig] = useState(false);
  const [activePage, setActivePage] = useState("cover");
  const [logDrawerOpen, setLogDrawerOpen] = useState(false);
  const [logFilter, setLogFilter] = useState("all");
  const [selectedDocsProjectId, setSelectedDocsProjectId] = useState("");
  const [highlightedDocsEventId, setHighlightedDocsEventId] = useState("");
  const [researchSeed, setResearchSeed] = useState(null);
  const [projectForm, setProjectForm] = useState({
    name: "",
    githubUrl: "",
    docsUrl: "",
  });

  useEffect(() => {
    let timerId = 0;
    let activeController = null;

    async function load(signal) {
      try {
        const [dashboardPayload, projectsPayload, configPayload] = await Promise.all([
          fetchDashboard(signal),
          fetchProjects(signal),
          fetchConfig(signal),
        ]);
        const [syncStatusPayload, syncRunsPayload] = await Promise.all([
          fetchSyncStatus(signal),
          fetchSyncRuns(signal, 20),
        ]);
        startTransition(() => {
          setDashboard(dashboardPayload);
          setProjects(projectsPayload);
          setConfig(configPayload);
          setSyncStatus(syncStatusPayload);
          setSyncRuns(syncRunsPayload);
          setError("");
          setLoading(false);
        });
      } catch (loadError) {
        if (loadError.name !== "AbortError") {
          setError(loadError instanceof Error ? loadError.message : "加载失败");
          setLoading(false);
        }
      }
    }

    function scheduleLoad() {
      activeController?.abort();
      activeController = new AbortController();
      load(activeController.signal);
    }

    scheduleLoad();
    timerId = window.setInterval(scheduleLoad, 30000);

    return () => {
      activeController?.abort();
      window.clearInterval(timerId);
    };
  }, []);

  useEffect(() => {
    let timerId = 0;
    let activeController = null;

    async function loadStatus(signal) {
      try {
        const [statusPayload, runsPayload] = await Promise.all([
          fetchSyncStatus(signal),
          fetchSyncRuns(signal, 20),
        ]);
        startTransition(() => {
          setSyncStatus(statusPayload);
          setSyncRuns(runsPayload);
        });
      } catch (statusError) {
        if (statusError.name !== "AbortError") {
          setError(statusError instanceof Error ? statusError.message : "同步状态读取失败");
        }
      }
    }

    function scheduleStatusLoad() {
      activeController?.abort();
      activeController = new AbortController();
      loadStatus(activeController.signal);
    }

    scheduleStatusLoad();
    timerId = window.setInterval(scheduleStatusLoad, syncStatus?.status === "running" ? 2000 : 10000);

    return () => {
      activeController?.abort();
      window.clearInterval(timerId);
    };
  }, [syncStatus?.status]);

  async function handleSync() {
    setSyncing(true);
    try {
      const statusPayload = await triggerSync();
      const runsPayload = await fetchSyncRuns();
      startTransition(() => {
        setSyncStatus(statusPayload);
        setSyncRuns(runsPayload);
        setSelectedSyncRunId(statusPayload.run_id || "");
        setError("");
      });
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : "同步失败");
    } finally {
      setSyncing(false);
    }
  }

  async function handleProjectSubmit(event) {
    event.preventDefault();
    setSubmittingProject(true);
    try {
      const created = await createProject({
        name: projectForm.name,
        github_url: projectForm.githubUrl,
        docs_url: projectForm.docsUrl,
      });
      startTransition(() => {
        setProjects((current) => [...current, created]);
        setProjectForm({ name: "", githubUrl: "", docsUrl: "" });
        setError("");
      });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "新增项目失败");
    } finally {
      setSubmittingProject(false);
    }
  }

  async function handleConfigSave(payload) {
    setSavingConfig(true);
    try {
      const updated = await updateConfig(payload);
      startTransition(() => {
        setConfig(updated);
        setError("");
      });
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "保存配置失败");
    } finally {
      setSavingConfig(false);
    }
  }

  async function handleProjectMetadataSave(projectId, payload) {
    setSavingProjectMetadataId(projectId);
    try {
      const updated = await updateProject(projectId, payload);
      startTransition(() => {
        setProjects((current) => current.map((project) => (project.id === projectId ? updated : project)));
        setDashboard((current) =>
          current
            ? {
                ...current,
                projects: (current.projects || []).map((project) => (project.id === projectId ? { ...project, ...updated } : project)),
              }
            : current,
        );
        setError("");
      });
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "保存项目分类失败");
    } finally {
      setSavingProjectMetadataId("");
    }
  }

  const overview = dashboard?.overview;
  const homepageProjects = dashboard?.homepage_projects ?? [];
  const projectBoard = dashboard?.project_board ?? [];
  const recentProjectUpdates = dashboard?.recent_project_updates ?? [];
  const dailyDigestHistory = dashboard?.daily_digest_history ?? [];
  const projectSections = dashboard?.projects ?? [];
  const currentPage = useMemo(() => NAV_ITEMS.find((item) => item.id === activePage) || NAV_ITEMS[0], [activePage]);
  const primarySyncRun = useMemo(() => {
    const selectedRun = syncRuns.find((run) => run.id === selectedSyncRunId);
    return selectedRun || selectPrimaryJob(syncRuns);
  }, [selectedSyncRunId, syncRuns]);

  useEffect(() => {
    if (!syncRuns.length) {
      setSelectedSyncRunId("");
      return;
    }
    setSelectedSyncRunId((current) => {
      if (current && syncRuns.some((run) => run.id === current)) {
        return current;
      }
      return selectPrimaryJob(syncRuns)?.id || "";
    });
  }, [syncRuns]);

  function handleOpenLogs(filter = "all") {
    setLogFilter(filter);
    setLogDrawerOpen(true);
  }

  function handleOpenDocs(projectId = "", eventId = "") {
    setSelectedDocsProjectId(projectId);
    setHighlightedDocsEventId(eventId);
    setActivePage("docsdesk");
  }

  function handleStartResearch(seed) {
    setResearchSeed(seed);
    setActivePage("research");
  }

  return (
    <div className="workbench-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <div className="sidebar__brand-mark">
            <img className="brand-avatar brand-avatar--sidebar" src={brandAvatar} alt="品牌头像" />
            <div>
              <p>架构师</p>
              <strong>开源情报站</strong>
            </div>
          </div>
          <span className="sidebar__brand-note">开源动态、中文结论、同步日志</span>
        </div>
        <nav className="sidebar__nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`sidebar__nav-item ${item.id === activePage ? "sidebar__nav-item--active" : ""}`}
              type="button"
              onClick={() => setActivePage(item.id)}
            >
              <span className="sidebar__nav-icon" aria-hidden="true">
                {item.icon}
              </span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <footer className="sidebar__footer">开源动态、中文结论、同步日志</footer>
      </aside>

      <main className="workbench-main">
        <header className="topbar">
          <div className="topbar__title">
            <h1>{currentPage.title}</h1>
            <HelpTip label={`${currentPage.title}说明`} text={currentPage.help} />
          </div>
          {activePage === "clues" ? (
            <button className="primary-button" onClick={handleSync} disabled={syncing}>
              {syncing ? "正在同步..." : "立即同步"}
            </button>
          ) : null}
        </header>

        {error ? <div className="error-banner">{error}</div> : null}
        {loading ? <section className="empty-state">正在读取最新数据...</section> : null}

        {!loading && activePage === "cover" ? (
          <IntelOverviewPage
            overview={overview}
            homepageProjects={homepageProjects}
            projectBoard={projectBoard}
            recentProjectUpdates={recentProjectUpdates}
            dailyDigestHistory={dailyDigestHistory}
          />
        ) : null}

        {!loading && activePage === "clues" ? (
          <SyncMonitorPage
            primaryRun={primarySyncRun}
            runs={syncRuns}
            selectedRunId={selectedSyncRunId}
            liveStatus={syncStatus}
            onSelectRun={setSelectedSyncRunId}
            onOpenLogs={handleOpenLogs}
          />
        ) : null}

        {!loading && activePage === "topics" ? (
          <ProjectMonitorPage projectSections={projectSections} onOpenDocs={handleOpenDocs} />
        ) : null}

        {!loading && activePage === "docsdesk" ? (
          <DocsWorkbenchPage
            initialProjectId={selectedDocsProjectId}
            highlightedEventId={highlightedDocsEventId}
            onSelectProject={setSelectedDocsProjectId}
            onStartResearch={handleStartResearch}
          />
        ) : null}

        {!loading && activePage === "research" ? (
          <AIConsolePage projects={projects} assistantConfig={config?.assistant} onQuery={queryAssistant} initialContext={researchSeed} />
        ) : null}

        {!loading && activePage === "settings" ? (
          <SettingsPage
            config={config}
            projects={projects}
            projectForm={projectForm}
            setProjectForm={setProjectForm}
            submittingProject={submittingProject}
            savingProjectMetadataId={savingProjectMetadataId}
            savingConfig={savingConfig}
            onProjectSubmit={handleProjectSubmit}
            onProjectMetadataSave={handleProjectMetadataSave}
            onConfigSave={handleConfigSave}
          />
        ) : null}

        <SyncLogDrawer
          open={logDrawerOpen}
          onClose={() => setLogDrawerOpen(false)}
          currentRunId={selectedSyncRunId || syncStatus?.run_id}
          initialFilter={logFilter}
        />
      </main>
    </div>
  );
}
