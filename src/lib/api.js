export async function fetchDashboard(signal) {
  const response = await fetch("/api/dashboard", { signal });
  if (!response.ok) {
    throw new Error(`dashboard request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchDailyDigestArchive(digestDate, signal) {
  const response = await fetch(`/api/daily-digests/${encodeURIComponent(digestDate)}`, { signal });
  if (!response.ok) {
    throw new Error(`daily digest archive request failed: ${response.status}`);
  }
  return response.json();
}

export async function triggerSync() {
  const response = await fetch("/api/sync", { method: "POST" });
  if (!response.ok) {
    throw new Error(`sync request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchSyncStatus(signal) {
  const response = await fetch("/api/sync/status", { signal });
  if (!response.ok) {
    throw new Error(`sync status request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchSyncRuns(signal, limit = 20) {
  const params = new URLSearchParams();
  if (limit !== undefined && limit !== null) {
    params.set("limit", String(limit));
  }
  const response = await fetch(`/api/sync/runs${params.toString() ? `?${params.toString()}` : ""}`, { signal });
  if (!response.ok) {
    throw new Error(`sync runs request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchSyncRun(runId, signal) {
  const response = await fetch(`/api/sync/runs/${encodeURIComponent(runId)}`, { signal });
  if (!response.ok) {
    throw new Error(`sync run request failed: ${response.status}`);
  }
  return response.json();
}

export async function clearSyncRuns() {
  const response = await fetch("/api/sync/runs", { method: "DELETE" });
  if (!response.ok) {
    throw new Error(`sync runs clear failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchProjects(signal) {
  const response = await fetch("/api/projects", { signal });
  if (!response.ok) {
    throw new Error(`projects request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchConfig(signal) {
  const response = await fetch("/api/config", { signal });
  if (!response.ok) {
    throw new Error(`config request failed: ${response.status}`);
  }
  return response.json();
}

export async function createProject(payload) {
  const response = await fetch("/api/projects", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`create project failed: ${response.status}`);
  }
  return response.json();
}

export async function updateProject(projectId, payload) {
  const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}`, {
    method: "PUT",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`update project failed: ${response.status}`);
  }
  return response.json();
}

export async function updateConfig(payload) {
  const response = await fetch("/api/config", {
    method: "PUT",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`update config failed: ${response.status}`);
  }
  return response.json();
}

export async function postReadEvent(payload) {
  const response = await fetch("/api/read-events", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`read event request failed: ${response.status}`);
  }
  return response.json();
}

export async function queryAssistant(payload) {
  const response = await fetch("/api/assistant/query", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`assistant query failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchDocsProjects(signal) {
  const response = await fetch("/api/docs/projects", { signal });
  if (!response.ok) {
    throw new Error(`docs projects request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchDocsProject(projectId, signal) {
  const response = await fetch(`/api/docs/projects/${encodeURIComponent(projectId)}`, { signal });
  if (!response.ok) {
    throw new Error(`docs project request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchDocsEvents(projectId, mode = "", signal) {
  const params = new URLSearchParams();
  if (mode) {
    params.set("mode", mode);
  }
  const response = await fetch(
    `/api/docs/projects/${encodeURIComponent(projectId)}/events${params.toString() ? `?${params.toString()}` : ""}`,
    { signal },
  );
  if (!response.ok) {
    throw new Error(`docs events request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchDocsPages(projectId, signal) {
  const response = await fetch(`/api/docs/projects/${encodeURIComponent(projectId)}/pages`, { signal });
  if (!response.ok) {
    throw new Error(`docs pages request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchDocsPageDiff(projectId, pageId, signal) {
  const response = await fetch(
    `/api/docs/projects/${encodeURIComponent(projectId)}/pages/${encodeURIComponent(pageId)}/diff`,
    { signal },
  );
  if (!response.ok) {
    throw new Error(`docs page diff request failed: ${response.status}`);
  }
  return response.json();
}
