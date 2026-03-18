import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SyncStatusPanel from "../components/SyncStatusPanel";

describe("SyncStatusPanel", () => {
  it("shows completed-with-failures copy for successful jobs with failed items", () => {
    render(
      <SyncStatusPanel
        run={{
          run_kind: "scheduled-incremental",
          status: "success",
          phase: "completed",
          message: "定时增量同步完成",
          started_at: "2026-03-15T02:00:00Z",
          finished_at: "2026-03-15T02:31:00Z",
          last_heartbeat_at: "2026-03-15T02:31:00Z",
          metrics: {
            total_sources: 26,
            processed_sources: 26,
            new_events: 9,
            analyzed_events: 7,
            failed_events: 1,
            skipped_events: 4,
          },
        }}
        onOpenLogs={vi.fn()}
      />,
    );

    expect(screen.getByRole("heading", { name: "当前", level: 2 })).toBeInTheDocument();
    expect(screen.getByText("已完成，含失败项")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "查看日志" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "跳过" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "新增" })).toHaveTextContent("9");
    expect(screen.getByRole("button", { name: "已分析" })).toHaveTextContent("7");
    expect(screen.getByRole("button", { name: "失败" })).toHaveTextContent("1");
    expect(screen.getByRole("button", { name: "跳过" })).toHaveTextContent("4");
    expect(screen.getByText("定时增量同步")).toBeInTheDocument();
    expect(screen.getByText("本 Job 合计")).toBeInTheDocument();
  });

  it("shows stalled state explicitly when backend marks the sync as stalled", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-03-10T04:15:00Z"));

    render(
      <SyncStatusPanel
        run={{
          status: "running",
          run_kind: "manual-incremental",
          phase: "incremental",
          message: "正在抓取 GitHub releases",
          started_at: "2026-03-10T04:10:00Z",
          finished_at: null,
          last_heartbeat_at: "2026-03-10T04:10:00Z",
          metrics: {
            processed_sources: 1,
            total_sources: 8,
            new_events: 2,
            analyzed_events: 1,
            failed_events: 0,
            skipped_events: 0,
          },
          error: "",
          result: {},
        }}
        liveStatus={{
          run_id: "run_1",
          current_label: "cilium/cilium",
          heartbeat_age_seconds: 300,
          is_stalled: true,
          last_heartbeat_at: "2026-03-10T04:10:00Z",
          status: "running",
        }}
      />,
    );

    expect(screen.getByText("可能卡住")).toBeInTheDocument();
    expect(screen.getByText("心跳超时")).toBeInTheDocument();

    vi.useRealTimers();
  });
});
