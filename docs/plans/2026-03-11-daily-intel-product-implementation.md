# Daily Intel Product Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the intelligence pipeline into hourly incremental updates plus a daily digest product with digest history.

**Architecture:** Keep event-level ingestion and analysis, then introduce separate view-model layers for hourly incremental project updates and daily digest summaries. The scheduler will run two jobs in Asia/Shanghai time: an hourly incremental sync that updates project monitoring and incremental alerts, and a daily digest job that freezes homepage summaries and appends digest history.

**Tech Stack:** Python 3, Flask, APScheduler, requests, pytest, React 18, Vite 5, Vitest, Testing Library.

---

### Task 1: Add failing backend tests for split refresh semantics

**Files:**
- Modify: `backend/tests/test_runtime.py`
- Modify: `backend/tests/test_api.py`
- Create: `backend/tests/test_digest_history.py`

**Step 1: Write the failing test**

Require:
- hourly sync updates fetch and incremental-analysis timestamps
- daily digest updates digest timestamp and history
- dashboard returns daily digest cards, incremental updates, and digest history separately

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_runtime.py backend/tests/test_api.py backend/tests/test_digest_history.py -q`
Expected: FAIL because the current runtime only has one job and one digest layer.

**Step 3: Write minimal implementation**

Define expected payloads for:
- `recent_project_updates`
- `daily_digest_history`
- scheduler job status fields

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_runtime.py backend/tests/test_api.py backend/tests/test_digest_history.py -q`
Expected: PASS.

### Task 2: Split runtime into hourly incremental and daily digest jobs

**Files:**
- Modify: `backend/runtime.py`
- Modify: `backend/scheduler.py`
- Modify: `backend/server.py`
- Modify: `backend/storage.py`

**Step 1: Write the failing test**

Require:
- separate incremental and daily digest callbacks
- Asia/Shanghai daily scheduling
- heartbeat and real last-success timestamps

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_runtime.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**

Add:
- `build_incremental_sync_runner`
- `build_daily_digest_runner`
- scheduler with interval + cron jobs
- state fields for fetch, incremental analysis, digest, heartbeat

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_runtime.py -q`
Expected: PASS.

### Task 3: Add digest history and incremental view models

**Files:**
- Create: `backend/digest_history.py`
- Modify: `backend/daily_summary.py`
- Modify: `backend/app.py`
- Modify: `backend/tests/test_api.py`

**Step 1: Write the failing test**

Require:
- digest history persisted by date
- hourly updates excluded from frozen daily digest cards
- recent incremental updates exposed separately

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_api.py backend/tests/test_digest_history.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement:
- digest history storage and retrieval
- incremental updates builder
- dashboard payload split into daily digest, incremental updates, history

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_api.py backend/tests/test_digest_history.py -q`
Expected: PASS.

### Task 4: Redesign the homepage as a daily digest product

**Files:**
- Modify: `src/components/IntelOverviewPage.jsx`
- Create: `src/components/DailyDigestHistory.jsx`
- Create: `src/components/IncrementalUpdateList.jsx`
- Modify: `src/test/app.test.jsx`
- Modify: `src/index.css`

**Step 1: Write the failing test**

Require:
- homepage sections for daily digest, incremental updates, and history
- no ambiguity between “last sync” and “last digest”
- clear stale/heartbeat messaging hooks

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL.

**Step 3: Write minimal implementation**

Render:
- today digest cards
- incremental updates since digest
- digest history date list

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS.

### Task 5: Verify end-to-end behavior

**Files:**
- Modify: `README.md`

**Step 1: Run backend tests**

Run: `python3 -m pytest backend/tests -q`
Expected: PASS.

**Step 2: Run frontend tests**

Run: `npm test`
Expected: PASS.

**Step 3: Run production build**

Run: `npm run build`
Expected: PASS.
