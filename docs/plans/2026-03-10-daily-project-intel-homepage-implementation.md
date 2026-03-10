# Daily Project Intel Homepage Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the homepage as a daily AI-generated project intelligence summary page and add desktop start/stop launchers for local use.

**Architecture:** Keep the current Flask + React split, retain event-level ingestion and analysis, then add a project-level daily summary layer stored in local JSON. The homepage will consume project summary cards instead of a flat event timeline, and desktop `.command` scripts will manage local start/stop behavior through PID files.

**Tech Stack:** Python 3, Flask, APScheduler, requests, pytest, React 18, Vite 5, Vitest, Testing Library, macOS shell scripts.

---

### Task 1: Add failing backend tests for daily project summaries

**Files:**
- Modify: `backend/tests/test_api.py`
- Create: `backend/tests/test_daily_summary.py`

**Step 1: Write the failing test**

Require:
- a project-level daily summary builder
- homepage data returned from `/api/dashboard`
- fallback summary when a project has no new critical changes

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_daily_summary.py backend/tests/test_api.py -q`
Expected: FAIL because no daily summary layer exists yet.

**Step 3: Write minimal implementation**

Add test fixtures that exercise:
- one project with release and docs evidence
- one project with no same-day critical updates
- dashboard homepage ordering by importance

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_daily_summary.py backend/tests/test_api.py -q`
Expected: PASS.

### Task 2: Implement daily project summary storage and builder

**Files:**
- Modify: `backend/storage.py`
- Create: `backend/daily_summary.py`
- Modify: `backend/llm.py`
- Modify: `backend/prompts.py`
- Modify: `backend/app.py`

**Step 1: Write the failing test**

Require:
- `daily_project_summaries.json` storage support
- summary generation from existing `events + analyses`
- evidence trimming to 1-3 items

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_daily_summary.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement:
- store load/save for daily summaries
- prompt and parser for project daily summary generation
- fallback summary builder without LLM when evidence is thin
- dashboard payload field for homepage project cards

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_daily_summary.py backend/tests/test_api.py -q`
Expected: PASS.

### Task 3: Refresh daily summaries during sync

**Files:**
- Modify: `backend/runtime.py`
- Modify: `backend/sync.py`
- Modify: `backend/tests/test_runtime.py`

**Step 1: Write the failing test**

Require:
- sync to rebuild daily summaries once per day
- manual sync to refresh the current day when evidence changes

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_runtime.py -q`
Expected: FAIL because sync does not touch daily summaries.

**Step 3: Write minimal implementation**

Update the sync runner so it:
- completes event-level sync first
- then regenerates daily project summaries
- records summary refresh time in state

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_runtime.py -q`
Expected: PASS.

### Task 4: Redesign the homepage around project summary cards

**Files:**
- Modify: `src/components/IntelOverviewPage.jsx`
- Create: `src/components/ProjectSummaryCard.jsx`
- Modify: `src/App.jsx`
- Modify: `src/index.css`
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Require:
- homepage to show per-project AI summary cards
- each card to show summary text and 1-3 evidence entries
- old flat high-impact timeline to no longer be the homepage primary structure

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL.

**Step 3: Write minimal implementation**

Replace the current homepage sections with:
- lightweight header and sync status
- ordered project summary card list
- evidence snippets and project actions

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS.

### Task 5: Add desktop start/stop launchers

**Files:**
- Create: `scripts/start_intel_workbench.sh`
- Create: `scripts/stop_intel_workbench.sh`
- Create: `desktop/启动 Intel Workbench.command`
- Create: `desktop/停止 Intel Workbench.command`
- Modify: `README.md`

**Step 1: Write the failing test**

Require:
- launcher scripts to create PID files
- stop script to terminate tracked processes safely

**Step 2: Run test to verify it fails**

Run: `bash scripts/start_intel_workbench.sh --help`
Expected: FAIL because no launcher scripts exist yet.

**Step 3: Write minimal implementation**

Implement:
- backend start in background
- frontend start in background
- log directory and PID directory under project workspace
- browser open helper for local homepage
- stop script with idempotent cleanup

**Step 4: Run test to verify it passes**

Run: `bash scripts/start_intel_workbench.sh`
Expected: frontend and backend start, browser opens, PID files are written.

### Task 6: Verify end-to-end behavior

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

**Step 4: Verify launcher flow**

Run: `bash scripts/start_intel_workbench.sh`
Expected: backend and frontend become reachable locally.

**Step 5: Verify stop flow**

Run: `bash scripts/stop_intel_workbench.sh`
Expected: tracked processes stop and PID files are removed.
