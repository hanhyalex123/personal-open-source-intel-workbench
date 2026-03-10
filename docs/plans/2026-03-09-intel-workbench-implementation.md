# Intel Workbench Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert the current dashboard into a multi-page intelligence workbench with project monitoring, docs category aggregation, a project knowledge assistant, and a real configuration center.

**Architecture:** Keep the Flask + React split, but add a routed shell in the frontend and explicit backend support for project knowledge retrieval, docs category aggregation, and assistant queries. The UI will move from a single scroll page to a left-nav workbench with dedicated pages for `技术情报`, `项目监控`, `AI 控制台`, and `配置中心`.

**Tech Stack:** Python 3, Flask, requests, APScheduler, pytest, React 18, Vite 5, Vitest, Testing Library.

---

### Task 1: Introduce routed workbench shell

**Files:**
- Modify: `src/App.jsx`
- Create: `src/components/WorkbenchShell.jsx`
- Create: `src/components/SidebarNav.jsx`
- Modify: `src/index.css`
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Require the UI to render:
- left sidebar nav
- page tabs / routes for `技术情报`, `项目监控`, `AI 控制台`, `配置中心`

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL because the app is still a single-page layout.

**Step 3: Write minimal implementation**

Add:
- sidebar shell
- internal route state
- top header per page

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS.

### Task 2: Professionalize homepage / intelligence landing

**Files:**
- Modify: `src/App.jsx`
- Create: `src/components/IntelOverviewPage.jsx`
- Modify: `src/index.css`

**Step 1: Write the failing test**

Require the default landing page to show:
- professional title
- current scope / counts
- high-impact summary blocks
- no slogan-like marketing copy

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL.

**Step 3: Write minimal implementation**

Replace the hero messaging with:
- product identity
- data status
- concise professional explanatory text

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS.

### Task 3: Split project monitoring into dedicated page components

**Files:**
- Create: `src/components/ProjectMonitorPage.jsx`
- Create: `src/components/ProjectPanel.jsx`
- Modify: `src/components/InsightCard.jsx`
- Modify: `src/index.css`

**Step 1: Write the failing test**

Require:
- `项目监控` page entry
- project sections with `ReleaseNote 区` and `文档区`
- latest three items visible by default
- expand controls for history

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL.

**Step 3: Write minimal implementation**

Extract the current project monitoring area into dedicated page-level components and preserve compact cards.

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS.

### Task 4: Build assistant retrieval backend

**Files:**
- Create: `backend/assistant.py`
- Create: `backend/tests/test_assistant.py`
- Modify: `backend/app.py`

**Step 1: Write the failing test**

Require:
- assistant query endpoint
- query classification by project / category / timeframe
- retrieval from structured results and docs snippets

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_assistant.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement:
- `/api/assistant/query`
- basic retrieval from release/doc knowledge
- structured response with `answer`, `evidence`, `next_steps`, `sources`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_assistant.py -q`
Expected: PASS.

### Task 5: Build AI console page

**Files:**
- Create: `src/components/AIConsolePage.jsx`
- Modify: `src/lib/api.js`
- Modify: `src/test/app.test.jsx`
- Modify: `src/index.css`

**Step 1: Write the failing test**

Require:
- `AI 控制台` page
- query input
- answer block
- evidence / source panel

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement the assistant UI as a project knowledge helper, not a code execution console.

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS.

### Task 6: Expand configuration center

**Files:**
- Create: `src/components/SettingsPage.jsx`
- Modify: `src/lib/api.js`
- Modify: `backend/app.py`
- Modify: `backend/tests/test_admin_api.py`

**Step 1: Write the failing test**

Require:
- crawl profile inspection
- crawl profile update
- prompts visibility

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_admin_api.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**

Expose:
- project list
- crawl profile editor
- prompt editor
- sync status

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_admin_api.py -q`
Expected: PASS.

### Task 7: Improve docs category quality and reduce `其他`

**Files:**
- Modify: `backend/docs_classify.py`
- Modify: `backend/docs_crawl.py`
- Modify: `backend/tests/test_docs_classify.py`
- Modify: `backend/tests/test_docs_crawl.py`

**Step 1: Write the failing test**

Require better separation for:
- 网络
- 存储
- 调度
- 架构
- 升级
- 运行时

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_docs_classify.py backend/tests/test_docs_crawl.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**

Improve:
- title weighting
- path weighting
- nav noise filtering
- shallow category landing pages

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_docs_classify.py backend/tests/test_docs_crawl.py -q`
Expected: PASS.

### Task 8: Final integration and verification

**Files:**
- Modify: `README.md`

**Step 1: Update docs**

Document:
- multi-page workbench structure
- AI console purpose
- project config center
- assistant query flow

**Step 2: Run verification**

Run: `python3 -m pytest backend/tests -q`
Run: `npm test`
Run: `npm run build`
Expected: all pass.
