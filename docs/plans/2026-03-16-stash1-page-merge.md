# Stash Page Merge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Selectively merge page-related UI + required API endpoints from `stash@{1}` into current `main`, preserving all newer main behavior.

**Architecture:** Apply changes file-by-file for page UI and minimal backend endpoints. Resolve conflicts in favor of current main except for explicitly required UI features. Add/adjust tests for new page behavior and run full verification.

**Tech Stack:** React + Vite frontend, Python Flask backend, Pytest + Vitest.

---

### Task 1: Create a worktree for safe merge work

**Files:**
- None

**Step 1: Create worktree**

Run: `git worktree add .worktrees/stash1-page-merge -b stash1-page-merge`

**Step 2: Verify clean status**

Run: `cd .worktrees/stash1-page-merge && git status -sb`
Expected: clean

**Step 3: Commit**

No commit for this task.

---

### Task 2: Extract page-related changes from stash@{1} into worktree

**Files:**
- Modify: `src/App.jsx`
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `src/components/ProjectMonitorPage.jsx`
- Modify: `src/components/SyncStatusPanel.jsx`
- Modify: `src/index.css`
- Modify: `src/lib/api.js`
- Modify: `src/test/app.test.jsx`

**Step 1: Apply stash@{1} to a temporary branch**

Run: `git stash show -p stash@{1} > /tmp/stash1.patch`

**Step 2: Apply only the frontend file hunks**

Apply changes by patching each file in the worktree, resolving conflicts in favor of current main except where the new page UI is needed.

**Step 3: Commit**

```bash
git add src/App.jsx src/components/IntelOverviewPage.jsx src/components/ProjectMonitorPage.jsx src/components/SyncStatusPanel.jsx src/index.css src/lib/api.js src/test/app.test.jsx
git commit -m "feat: merge stash page UI updates"
```

---

### Task 3: Add backend endpoints required by the new pages

**Files:**
- Modify: `backend/app.py`
- Modify: `backend/storage.py` (only if required)
- Modify: `backend/runtime.py` (only if required)

**Step 1: Apply only the /api/sync/runs endpoints from stash@{1}**

Ensure endpoints are additive and do not remove existing API routes.

**Step 2: Add minimal storage or runtime support (if needed)**

Only add what the new pages require (e.g., load/save sync runs).

**Step 3: Commit**

```bash
git add backend/app.py backend/storage.py backend/runtime.py
git commit -m "feat: add sync run endpoints for new pages"
```

---

### Task 4: Tests for new page behavior

**Files:**
- Modify: `src/test/app.test.jsx`
- Modify: `backend/tests/test_api.py` (if endpoints added)

**Step 1: Add failing tests for sync run endpoints/UI**

Write tests that assert the new page renders and fetches sync run history.

**Step 2: Run tests to see failure**

Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL before implementation is fully wired.

**Step 3: Update implementation until tests pass**

**Step 4: Commit**

```bash
git add src/test/app.test.jsx backend/tests/test_api.py
git commit -m "test: cover new sync log page"
```

---

### Task 5: Full verification

**Step 1: Run backend tests**

Run: `python -m pytest -q`
Expected: PASS

**Step 2: Run frontend tests**

Run: `npm test`
Expected: PASS

**Step 3: Build**

Run: `npm run build`
Expected: PASS

---

## Notes
- Keep only page-related changes from stash@{1}.
- Prefer current main logic for any shared code not required for the new pages.
