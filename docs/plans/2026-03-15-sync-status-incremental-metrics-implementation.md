# Sync Status Incremental Metrics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the homepage “本次合计（全来源）” always show the latest incremental sync summary (including skipped), even when the current phase is daily digest.

**Architecture:** Persist a `last_incremental_metrics` summary in the sync status payload after each incremental run. The UI reads this stable summary for totals, while phase/progress remain live.

**Tech Stack:** Flask backend, React frontend, Vitest, Pytest

---

### Task 1: Backend — expose `last_incremental_metrics`

**Files:**
- Modify: `backend/tests/test_sync_status.py`
- Modify: `backend/sync_status.py`

**Step 1: Write the failing test**

Update the manual sync test to assert `last_incremental_metrics` after completion:

```python
# backend/tests/test_sync_status.py
    assert payload["phase"] == "completed"
    assert payload["result"]["incremental"]["new_events"] == 2
    assert payload["result"]["daily_digest"]["summary_count"] == 8
    assert payload["last_incremental_metrics"]["new_events"] == 2
    assert payload["last_incremental_metrics"]["analyzed_events"] == 1
    assert payload["last_incremental_metrics"]["failed_events"] == 0
    assert payload["last_incremental_metrics"]["skipped_events"] == 5
```

Optional (if you want explicit scheduled incremental coverage), add a new test:

```python
def test_scheduled_incremental_sets_last_incremental_metrics(tmp_path):
    from backend.app import create_app
    from backend.storage import JsonStore

    def ok_runner(*, progress_callback=None):
        return {"new_events": 3, "analyzed_events": 2, "failed_events": 0, "skipped_events": 4}

    app = create_app(store=JsonStore(tmp_path), sync_runner=ok_runner)
    coordinator = app.config["SYNC_COORDINATOR"]

    coordinator.run_scheduled_incremental()
    status = coordinator.get_status()

    assert status["last_incremental_metrics"]["new_events"] == 3
    assert status["last_incremental_metrics"]["skipped_events"] == 4
```

**Step 2: Run test to verify it fails**

Run:

```bash
../../.venv/bin/python -m pytest -q backend/tests/test_sync_status.py
```

Expected: FAIL (missing `last_incremental_metrics`).

**Step 3: Write minimal implementation**

Update sync status to preserve previous summary and set it when incremental completes.

```python
# backend/sync_status.py

def default_sync_status() -> dict:
    return {
        ...,
        "skipped_events": 0,
        "last_incremental_metrics": None,
        "error": "",
        "result": {},
    }

class SyncCoordinator:
    def start_manual_sync(self) -> tuple[bool, dict]:
        with self._lock:
            if self._status["status"] == "running":
                return False, deepcopy(self._status)

            previous_incremental = self._status.get("last_incremental_metrics")
            started_at = now_iso()
            run_id = self._start_run("manual", started_at=started_at)
            initial_status = {
                **default_sync_status(),
                "last_incremental_metrics": previous_incremental,
                "run_id": run_id,
                "status": "running",
                "run_kind": "manual",
                "phase": "queued",
                "message": "同步任务已开始",
                "started_at": started_at,
                "last_heartbeat_at": started_at,
            }
            self._status = initial_status
        ...

    def _build_incremental_metrics(self, result: dict, *, finished_at: str) -> dict:
        return {
            "new_events": result.get("new_events", 0),
            "analyzed_events": result.get("analyzed_events", 0),
            "failed_events": result.get("failed_events", 0),
            "skipped_events": result.get("skipped_events", 0),
            "total_sources": self._status.get("total_sources", 0),
            "processed_sources": self._status.get("processed_sources", 0),
            "finished_at": finished_at,
        }

    def run_scheduled_incremental(self) -> dict:
        ...
        try:
            result = self._invoke_runner(...)
            finished_at = now_iso()
            self._set_status(
                status="success",
                phase="completed",
                message="定时增量同步完成",
                finished_at=finished_at,
                last_incremental_metrics=self._build_incremental_metrics(result, finished_at=finished_at),
                result={"incremental": result},
            )
            return result
        ...

    def _run_manual_sync(self) -> None:
        ...
        try:
            ...
            incremental_result = self._invoke_runner(...)
            finished_at = now_iso()
            self._set_status(
                phase="daily_digest",
                message="正在生成今日日报",
                last_incremental_metrics=self._build_incremental_metrics(incremental_result, finished_at=finished_at),
                result={"incremental": incremental_result},
            )
            ...
```

**Step 4: Run test to verify it passes**

Run:

```bash
../../.venv/bin/python -m pytest -q backend/tests/test_sync_status.py
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/sync_status.py backend/tests/test_sync_status.py
git commit -m "Add last incremental metrics to sync status"
```

---

### Task 2: Frontend — use `last_incremental_metrics` for totals

**Files:**
- Modify: `src/components/SyncStatusPanel.jsx`
- Modify: `src/test/sync-status-panel.test.jsx`
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Make test data include a different `last_incremental_metrics` so the UI must prefer it:

```jsx
// src/test/sync-status-panel.test.jsx
const status = {
  status: "success",
  ...,
  new_events: 1,
  analyzed_events: 1,
  failed_events: 0,
  skipped_events: 0,
  last_incremental_metrics: {
    new_events: 9,
    analyzed_events: 7,
    failed_events: 1,
    skipped_events: 4,
    total_sources: 26,
    processed_sources: 26,
    finished_at: "2026-03-15T02:31:00Z",
  },
};

expect(screen.getByRole("button", { name: "新增" })).toHaveTextContent("9");
expect(screen.getByRole("button", { name: "已分析" })).toHaveTextContent("7");
expect(screen.getByRole("button", { name: "失败" })).toHaveTextContent("1");
expect(screen.getByRole("button", { name: "跳过" })).toHaveTextContent("4");
```

Update `src/test/app.test.jsx` syncStatus payload similarly (ensure the UI reflects `last_incremental_metrics`).

**Step 2: Run test to verify it fails**

Run:

```bash
npm test -- src/test/sync-status-panel.test.jsx
```

Expected: FAIL (still using status-level metrics).

**Step 3: Write minimal implementation**

```jsx
// src/components/SyncStatusPanel.jsx
const summary = status.last_incremental_metrics || null;
const summaryNew = summary ? summary.new_events : status.new_events;
const summaryAnalyzed = summary ? summary.analyzed_events : status.analyzed_events;
const summaryFailed = summary ? summary.failed_events : status.failed_events;
const summarySkipped = summary ? summary.skipped_events : skippedEvents;

const skippedEvents = summary ? summary.skipped_events ?? 0 : status.skipped_events ?? 0;
const totalNote = `本次合计（全来源）${!summaryNew && !summaryAnalyzed && !summaryFailed && skippedEvents ? " · 无新增变化" : ""}`;

// use summaryNew/summaryAnalyzed/summaryFailed/skippedEvents in the tiles
```

**Step 4: Run tests to verify they pass**

Run:

```bash
npm test -- src/test/sync-status-panel.test.jsx
npm test -- src/test/app.test.jsx
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/components/SyncStatusPanel.jsx src/test/sync-status-panel.test.jsx src/test/app.test.jsx
git commit -m "Use last incremental metrics for sync totals"
```

---

### Task 3: Regression smoke checks

**Files:**
- None (verification only)

**Step 1: Backend smoke test**

```bash
../../.venv/bin/python -m pytest -q backend/tests/test_sync_status.py
```

Expected: PASS.

**Step 2: Frontend smoke test**

```bash
npm test -- src/test/app.test.jsx
```

Expected: PASS.

---

## Notes
- If `npm install` fails with EACCES, clear or fix npm cache permissions before running frontend tests.
- The UI still shows live phase/progress; only totals are sourced from `last_incremental_metrics`.
