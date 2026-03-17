# Docs Workbench Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild `文档台` into a page-first workspace that shows recent document changes, detailed interpretation, and a handoff into deep research.

**Architecture:** Keep the existing React page and docs APIs, but invert the UI from event-first to page-first. The selected page becomes the primary state, event data is used as related context, and page details render in fixed interpretation sections with a local `深读` expansion and a `去研究` handoff.

**Tech Stack:** React, Vite, Testing Library, existing `/api/docs/*` frontend API helpers, CSS in `src/index.css`

---

### Task 1: Lock the new docs workbench behavior with tests

**Files:**
- Modify: `src/test/app.test.jsx`
- Inspect: `src/components/DocsWorkbenchPage.jsx`

**Step 1: Write the failing test**

Add tests that assert:
- the main list renders pages as the default primary list
- selecting a page shows `变化 / 影响 / 建议 / diff`
- a page with no related event still renders page content instead of the empty event prompt
- `深读` expands more analysis content
- `去研究` is rendered with the selected page context

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench"`
Expected: FAIL because the current UI is event-first and has no `深读` / `去研究` flow.

**Step 3: Write minimal implementation**

Update `src/components/DocsWorkbenchPage.jsx` test hooks and structure only enough for the new tests to locate the page-first layout.

**Step 4: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/test/app.test.jsx src/components/DocsWorkbenchPage.jsx
git commit -m "test: lock docs workbench page-first flow"
```

### Task 2: Rebuild docs page state around selected page

**Files:**
- Modify: `src/components/DocsWorkbenchPage.jsx`
- Inspect: `src/lib/api.js`

**Step 1: Write the failing test**

Extend the docs workbench tests to assert:
- the default selected item comes from the best recent page, not the first event
- related event data is secondary and optional
- the source/job line is shown in the related section when available

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench"`
Expected: FAIL because current selection logic is event-driven.

**Step 3: Write minimal implementation**

In `src/components/DocsWorkbenchPage.jsx`:
- compute the preferred selected page from changed pages / recent pages
- derive related event(s) for that page after selection
- stop using the event list as the primary browsing path
- keep current API calls; do not add new endpoints unless blocked

**Step 4: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/components/DocsWorkbenchPage.jsx src/test/app.test.jsx
git commit -m "feat: make docs workbench page-first"
```

### Task 3: Implement the new detail modules

**Files:**
- Modify: `src/components/DocsWorkbenchPage.jsx`
- Modify: `src/index.css`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Add assertions for the fixed right-side modules:
- `变化`
- `影响`
- `建议`
- `Diff`
- `关联`
- `深读`
- `去研究`

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench"`
Expected: FAIL because the current right-side detail structure does not match these modules.

**Step 3: Write minimal implementation**

Implement a new detail panel in `src/components/DocsWorkbenchPage.jsx` that:
- maps current event/page fields into the new sections
- falls back to page summary when event analysis is absent
- renders source time and job info in `关联`
- exposes a local `深读` toggle for expanded content

Update `src/index.css` to support the new three-column page-first layout with simpler cards and stronger hierarchy.

**Step 4: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/components/DocsWorkbenchPage.jsx src/index.css src/test/app.test.jsx
git commit -m "feat: redesign docs detail interpretation panels"
```

### Task 4: Wire the research handoff

**Files:**
- Modify: `src/components/DocsWorkbenchPage.jsx`
- Modify: `src/App.jsx`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Add a test that clicks `去研究` and verifies the app navigates to `研究台` with the current project/page context visible in the research input state or heading.

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "去研究"`
Expected: FAIL because the current docs page has no research handoff.

**Step 3: Write minimal implementation**

Add a callback prop from `src/App.jsx` into `src/components/DocsWorkbenchPage.jsx` that:
- switches the active nav to `研究台`
- passes selected page context into the research page state

Keep the implementation small and reuse existing app-level navigation state.

**Step 4: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx -t "去研究"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/App.jsx src/components/DocsWorkbenchPage.jsx src/test/app.test.jsx
git commit -m "feat: hand off docs context into research desk"
```

### Task 5: Remove obsolete docs desk chrome and verify the flow

**Files:**
- Modify: `src/components/DocsWorkbenchPage.jsx`
- Modify: `src/index.css`
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Add assertions that the old summary cards and event-first headers are gone:
- no `首次完整解读`
- no `最近更新 diff`
- no large empty event prompt when pages exist

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench"`
Expected: FAIL because the old chrome still exists.

**Step 3: Write minimal implementation**

Delete or downgrade the old digest grid and event-first layout remnants from `src/components/DocsWorkbenchPage.jsx` and matching CSS from `src/index.css`.

**Step 4: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench|去研究"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/components/DocsWorkbenchPage.jsx src/index.css src/test/app.test.jsx
git commit -m "refactor: remove obsolete docs desk chrome"
```

### Task 6: Final verification

**Files:**
- Inspect: `src/components/DocsWorkbenchPage.jsx`
- Inspect: `src/App.jsx`
- Inspect: `src/index.css`
- Inspect: `src/test/app.test.jsx`

**Step 1: Run focused tests**

Run: `npm test -- src/test/app.test.jsx -t "docs workbench|去研究|文档台"`
Expected: PASS

**Step 2: Run build**

Run: `npm run build`
Expected: PASS

**Step 3: Sanity-check runtime**

Run: `curl -sS http://127.0.0.1:5173/ | head -n 20`
Expected: HTML is returned and the app still boots.

**Step 4: Commit**

```bash
git add src/App.jsx src/components/DocsWorkbenchPage.jsx src/index.css src/test/app.test.jsx docs/plans/2026-03-17-docs-workbench-redesign-design.md docs/plans/2026-03-17-docs-workbench-redesign.md
git commit -m "feat: rebuild docs desk around page-first reading"
```
