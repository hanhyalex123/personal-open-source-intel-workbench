# Intel Workbench Phase 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Distinguish the intel and project monitoring pages, wire the AI console to a local assistant API, and manage assistant behavior through global config.

**Architecture:** Keep the existing single-shell app and button-based page switching, but split page content into dedicated components. Extend the Flask backend with assistant query/config endpoints backed by the existing JSON store so the frontend talks only to local APIs.

**Tech Stack:** React, Vitest, Flask, pytest, local JSON storage

---

### Task 1: Backend config API

**Files:**
- Modify: `backend/storage.py`
- Modify: `backend/app.py`
- Modify: `backend/tests/test_admin_api.py`

**Step 1: Write the failing test**

Require:
- `GET /api/config` returns assistant defaults
- `PUT /api/config` persists assistant settings

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_admin_api.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement:
- assistant defaults in config storage
- read/update config endpoints

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_admin_api.py -q`
Expected: PASS.

### Task 2: Backend assistant query API

**Files:**
- Modify: `backend/app.py`
- Create: `backend/tests/test_assistant.py`

**Step 1: Write the failing test**

Require:
- `POST /api/assistant/query`
- explicit filters for project/category/timeframe
- structured response with `answer`, `evidence`, `next_steps`, `sources`, `applied_filters`

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_assistant.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement:
- local retrieval from stored events/analyses
- basic query classification fallback
- structured answer assembly

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_assistant.py -q`
Expected: PASS.

### Task 3: Frontend AI console and configuration tests

**Files:**
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Require:
- `技术情报` and `项目监控` expose clearly different headings/content
- `AI 控制台` shows query input, filters, answer, evidence, sources
- `配置中心` shows assistant config form

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement the new UI and API calls.

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS.

### Task 4: Frontend page refactor and API wiring

**Files:**
- Create: `src/components/IntelOverviewPage.jsx`
- Create: `src/components/ProjectMonitorPage.jsx`
- Create: `src/components/AIConsolePage.jsx`
- Create: `src/components/SettingsPage.jsx`
- Modify: `src/App.jsx`
- Modify: `src/components/InsightCard.jsx`
- Modify: `src/index.css`
- Modify: `src/lib/api.js`

**Step 1: Implement page split**

Create dedicated components for each page and reduce `App.jsx` to shell/state orchestration.

**Step 2: Fix layout issues**

Change:
- intel page to summary/list layout
- project monitor to single-column project stream
- insight cards to avoid compressed multi-column overflow

**Step 3: Wire AI console**

Add:
- local query submission
- filter hydration from global config
- answer/evidence/source rendering

**Step 4: Run verification**

Run: `npm test`
Run: `npm run build`
Expected: PASS.
