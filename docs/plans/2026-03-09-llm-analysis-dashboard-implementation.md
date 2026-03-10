# LLM Analysis Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the current raw GitHub dashboard into a Chinese insight dashboard backed by a lightweight Python service that fetches, analyzes, stores, and serves stable LLM summaries.

**Architecture:** Add a small Flask backend with local JSON persistence and an in-process scheduler. The backend normalizes upstream release and docs events, deduplicates them, analyzes only new items with the configured LLM endpoint, and serves ready-made Chinese results to a refreshed React frontend.

**Tech Stack:** Python 3, Flask, APScheduler, requests, pytest, React 18, Vite 5, Tailwind CSS 3, Vitest, Testing Library.

---

### Task 1: Scaffold the Python backend and persistence layout

**Files:**
- Create: `backend/app.py`
- Create: `backend/config.py`
- Create: `backend/storage.py`
- Create: `backend/models.py`
- Create: `backend/scheduler.py`
- Create: `backend/__init__.py`
- Create: `backend/data/.gitkeep`
- Create: `requirements.txt`
- Test: `backend/tests/test_storage.py`

**Step 1: Write the failing test**

Create a storage test that expects JSON files to initialize with empty default structures and round-trip records safely.

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_storage.py -q`
Expected: FAIL because backend modules do not exist.

**Step 3: Write minimal implementation**

Implement file-based storage helpers for:
- loading defaults when files do not exist
- writing JSON atomically
- reading and updating events, analyses, and state

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_storage.py -q`
Expected: PASS.

### Task 2: Add upstream normalization and dedupe rules

**Files:**
- Create: `backend/sources.py`
- Create: `backend/normalize.py`
- Test: `backend/tests/test_normalize.py`

**Step 1: Write the failing test**

Write tests for:
- GitHub release normalization into stable event ids
- docs feed normalization into stable event ids
- content hash generation
- dedupe behavior for repeated inputs

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_normalize.py -q`
Expected: FAIL because normalization code is missing.

**Step 3: Write minimal implementation**

Implement source fetch adapters and normalized event mapping with stable ids and content hashes.

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_normalize.py -q`
Expected: PASS.

### Task 3: Add LLM analysis client and prompt contract

**Files:**
- Create: `backend/llm.py`
- Create: `backend/prompts.py`
- Test: `backend/tests/test_llm_parsing.py`

**Step 1: Write the failing test**

Write tests for:
- prompt rendering containing required Chinese analysis instructions
- parsing structured JSON analysis output
- preserving stable conclusion flags

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_llm_parsing.py -q`
Expected: FAIL because the LLM helper does not exist.

**Step 3: Write minimal implementation**

Implement:
- environment-based API configuration
- prompt template builder
- response parser for structured JSON output
- safe error handling for malformed model output

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_llm_parsing.py -q`
Expected: PASS.

### Task 4: Build the sync pipeline and scheduled refresh

**Files:**
- Create: `backend/sync.py`
- Modify: `backend/scheduler.py`
- Test: `backend/tests/test_sync.py`

**Step 1: Write the failing test**

Write tests for:
- new events being analyzed and stored
- existing stable events being skipped
- changed hashes triggering reanalysis
- sync state being updated

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_sync.py -q`
Expected: FAIL because sync orchestration is missing.

**Step 3: Write minimal implementation**

Implement:
- end-to-end sync orchestration
- dedupe checks
- analysis-on-new-only flow
- background scheduler startup and interval config

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_sync.py -q`
Expected: PASS.

### Task 5: Expose backend HTTP APIs

**Files:**
- Modify: `backend/app.py`
- Test: `backend/tests/test_api.py`

**Step 1: Write the failing test**

Write API tests for:
- dashboard overview endpoint
- grouped analysis feed endpoint
- manual sync trigger endpoint
- health endpoint

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_api.py -q`
Expected: FAIL because API routes are incomplete.

**Step 3: Write minimal implementation**

Implement JSON endpoints that return frontend-ready data with grouped Chinese analysis records.

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_api.py -q`
Expected: PASS.

### Task 6: Replace the current frontend with a Chinese insight UI

**Files:**
- Modify: `src/App.jsx`
- Modify: `src/index.css`
- Create: `src/lib/api.js`
- Create: `src/components/InsightCard.jsx`
- Create: `src/components/SourceSection.jsx`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Write frontend tests that assert:
- the page renders Chinese summary cards from backend data
- stable conclusions are labeled clearly
- detailed explanation is visible or expandable
- source metadata and sync status are shown

**Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand`
Expected: FAIL because the new UI and test runner setup are missing.

**Step 3: Write minimal implementation**

Replace the raw three-column activity layout with:
- hero summary
- important changes feed
- grouped source sections
- Chinese detail cards
- sync actions and status

**Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand`
Expected: PASS.

### Task 7: Add frontend test tooling and backend run scripts

**Files:**
- Modify: `package.json`
- Modify: `vite.config.js`
- Create: `vitest.config.js`
- Create: `backend/tests/conftest.py`

**Step 1: Write the failing test**

Add the missing script and config expectations by attempting to run the frontend tests.

**Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand`
Expected: FAIL because test tooling is not configured.

**Step 3: Write minimal implementation**

Add:
- Vitest scripts
- jsdom test config
- backend pytest config if needed

**Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand`
Expected: PASS.

### Task 8: Add docs, sample env setup, and final verification

**Files:**
- Modify: `README.md`
- Create: `.env.example`

**Step 1: Update docs**

Document:
- backend startup
- scheduler behavior
- model env vars
- local JSON persistence layout
- manual sync commands

**Step 2: Run verification**

Run: `python -m pytest backend/tests -q`
Run: `npm test -- --runInBand`
Run: `npm run build`
Expected: all pass.
