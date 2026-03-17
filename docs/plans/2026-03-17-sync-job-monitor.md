# Sync Job Monitor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the sync monitor around Job records and root-cause the current sync failures so the UI reflects real Job outcomes instead of ambiguous system-wide failure.

**Architecture:** The monitor page becomes Job-first: `/api/sync/runs` drives the selected Job summary and `/api/sync/runs/:id` drives drilldown details. `/api/sync/status` remains a supporting live-status channel for trigger state and in-flight heartbeat. In parallel, follow `@superpowers:systematic-debugging` to reproduce, classify, and fix the failure causes currently inflating failed counts.

**Tech Stack:** React, Vite, Vitest, Flask, pytest, JSON store

---

### Task 1: Reproduce and classify current sync failures

**Files:**
- Modify: `backend/tests/test_sync.py`
- Modify: `backend/tests/test_sync_status.py`
- Reference: `backend/sync.py`
- Reference: `backend/sync_status.py`

**Step 1: Write the failing backend test for ambiguous successful Jobs with failures**

```python
def test_manual_sync_keeps_job_success_when_incremental_has_failed_items(tmp_path):
    from backend.storage import JsonStore
    from backend.sync_status import SyncCoordinator

    def incremental_runner(**_kwargs):
        return {
            "new_events": 2,
            "analyzed_events": 1,
            "failed_events": 3,
            "skipped_events": 5,
        }

    def daily_digest_runner(**_kwargs):
        return {"project_count": 2}

    coordinator = SyncCoordinator(
        incremental_runner=incremental_runner,
        daily_digest_runner=daily_digest_runner,
        store=JsonStore(tmp_path),
    )

    ok, _status = coordinator.start_manual_sync()
    assert ok is True

    final_status = coordinator.get_status()
    assert final_status["status"] == "success"
    assert final_status["result"]["incremental"]["failed_events"] == 3
```

**Step 2: Run test to verify it fails or exposes a different root cause**

Run: `python3 -m pytest backend/tests/test_sync_status.py -k ambiguous_success -v`
Expected: FAIL because the test does not yet reflect the real selected Job semantics or because the current status/run payload lacks the fields needed for classification.

**Step 3: Add a second failing test for source-level failure visibility**

```python
def test_run_detail_preserves_source_error_reason(tmp_path):
    from backend.storage import JsonStore
    from backend.sync_runs import SyncRunRecorder, load_runs

    store = JsonStore(tmp_path)
    recorder = SyncRunRecorder(store)
    run_id = recorder.start_run(run_kind="manual", started_at="2026-03-17T00:00:00Z")

    recorder.record_source(
        run_id,
        {
            "kind": "repo",
            "label": "broken/repo",
            "status": "failed",
            "metrics": {"new_events": 0, "analyzed_events": 0, "failed_events": 1, "skipped_events": 0},
            "error": "llm timeout",
            "events": [],
        },
    )

    payload = load_runs(store)
    assert payload["runs"][0]["sources"][0]["error"] == "llm timeout"
```

**Step 4: Run the focused tests**

Run: `python3 -m pytest backend/tests/test_sync.py backend/tests/test_sync_status.py -k "source_error_reason or ambiguous_success" -v`
Expected: At least one failure that clarifies what is missing in current behavior.

**Step 5: Implement the minimal backend fix informed by evidence**

- Preserve enough run/result metadata to distinguish:
  - Job failure
  - completed Job with failed items
  - source-level failure reasons
- Do not guess. Use the observed test failure to drive the exact change.

**Step 6: Re-run the focused tests**

Run: `python3 -m pytest backend/tests/test_sync.py backend/tests/test_sync_status.py -k "source_error_reason or ambiguous_success" -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/tests/test_sync.py backend/tests/test_sync_status.py backend/sync.py backend/sync_status.py backend/sync_runs.py
git commit -m "fix: classify sync job failures clearly"
```

### Task 2: Add a Job-centric view model in the frontend

**Files:**
- Modify: `src/App.jsx`
- Modify: `src/lib/api.js`
- Create: `src/lib/syncJobs.js`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing frontend test for selected Job priority**

```jsx
it("prefers the running job for the sync monitor primary card", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "同步监控" }));
  expect(await screen.findByText("当前 Job")).toBeInTheDocument();
  expect(screen.getByText("运行中")).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "prefers the running job"`
Expected: FAIL because the page still renders the old global status panel.

**Step 3: Write a small view-model helper**

Create `src/lib/syncJobs.js` with minimal helpers:

```js
export function selectPrimaryJob(runs) {
  return runs.find((run) => run.status === "running") || runs[0] || null;
}

export function jobDisplayState(run) {
  if (!run) return "idle";
  if (run.status === "failed") return "failed";
  if ((run.metrics?.failed_events ?? 0) > 0) return "completed_with_failures";
  if (run.status === "success") return "success";
  return run.status;
}
```

**Step 4: Load runs in `App.jsx` and keep the selected Job id in state**

- Fetch `/api/sync/runs` for the monitor page model.
- Keep `syncStatus` for trigger button and live updates.
- Store `selectedSyncRunId`.

**Step 5: Re-run the test**

Run: `npm test -- src/test/app.test.jsx -t "prefers the running job"`
Expected: PASS

**Step 6: Commit**

```bash
git add src/App.jsx src/lib/syncJobs.js src/test/app.test.jsx
git commit -m "feat: add sync job selection model"
```

### Task 3: Replace the monitor hero with a Current Job card and recent Jobs list

**Files:**
- Modify: `src/components/SyncMonitorPage.jsx`
- Modify: `src/components/SyncStatusPanel.jsx`
- Create: `src/components/SyncJobList.jsx`
- Test: `src/test/sync-status-panel.test.jsx`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing component test for completed Jobs with failed items**

```jsx
it("shows completed-with-failures copy for successful jobs with failed items", () => {
  render(
    <SyncStatusPanel
      run={{
        run_kind: "manual",
        status: "success",
        phase: "completed",
        message: "同步完成",
        metrics: { new_events: 0, analyzed_events: 0, failed_events: 14, skipped_events: 72, total_sources: 16, processed_sources: 16 },
      }}
    />,
  );

  expect(screen.getByText("已完成，含失败项")).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/sync-status-panel.test.jsx -t "completed-with-failures"`
Expected: FAIL because the component still expects `status` payload and current wording.

**Step 3: Implement the minimal component changes**

- `SyncMonitorPage` accepts:
  - `primaryRun`
  - `runs`
  - `selectedRunId`
  - `onSelectRun`
  - `onOpenLogs`
- `SyncStatusPanel` becomes a Job summary card, driven by a single run summary or detail payload.
- `SyncJobList` renders recent Jobs and selection state.

**Step 4: Re-run the focused component tests**

Run: `npm test -- src/test/sync-status-panel.test.jsx src/test/app.test.jsx -t "completed-with-failures|prefers the running job"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/components/SyncMonitorPage.jsx src/components/SyncStatusPanel.jsx src/components/SyncJobList.jsx src/test/sync-status-panel.test.jsx src/test/app.test.jsx
git commit -m "feat: redesign sync monitor around jobs"
```

### Task 4: Scope the log drawer to the selected Job

**Files:**
- Modify: `src/components/SyncLogDrawer.jsx`
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test for drawer scoping**

```jsx
it("opens logs for the selected job instead of defaulting to the newest run", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "同步监控" }));
  fireEvent.click(await screen.findByRole("button", { name: /历史 job/i }));
  fireEvent.click(screen.getByRole("button", { name: "查看日志" }));
  await screen.findByText("同步日志");
  expect(screen.getByText(/run_2026-03-10/)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "opens logs for the selected job"`
Expected: FAIL because the drawer currently resolves its own fallback run.

**Step 3: Implement the minimal fix**

- Pass `selectedRunId` into `SyncLogDrawer`.
- Use the selected Job as the primary detail target.
- Keep history tab behavior, but do not override the page-level selection on open.

**Step 4: Re-run the focused test**

Run: `npm test -- src/test/app.test.jsx -t "opens logs for the selected job"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/components/SyncLogDrawer.jsx src/test/app.test.jsx
git commit -m "fix: scope sync logs to selected job"
```

### Task 5: Investigate and fix the concrete sync failure source

**Files:**
- Modify: `backend/tests/test_sync.py`
- Modify: `backend/tests/test_api.py`
- Modify: `backend/sync.py`
- Modify: `backend/app.py`
- Reference: `backend/tests/test_sync_runs.py`

**Step 1: Write the failing regression test for the actual observed failure class**

Use the evidence gathered in Task 1. Choose one concrete reproduction:

- source fetch exception increments `failed_events` incorrectly
- analysis exception lacks actionable detail
- stale runs are selected as current
- timeouts are being counted as generic system failure

Example skeleton:

```python
def test_sync_run_failure_reason_is_exposed_in_api(tmp_path):
    from backend.app import create_app
    from backend.storage import JsonStore

    def sync_runner(**_kwargs):
        raise RuntimeError("upstream rate limited")

    app = create_app(store=JsonStore(tmp_path), sync_runner=sync_runner)
    client = app.test_client()

    client.post("/api/sync")
    payload = client.get("/api/sync/status").get_json()
    assert "rate limited" in payload["error"]
```

**Step 2: Run the targeted backend test**

Run: `python3 -m pytest backend/tests/test_sync.py backend/tests/test_api.py -k "failure_reason" -v`
Expected: FAIL with the exact missing behavior.

**Step 3: Implement only the fix that the failing test requires**

Examples:

- preserve source exception text in run detail
- avoid counting stale historical failures into the selected current Job
- classify timeout separately from orchestration failure

**Step 4: Re-run the targeted backend tests**

Run: `python3 -m pytest backend/tests/test_sync.py backend/tests/test_api.py -k "failure_reason" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/tests/test_sync.py backend/tests/test_api.py backend/sync.py backend/app.py
git commit -m "fix: surface actionable sync failure reasons"
```

### Task 6: Verification before completion

**Files:**
- Reference: `src/test/app.test.jsx`
- Reference: `src/test/sync-status-panel.test.jsx`
- Reference: `backend/tests/test_sync.py`
- Reference: `backend/tests/test_sync_status.py`
- Reference: `backend/tests/test_api.py`

**Step 1: Run frontend tests**

Run: `npm test -- src/test/app.test.jsx src/test/sync-status-panel.test.jsx`
Expected: PASS

**Step 2: Run backend sync-related tests**

Run: `python3 -m pytest backend/tests/test_sync.py backend/tests/test_sync_status.py backend/tests/test_api.py backend/tests/test_sync_runs.py -v`
Expected: PASS

**Step 3: Run the full test suite if practical**

Run: `python3 -m pytest backend/tests -v`
Run: `npm test`
Expected: PASS, or document any unrelated existing failures with evidence.

**Step 4: Smoke-check the app manually if the local environment is available**

Run: `npm run test -- --runInBand`
Expected: Core monitor flows remain green.

**Step 5: Commit**

```bash
git add src backend docs/plans
git commit -m "feat: ship sync job monitor and failure diagnosis"
```
