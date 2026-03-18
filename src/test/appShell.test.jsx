import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";
import AppProviders from "../providers/AppProviders";

const dashboardPayload = {
  overview: {
    scheduler: {
      running: true,
      interval_minutes: 60,
    },
  },
  homepage_projects: [],
  project_board: [],
  recent_project_updates: [],
  daily_digest_history: [],
  projects: [],
  sources: [],
  groups: [],
};

const projectsPayload = [{ id: "openclaw", name: "OpenClaw" }];

const configPayload = {
  assistant: {
    enabled: true,
    default_project_ids: [],
    default_categories: [],
    default_timeframe: "14d",
  },
};

const syncStatusPayload = {
  status: "idle",
  run_id: "",
  run_kind: "",
  phase: "",
  message: "",
};

const syncRunsPayload = [];

function createFetchMock() {
  return vi.fn((url) => {
    const requestUrl = String(url);

    if (requestUrl.includes("/api/dashboard")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(dashboardPayload) });
    }

    if (requestUrl.includes("/api/projects")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(projectsPayload) });
    }

    if (requestUrl.includes("/api/config")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(configPayload) });
    }

    if (requestUrl.includes("/api/sync/status")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(syncStatusPayload) });
    }

    if (requestUrl.includes("/api/sync/runs")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(syncRunsPayload) });
    }

    return Promise.reject(new Error(`unexpected request: ${url}`));
  });
}

describe("App shell", () => {
  beforeEach(() => {
    global.fetch = createFetchMock();
  });

  it("renders the unified console sider and header", async () => {
    render(
      <AppProviders>
        <App />
      </AppProviders>,
    );

    expect(await screen.findByTestId("app-shell-sider")).toBeInTheDocument();
    expect(screen.getByTestId("app-shell-header")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "线索台" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "线索台", level: 1 })).toBeInTheDocument();
    });
  });
});
