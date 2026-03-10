export async function fetchDashboard(signal) {
  const response = await fetch("/api/dashboard", { signal });
  if (!response.ok) {
    throw new Error(`dashboard request failed: ${response.status}`);
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
