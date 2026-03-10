# Source-First Doc Enrichment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the dashboard so it renders structured Chinese insights instead of raw markdown text, and strengthen project-source monitoring by treating official docs/blog sources as first-class inputs.

**Architecture:** Keep the existing Flask + React split, but enrich feed sources with optional linked-page expansion, add source summaries to the dashboard API, and normalize analysis output into structured sections and bullets. The frontend will pivot to a source-first layout with cleaner rendering for long-form insights.

**Tech Stack:** Python 3, Flask, requests, feedparser, pytest, React 18, Vite 5, Vitest, Testing Library.

---

### Task 1: Add structured analysis formatting and legacy fallback

**Files:**
- Modify: `backend/llm.py`
- Modify: `backend/prompts.py`
- Modify: `backend/tests/test_llm_parsing.py`

**Step 1: Write the failing test**
- Require the prompt to request structured sections and bullet arrays.
- Require parser fallback that repairs legacy markdown-ish strings into structured fields.

**Step 2: Run test to verify it fails**
- Run: `python3 -m pytest backend/tests/test_llm_parsing.py -q`
- Expected: FAIL.

**Step 3: Write minimal implementation**
- Parse or derive `detail_sections`, `impact_points`, and `action_items`.
- Preserve backward compatibility for existing cached records.

**Step 4: Run test to verify it passes**
- Run: `python3 -m pytest backend/tests/test_llm_parsing.py -q`
- Expected: PASS.

### Task 2: Enrich official docs/blog feed sources

**Files:**
- Modify: `backend/sources.py`
- Modify: `backend/storage.py`
- Modify: `backend/tests/test_sources.py`
- Modify: `backend/tests/test_storage.py`

**Step 1: Write the failing test**
- Require feed sources to support optional linked-page expansion.
- Require default config to include official Kubernetes blog feed.

**Step 2: Run test to verify it fails**
- Run: `python3 -m pytest backend/tests/test_sources.py backend/tests/test_storage.py -q`
- Expected: FAIL.

**Step 3: Write minimal implementation**
- Add a `k8s-blog` feed source.
- For selected feeds, fetch the linked page and append cleaned article text into the event body.

**Step 4: Run test to verify it passes**
- Run: `python3 -m pytest backend/tests/test_sources.py backend/tests/test_storage.py -q`
- Expected: PASS.

### Task 3: Add source summaries to the dashboard API

**Files:**
- Modify: `backend/app.py`
- Modify: `backend/tests/test_api.py`

**Step 1: Write the failing test**
- Require `/api/dashboard` to return source-level summary cards and structured item fields.

**Step 2: Run test to verify it fails**
- Run: `python3 -m pytest backend/tests/test_api.py -q`
- Expected: FAIL.

**Step 3: Write minimal implementation**
- Add `sources` to the API payload.
- Format analysis records for UI use.

**Step 4: Run test to verify it passes**
- Run: `python3 -m pytest backend/tests/test_api.py -q`
- Expected: PASS.

### Task 4: Rewrite the frontend to render source-first structured cards

**Files:**
- Modify: `src/App.jsx`
- Modify: `src/components/InsightCard.jsx`
- Modify: `src/components/SourceSection.jsx`
- Modify: `src/index.css`
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**
- Require a source summary strip.
- Require section bullet rendering without raw markdown markers.

**Step 2: Run test to verify it fails**
- Run: `npm test`
- Expected: FAIL.

**Step 3: Write minimal implementation**
- Render sources overview.
- Render detail sections, impact points, and action items as lists.
- Improve layout to handle more sources cleanly.

**Step 4: Run test to verify it passes**
- Run: `npm test`
- Expected: PASS.

### Task 5: Verify the integrated result

**Files:**
- Modify: `README.md`

**Step 1: Update docs**
- Explain source-first monitoring and official docs/blog enrichment.

**Step 2: Run verification**
- Run: `python3 -m pytest backend/tests -q`
- Run: `npm test`
- Run: `npm run build`
- Expected: all pass.
