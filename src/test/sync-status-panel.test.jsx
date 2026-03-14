import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SyncStatusPanel from "../components/SyncStatusPanel";

describe("SyncStatusPanel", () => {
  it("uses clearer log entry copy", () => {
    render(
      <SyncStatusPanel
        status={{
          status: "running",
          message: "正在抓取 GitHub releases",
          current_label: "cilium/cilium",
          processed_sources: 1,
          total_sources: 8,
          new_events: 2,
          analyzed_events: 1,
          failed_events: 0,
          is_stalled: false,
          last_heartbeat_at: "2026-03-10T04:10:10Z",
        }}
        onOpenLogs={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "查看日志" })).toBeInTheDocument();
  });
});
