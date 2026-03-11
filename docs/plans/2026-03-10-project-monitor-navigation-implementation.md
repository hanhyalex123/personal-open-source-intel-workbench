# Project Monitor Navigation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a sticky right-side navigator to the project monitor page, strengthen per-project visual separation, and fix the related homepage/startup review findings.

**Architecture:** Keep the current React page structure but add stable per-project anchor ids, a lightweight outline component, and a small project theme map shared by homepage and project monitor cards. Backend changes stay limited to homepage summary freshness/sorting and startup script process verification.

**Tech Stack:** Python 3, Flask, pytest, React 18, Vite 5, Vitest, shell scripts.

---

### Task 1: Fix stale homepage summary behavior

**Files:**
- Modify: `backend/daily_summary.py`
- Modify: `backend/app.py`
- Modify: `backend/tests/test_daily_summary.py`
- Modify: `backend/tests/test_api.py`

**Step 1: Write the failing test**

Require:
- freshest known date wins over stale `last_daily_summary_at`
- homepage cards are re-sorted after backfilling generated summaries

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_daily_summary.py backend/tests/test_api.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**

Use the newest date from summary state, sync state, or event timestamps, then sort merged homepage cards by importance and freshness.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_daily_summary.py backend/tests/test_api.py -q`
Expected: PASS.

### Task 2: Harden launcher success checks

**Files:**
- Modify: `scripts/start_intel_workbench.sh`
- Create: `backend/tests/test_start_script.py`

**Step 1: Write the failing test**

Require:
- startup fails when the launched child exits immediately even if the port is already occupied by another process

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_start_script.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**

Verify:
- tracked child pid is still running
- process is not zombie
- child survives a short stability window after readiness probe

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_start_script.py -q`
Expected: PASS.

### Task 3: Add project-level themes and sticky navigator

**Files:**
- Create: `src/lib/projectTheme.js`
- Modify: `src/components/ProjectSummaryCard.jsx`
- Modify: `src/components/ProjectMonitorPage.jsx`
- Modify: `src/index.css`
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Require:
- per-project `data-project-id` hooks
- right-side “快速定位” navigator with project and subsection links

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL.

**Step 3: Write minimal implementation**

Add:
- per-project theme tokens
- sticky outline navigator
- anchor ids for project, release, and docs categories
- mobile fallback for the navigator

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS.

### Task 4: Verify end-to-end

**Files:**
- No additional files

**Step 1: Run backend tests**

Run: `python3 -m pytest backend/tests -q`
Expected: PASS.

**Step 2: Run frontend tests**

Run: `npm test`
Expected: PASS.

**Step 3: Run production build**

Run: `npm run build`
Expected: PASS.
