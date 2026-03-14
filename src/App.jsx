import { startTransition, useEffect, useMemo, useState } from "react";

import AIConsolePage from "./components/AIConsolePage";
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
  fetchSyncStatus,
  queryAssistant,
  triggerSync,
  updateConfig,
} from "./lib/api";

const NAV_ITEMS = [
  { id: "intel", label: "日报", title: "日报", subtitle: "固定日报、同步雷达和增量提醒" },
  { id: "monitor", label: "同步监控", title: "同步监控", subtitle: "同步状态、日志与异常一目了然" },
  { id: "projects", label: "情报监控", title: "情报监控", subtitle: "按项目跟踪版本、文档与分析结论" },
  { id: "assistant", label: "AI 控制台", title: "AI 控制台", subtitle: "本地知识检索与结构化问答" },
  { id: "settings", label: "配置中心", title: "配置中心", subtitle: "Assistant 全局配置与项目接入" },
];

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [projects, setProjects] = useState([]);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [submittingProject, setSubmittingProject] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);
  const [activePage, setActivePage] = useState("intel");
  const [logDrawerOpen, setLogDrawerOpen] = useState(false);
  const [logFilter, setLogFilter] = useState("all");
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
        const syncStatusPayload = await fetchSyncStatus(signal);
        startTransition(() => {
          setDashboard(dashboardPayload);
          setProjects(projectsPayload);
          setConfig(configPayload);
          setSyncStatus(syncStatusPayload);
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
        const payload = await fetchSyncStatus(signal);
        startTransition(() => {
          setSyncStatus(payload);
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
      startTransition(() => {
        setSyncStatus(statusPayload);
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

  const overview = dashboard?.overview;
  const homepageProjects = dashboard?.homepage_projects ?? [];
  const recentProjectUpdates = dashboard?.recent_project_updates ?? [];
  const dailyDigestHistory = dashboard?.daily_digest_history ?? [];
  const projectSections = dashboard?.projects ?? [];
  const currentPage = useMemo(() => NAV_ITEMS.find((item) => item.id === activePage) || NAV_ITEMS[0], [activePage]);

  function handleOpenLogs(filter = "all") {
    setLogFilter(filter);
    setLogDrawerOpen(true);
  }

  return (
    <div className="workbench-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <p>Intel</p>
          <strong>Workbench</strong>
        </div>
        <nav className="sidebar__nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`sidebar__nav-item ${item.id === activePage ? "sidebar__nav-item--active" : ""}`}
              type="button"
              onClick={() => setActivePage(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <footer className="sidebar__footer">首页看日报，第二页看情报监控</footer>
      </aside>

      <main className="workbench-main">
        <header className="topbar">
          <div>
            <p className="section-kicker">Workspace</p>
            <h1>{currentPage.title}</h1>
            <p className="topbar__subtitle">{currentPage.subtitle}</p>
          </div>
          <button className="primary-button" onClick={handleSync} disabled={syncing}>
            {syncing ? "正在同步..." : "立即同步"}
          </button>
        </header>

        {error ? <div className="error-banner">{error}</div> : null}
        {loading ? <section className="empty-state">正在读取最新数据...</section> : null}

        {!loading && activePage === "intel" ? (
          <IntelOverviewPage
            overview={overview}
            homepageProjects={homepageProjects}
            recentProjectUpdates={recentProjectUpdates}
            dailyDigestHistory={dailyDigestHistory}
          />
        ) : null}

        {!loading && activePage === "monitor" ? (
          <SyncMonitorPage status={syncStatus} onOpenLogs={handleOpenLogs} />
        ) : null}

        {!loading && activePage === "projects" ? <ProjectMonitorPage projectSections={projectSections} /> : null}

        {!loading && activePage === "assistant" ? (
          <AIConsolePage projects={projects} assistantConfig={config?.assistant} onQuery={queryAssistant} />
        ) : null}

        {!loading && activePage === "settings" ? (
          <SettingsPage
            config={config}
            projects={projects}
            projectForm={projectForm}
            setProjectForm={setProjectForm}
            submittingProject={submittingProject}
            savingConfig={savingConfig}
            onProjectSubmit={handleProjectSubmit}
            onConfigSave={handleConfigSave}
          />
        ) : null}

        <SyncLogDrawer
          open={logDrawerOpen}
          onClose={() => setLogDrawerOpen(false)}
          currentRunId={syncStatus?.run_id}
          initialFilter={logFilter}
        />
      </main>
    </div>
  );
}
