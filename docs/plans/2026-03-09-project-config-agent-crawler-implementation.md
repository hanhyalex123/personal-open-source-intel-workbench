# Project Config Agent Crawler Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a configurable project monitoring system where each project is defined by a GitHub URL and an official docs URL, with release analysis, agent-assisted docs discovery, daily drift checks, and a source-first dashboard UI.

**Architecture:** Extend the current Flask backend with project registry storage, crawl profiles, docs discovery and classification pipelines, and daily audit jobs. Replace the fixed-source frontend with a project-centric admin and dashboard experience that splits each project into `ReleaseNote 区` and `文档区`.

**Tech Stack:** Python 3, Flask, APScheduler, requests, feedparser, pytest, React 18, Vite 5, Vitest, Testing Library.

---

### Task 1: Introduce persistent project registry and crawl profile storage

**Files:**
- Modify: `backend/storage.py`
- Create: `backend/projects.py`
- Create: `backend/tests/test_projects.py`
- Modify: `backend/tests/test_storage.py`

**Step 1: Write the failing test**

Write tests that require:
- storing projects with `github_url` and `docs_url`
- storing editable crawl profiles
- default project config to be empty rather than hardcoded sources

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_projects.py backend/tests/test_storage.py -q`
Expected: FAIL because project registry helpers do not exist.

**Step 3: Write minimal implementation**

Implement:
- `projects.json`
- project CRUD helpers
- crawl profile persistence
- migration away from hardcoded default project lists

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_projects.py backend/tests/test_storage.py -q`
Expected: PASS.

### Task 2: Build docs discovery agent profile generation

**Files:**
- Create: `backend/discovery.py`
- Modify: `backend/llm.py`
- Modify: `backend/prompts.py`
- Create: `backend/tests/test_discovery.py`

**Step 1: Write the failing test**

Write tests that require:
- inferring crawl profile structure from docs home HTML
- extracting path allowlists and section hints
- storing discovery prompt output in a structured form

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_discovery.py -q`
Expected: FAIL because discovery helpers do not exist.

**Step 3: Write minimal implementation**

Implement:
- discovery prompt builder
- structured parser for discovery output
- initial crawl profile generation from docs URL

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_discovery.py -q`
Expected: PASS.

### Task 3: Replace single-page docs monitoring with section crawling

**Files:**
- Modify: `backend/sources.py`
- Create: `backend/docs_crawl.py`
- Create: `backend/tests/test_docs_crawl.py`

**Step 1: Write the failing test**

Write tests that require:
- traversing docs links from an entry page
- honoring allow / block rules from crawl profile
- extracting multiple page records with weak structure

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_docs_crawl.py -q`
Expected: FAIL because docs crawler does not exist.

**Step 3: Write minimal implementation**

Implement:
- link extraction
- bounded crawl by depth and prefix
- per-page weak record generation

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_docs_crawl.py -q`
Expected: PASS.

### Task 4: Add category aggregation for docs pages

**Files:**
- Create: `backend/docs_classify.py`
- Modify: `backend/llm.py`
- Create: `backend/tests/test_docs_classify.py`

**Step 1: Write the failing test**

Write tests that require:
- assigning docs pages to `网络 / 存储 / 调度 / 架构 / 安全 / 升级 / 运行时 / 可观测性`
- using rule-first classification with LLM fallback
- producing grouped docs insights instead of page-by-page summaries

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_docs_classify.py -q`
Expected: FAIL because docs categorization is missing.

**Step 3: Write minimal implementation**

Implement:
- rule-based classifier
- optional lightweight LLM fallback
- grouped docs insight model

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_docs_classify.py -q`
Expected: PASS.

### Task 5: Add daily drift audit and partial-failure resilience

**Files:**
- Modify: `backend/sync.py`
- Modify: `backend/runtime.py`
- Create: `backend/audit.py`
- Create: `backend/tests/test_audit.py`
- Modify: `backend/tests/test_sync.py`

**Step 1: Write the failing test**

Write tests that require:
- detecting missing pages and new navigation branches
- recording drift alerts
- continuing sync when a single project or single event fails

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_audit.py backend/tests/test_sync.py -q`
Expected: FAIL because audit tracking is missing.

**Step 3: Write minimal implementation**

Implement:
- daily audit job
- drift records
- per-project partial failure isolation

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_audit.py backend/tests/test_sync.py -q`
Expected: PASS.

### Task 6: Build admin APIs for project config and crawl profiles

**Files:**
- Modify: `backend/app.py`
- Create: `backend/tests/test_admin_api.py`

**Step 1: Write the failing test**

Write API tests for:
- listing projects
- creating a project with GitHub URL + docs URL
- reading and updating crawl profile
- listing audit alerts

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_admin_api.py -q`
Expected: FAIL because admin routes do not exist.

**Step 3: Write minimal implementation**

Implement:
- `/api/projects`
- `/api/projects/<id>`
- `/api/projects/<id>/crawl-profile`
- `/api/audit`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_admin_api.py -q`
Expected: PASS.

### Task 7: Redesign dashboard payload around project sections

**Files:**
- Modify: `backend/app.py`
- Modify: `backend/tests/test_api.py`

**Step 1: Write the failing test**

Require `/api/dashboard` to return:
- top-level overview
- per-project sections
- release area
- docs area grouped by technical category

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_api.py -q`
Expected: FAIL because payload is still source-first only.

**Step 3: Write minimal implementation**

Implement a project-centric dashboard serializer with:
- project headers
- release item groups
- docs category groups
- alert counts

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_api.py -q`
Expected: PASS.

### Task 8: Build frontend project admin and project-centric dashboard

**Files:**
- Modify: `src/App.jsx`
- Modify: `src/index.css`
- Modify: `src/lib/api.js`
- Modify: `src/components/InsightCard.jsx`
- Modify: `src/components/SourceSection.jsx`
- Create: `src/components/ProjectPanel.jsx`
- Create: `src/components/ProjectForm.jsx`
- Create: `src/components/DocsCategorySection.jsx`
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Write frontend tests that require:
- adding a project from GitHub URL + docs URL form
- rendering each project with `ReleaseNote 区` and optional `文档区`
- rendering docs grouped by category rather than as one homepage summary

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL because the current UI has no project admin or docs categories.

**Step 3: Write minimal implementation**

Implement:
- project config panel
- project cards
- release area
- docs category area
- audit badges and sync status

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS.

### Task 9: Update docs and verify end-to-end behavior

**Files:**
- Modify: `README.md`

**Step 1: Update docs**

Document:
- project creation flow
- GitHub URL + docs URL requirements
- crawl profile editing
- daily audit behavior
- project dashboard structure

**Step 2: Run verification**

Run: `python3 -m pytest backend/tests -q`
Run: `npm test`
Run: `npm run build`
Expected: all pass.
