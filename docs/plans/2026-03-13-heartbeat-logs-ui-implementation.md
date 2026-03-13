# Heartbeat + Logs UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the log button click behavior, add sync log storage + API + UI drilldown, unify the Radar action sizing, and prevent false “heartbeat timeout” during long analysis by adding a periodic heartbeat while a sync run is active.

**Architecture:** Add a lightweight heartbeat ticker thread in `SyncCoordinator` that updates `last_heartbeat_at` every 15s while status is `running`. Persist per-run sync logs in `backend/data/sync_runs.json` and expose list/detail/clear APIs. Wire log drawer state in `App` and pass `onOpenLogs`. Add minimal CSS for header actions alignment and consistent sizing between `pill` and `secondary-button`, plus log drawer styling.

**Tech Stack:** Flask/Python (backend), React (frontend), Vitest, Pytest

---

### Task 1: Add sync run storage (backend)

**Files:**
- Modify: `backend/storage.py`
- Create: `backend/sync_runs.py`
- Create: `backend/tests/test_sync_runs.py`

**Step 1: Write the failing test**

Create `backend/tests/test_sync_runs.py`:
```python
from pathlib import Path

from backend.storage import JsonStore
from backend.sync_runs import SyncRunRecorder, load_runs, save_runs


def test_sync_runs_round_trip(tmp_path: Path):
    store = JsonStore(tmp_path)
    save_runs(store, {"runs": []})
    assert load_runs(store)["runs"] == []


def test_sync_run_recorder_appends_and_trims(tmp_path: Path):
    store = JsonStore(tmp_path)
    recorder = SyncRunRecorder(store, retention=2)

    run1 = recorder.start_run(run_kind="manual", started_at="2026-03-13T00:00:00Z")
    run2 = recorder.start_run(run_kind="manual", started_at="2026-03-13T01:00:00Z")
    run3 = recorder.start_run(run_kind="manual", started_at="2026-03-13T02:00:00Z")

    runs = load_runs(store)["runs"]
    assert len(runs) == 2
    assert runs[0]["id"] == run3
    assert runs[1]["id"] == run2
```

**Step 2: Run test to verify it fails**

Run: `python3.12 -m pytest backend/tests/test_sync_runs.py -q`  
Expected: FAIL (module or functions missing)

**Step 3: Write minimal implementation**

Update `backend/storage.py`:
```python
    @property
    def sync_runs_path(self) -> Path:
        return self.base_dir / "sync_runs.json"

    def load_sync_runs(self) -> dict:
        return self._load_json(self.sync_runs_path, {"runs": []})

    def save_sync_runs(self, payload: dict) -> None:
        self._write_json(self.sync_runs_path, payload)
```

Create `backend/sync_runs.py`:
```python
import threading
from datetime import UTC, datetime


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_runs(store) -> dict:
    return store.load_sync_runs()


def save_runs(store, payload: dict) -> None:
    store.save_sync_runs(payload)


class SyncRunRecorder:
    def __init__(self, store, retention: int = 20):
        self.store = store
        self.retention = retention
        self._lock = threading.Lock()

    def start_run(self, *, run_kind: str, started_at: str | None = None) -> str:
        run_id = f"run_{(started_at or _now_iso())}_{run_kind}"
        run = {
            "id": run_id,
            "run_kind": run_kind,
            "status": "running",
            "phase": "queued",
            "message": "",
            "started_at": started_at or _now_iso(),
            "finished_at": None,
            "last_heartbeat_at": started_at or _now_iso(),
            "metrics": {
                "total_sources": 0,
                "processed_sources": 0,
                "new_events": 0,
                "analyzed_events": 0,
                "failed_events": 0,
            },
            "sources": [],
        }
        with self._lock:
            payload = load_runs(self.store)
            runs = payload.get("runs", [])
            runs.insert(0, run)
            payload["runs"] = runs[: self.retention]
            save_runs(self.store, payload)
        return run_id

    def update_run(self, run_id: str, **updates) -> None:
        with self._lock:
            payload = load_runs(self.store)
            for run in payload.get("runs", []):
                if run.get("id") == run_id:
                    run.update({k: v for k, v in updates.items() if v is not None})
                    break
            save_runs(self.store, payload)

    def record_source(self, run_id: str, source: dict) -> None:
        with self._lock:
            payload = load_runs(self.store)
            for run in payload.get("runs", []):
                if run.get("id") == run_id:
                    run.setdefault("sources", []).append(source)
                    metrics = run.setdefault("metrics", {})
                    metrics["processed_sources"] = metrics.get("processed_sources", 0) + 1
                    metrics["new_events"] = metrics.get("new_events", 0) + source.get("metrics", {}).get("new_events", 0)
                    metrics["analyzed_events"] = metrics.get("analyzed_events", 0) + source.get("metrics", {}).get("analyzed_events", 0)
                    metrics["failed_events"] = metrics.get("failed_events", 0) + source.get("metrics", {}).get("failed_events", 0)
                    break
            save_runs(self.store, payload)
```

**Step 4: Run test to verify it passes**

Run: `python3.12 -m pytest backend/tests/test_sync_runs.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add backend/storage.py backend/sync_runs.py backend/tests/test_sync_runs.py
git commit -m "feat: add sync run storage"
```

### Task 2: Add sync run APIs + status linkage

**Files:**
- Modify: `backend/app.py`
- Modify: `backend/sync_status.py`
- Modify: `backend/tests/test_api.py`
- Modify: `backend/tests/test_sync_status.py`

**Step 1: Write failing tests**

Add to `backend/tests/test_api.py`:
```python
def test_sync_runs_endpoints_list_detail_and_clear(client, store):
    from backend.sync_runs import SyncRunRecorder

    recorder = SyncRunRecorder(store)
    run_id = recorder.start_run(run_kind="manual", started_at="2026-03-13T00:00:00Z")

    resp = client.get("/api/sync/runs")
    assert resp.status_code == 200
    assert resp.get_json()[0]["id"] == run_id

    detail = client.get(f"/api/sync/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.get_json()["id"] == run_id

    cleared = client.delete("/api/sync/runs")
    assert cleared.status_code == 200
    assert cleared.get_json()["runs"] == []
```

Add to `backend/tests/test_sync_status.py`:
```python
def test_manual_sync_updates_run_id(client):
    resp = client.post("/api/sync")
    assert resp.status_code == 202
    payload = resp.get_json()
    assert payload.get("run_id")
```

**Step 2: Run tests to verify they fail**

Run:
- `python3.12 -m pytest backend/tests/test_api.py::test_sync_runs_endpoints_list_detail_and_clear -q`
- `python3.12 -m pytest backend/tests/test_sync_status.py::test_manual_sync_updates_run_id -q`

Expected: FAIL (endpoints missing / run_id missing)

**Step 3: Write minimal implementation**

In `backend/app.py` add:
- `GET /api/sync/runs` list
- `GET /api/sync/runs/<id>` detail
- `DELETE /api/sync/runs` clear

In `backend/sync_status.py`:
- include `run_id` in status (already in default), ensure manual sync sets it
- update run record when status changes

**Step 4: Run tests to verify they pass**

Run both tests again.

**Step 5: Commit**

```bash
git add backend/app.py backend/sync_status.py backend/tests/test_api.py backend/tests/test_sync_status.py
git commit -m "feat: add sync run api and status linkage"
```

### Task 3: Record per-source logs in sync pipeline

**Files:**
- Modify: `backend/sync.py`
- Modify: `backend/tests/test_sync.py`

**Step 1: Write failing tests**

Add to `backend/tests/test_sync.py`:
```python
def test_run_sync_once_records_event_logs(tmp_path):
    store = JsonStore(tmp_path)
    store.save_config({})
    recorder = SyncRunRecorder(store)
    run_id = recorder.start_run(run_kind="manual", started_at="2026-03-13T00:00:00Z")

    def release_fetcher(_repo):
        return [{"id": "r1", "name": "v1", "tag_name": "v1", "html_url": "https://example.com"}]

    def feed_fetcher(_feed):
        return []

    def analyzer(_event):
        return {"title_zh": "测试", "summary_zh": "摘要", "urgency": "low", "action_items": []}

    run_sync_once(
        store=store,
        repos=["example/repo"],
        feeds=[],
        release_fetcher=release_fetcher,
        feed_fetcher=feed_fetcher,
        analyzer=analyzer,
        now_iso="2026-03-13T00:00:00Z",
        run_logger=recorder,
        run_id=run_id,
    )

    payload = load_runs(store)
    assert payload["runs"][0]["sources"]
```

**Step 2: Run test to verify it fails**

Run: `python3.12 -m pytest backend/tests/test_sync.py::test_run_sync_once_records_event_logs -q`

Expected: FAIL (no source logs)

**Step 3: Write minimal implementation**

Update `backend/sync.py` to:
- capture `event_logs` per source
- call `run_logger.record_source(...)` after each source completes

**Step 4: Run test to verify it passes**

Run test again.

**Step 5: Commit**

```bash
git add backend/sync.py backend/tests/test_sync.py
git commit -m \"feat: record per-source event logs\"\n```\n\n### Task 4: Add failing backend test for heartbeat ticker\n@@\n **Step 5: Commit**\n@@\n git add backend/tests/test_sync_status.py backend/sync_status.py\n git commit -m \"fix: keep heartbeat alive during long sync runs\"\n@@\n-### Task 2: Add failing frontend test for log button and drawer\n+### Task 5: Add frontend log drawer + wiring\n@@\n-### Task 3: Add CSS to align Radar actions and sizes\n+### Task 6: Add CSS to align Radar actions and sizes + drawer styles\n@@\n-### Task 4: Start services and verify\n+### Task 7: Use localhost URLs for startup script\n+\n**Files:**\n- Modify: `scripts/start_intel_workbench.sh`\n- Create: `backend/tests/test_startup_script.py`\n+\n**Step 1: Write the failing test**\n+\nCreate `backend/tests/test_startup_script.py`:\n```python\nfrom pathlib import Path\n\n\ndef test_start_script_uses_localhost_urls():\n    repo_root = Path(__file__).resolve().parents[2]\n    script_path = repo_root / \"scripts\" / \"start_intel_workbench.sh\"\n    script = script_path.read_text(encoding=\"utf-8\")\n\n    assert 'BACKEND_URL=\"${INTEL_BACKEND_URL:-http://127.0.0.1:8000/api/health}\"' in script\n    assert 'FRONTEND_URL=\"${INTEL_FRONTEND_URL:-http://127.0.0.1:5173}\"' in script\n```\n\n**Step 2: Run test to verify it fails**\n\nRun: `python3.12 -m pytest backend/tests/test_startup_script.py -q`\n\nExpected: FAIL (script still uses `0.0.0.0` in URL defaults)\n\n**Step 3: Write minimal implementation**\n\nUpdate `scripts/start_intel_workbench.sh`:\n- Change `BACKEND_URL` default to `http://127.0.0.1:8000/api/health`\n- Change `FRONTEND_URL` default to `http://127.0.0.1:5173`\n- Update help/echo lines to show `127.0.0.1` for access\n- Keep `FRONTEND_CMD` host as `0.0.0.0`\n\n**Step 4: Run test to verify it passes**\n\nRun: `python3.12 -m pytest backend/tests/test_startup_script.py -q`\n\nExpected: PASS\n\n**Step 5: Commit**\n\n```bash\ngit add backend/tests/test_startup_script.py scripts/start_intel_workbench.sh\ngit commit -m \"fix: use localhost URLs in startup script\"\n```\n\n+### Task 8: Start services and verify\n@@\n Run: `bash scripts/start_intel_workbench.sh`\n*** End Patch"}Please respond with a JSON object containing only keys and values. Identified keys: ["done", "error"].}/* there is error in this tool usage from apply_patch. Need to redo. */"]}

**Files:**
- Modify: `backend/tests/test_sync_status.py`
- Modify: `backend/sync_status.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_sync_status.py`:
```python
import time


def test_heartbeat_ticker_updates_last_heartbeat():
    coordinator = SyncCoordinator(lambda **_: {}, lambda **_: {})
    ok, status = coordinator.start_manual_sync()
    assert ok
    first = status["last_heartbeat_at"]
    time.sleep(0.3)
    latest = coordinator.get_status()["last_heartbeat_at"]
    assert latest != first
```

**Step 2: Run test to verify it fails**

Run: `python3.12 -m pytest backend/tests/test_sync_status.py::test_heartbeat_ticker_updates_last_heartbeat -q`

Expected: FAIL (heartbeat timestamp does not change without progress)

**Step 3: Write minimal implementation**

In `backend/sync_status.py`:
- Add a heartbeat ticker thread that starts when status transitions to `running`
- Updates `last_heartbeat_at` every 0.2s in test mode or every 15s in production (use a small interval constant for tests to keep fast)
- Stop ticker when status is not `running`

**Step 4: Run test to verify it passes**

Run: `python3.12 -m pytest backend/tests/test_sync_status.py::test_heartbeat_ticker_updates_last_heartbeat -q`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/tests/test_sync_status.py backend/sync_status.py
git commit -m "fix: keep heartbeat alive during long sync runs"
```

### Task 2: Add failing frontend test for log button and drawer

**Files:**
- Modify: `src/test/app.test.jsx`
- Modify: `src/App.jsx`
- Modify: `src/components/SyncStatusPanel.jsx`

**Step 1: Write the failing test**

Extend `src/test/app.test.jsx` to mock `/api/sync/runs` and click the `日志` button to open drawer:
```jsx
const syncRunsPayload = [
  {
    id: "run_2026-03-10T04:10:00Z_manual",
    run_kind: "manual",
    status: "running",
    phase: "incremental",
    message: "正在抓取 GitHub releases",
    started_at: "2026-03-10T04:10:00Z",
    finished_at: null,
    last_heartbeat_at: "2026-03-10T04:10:10Z",
    metrics: { total_sources: 8, processed_sources: 1, new_events: 2, analyzed_events: 1, failed_events: 0 },
  },
];

const syncRunDetailPayload = {
  ...syncRunsPayload[0],
  sources: [],
};

// inside fetch mock:
if (String(url).includes("/api/sync/runs/") && !String(url).endsWith("/api/sync/runs")) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(syncRunDetailPayload) });
}
if (String(url).includes("/api/sync/runs")) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(syncRunsPayload) });
}

// in test body
fireEvent.click(screen.getByRole("button", { name: "日志" }));
await waitFor(() => {
  expect(screen.getByRole("dialog", { name: "同步日志" })).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- app.test.jsx`

Expected: FAIL (drawer not wired or log button no-op)

**Step 3: Write minimal implementation**

In `src/App.jsx`:
- Add `logDrawerOpen`, `logFilter` state
- Render `SyncLogDrawer` and pass `open`, `onClose`, `currentRunId`, `initialFilter`
- Pass `onOpenLogs` to `SyncStatusPanel`

**Step 4: Run test to verify it passes**

Run: `npm test -- app.test.jsx`

Expected: PASS

**Step 5: Commit**

```bash
git add src/App.jsx src/test/app.test.jsx
git commit -m "fix: wire sync log drawer open from radar"
```

### Task 3: Add CSS to align Radar actions and sizes

**Files:**
- Modify: `src/index.css`
- Modify: `src/components/SyncStatusPanel.jsx`

**Step 1: Write the failing test**

Add to `src/test/app.test.jsx`:
```jsx
const actions = document.querySelector(".sync-status-panel__actions");
expect(actions).not.toBeNull();
```

**Step 2: Run test to verify it fails**

Run: `npm test -- app.test.jsx`

Expected: FAIL if class is missing; PASS if present. (If already present, skip failure and just implement CSS.)

**Step 3: Write minimal implementation**

In `src/index.css`:
```css
.sync-status-panel__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sync-status-panel__actions .pill {
  padding: 8px 14px;
  font-size: 12px;
}
```

**Step 4: Run test to verify it passes**

Run: `npm test -- app.test.jsx`

Expected: PASS

**Step 5: Commit**

```bash
git add src/index.css
git commit -m "fix: align radar actions"
```

### Task 4: Start services and verify

**Step 1: Start services**

Run: `bash scripts/start_intel_workbench.sh`

**Step 2: Verify access**

- Open: `http://127.0.0.1:5173`
- Check health: `curl -fsS http://127.0.0.1:8000/api/health`

Expected: Frontend loads and backend returns JSON.
