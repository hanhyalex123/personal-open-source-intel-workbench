# Release Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the current dashboard into a public-shareable release with a stronger magazine-style homepage, clearer sync monitor visuals, and a current-state README.

**Architecture:** Keep the data flow unchanged and limit the work to React component structure, CSS primitives, and documentation copy. Use lightweight inline icon components to avoid adding packages.

**Tech Stack:** React, Vite, CSS, Vitest, Pytest

---

### Task 1: Magazine-style homepage refresh

**Files:**
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `src/index.css`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Update homepage tests to assert the new visual labels and icon-backed copy:

```jsx
expect(screen.getByText("Signal Desk")).toBeInTheDocument();
expect(screen.getByText("情报封面")).toBeInTheDocument();
expect(screen.getByText("同步信号")).toBeInTheDocument();
```

**Step 2: Run test to verify it fails**

Run:

```bash
npm test -- src/test/app.test.jsx
```

Expected: FAIL because the new copy is not rendered yet.

**Step 3: Write minimal implementation**

- Add small inline icon components or glyph wrappers inside `IntelOverviewPage`.
- Rebuild the hero section into a cover-style layout with editorial labels.
- Add supporting CSS for the new cover panel, icon chips, and section headers.

**Step 4: Run test to verify it passes**

Run:

```bash
npm test -- src/test/app.test.jsx
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/components/IntelOverviewPage.jsx src/index.css src/test/app.test.jsx
git commit -m "Polish homepage for public release"
```

---

### Task 2: Sync monitor visual alignment

**Files:**
- Modify: `src/components/SyncMonitorPage.jsx`
- Modify: `src/components/SyncStatusPanel.jsx`
- Modify: `src/index.css`
- Test: `src/test/sync-status-panel.test.jsx`

**Step 1: Write the failing test**

Add assertions for the new sync monitor copy and visual labels:

```jsx
expect(screen.getByText("Signal Radar")).toBeInTheDocument();
expect(screen.getByText("本次合计（最近一次增量）")).toBeInTheDocument();
```

**Step 2: Run test to verify it fails**

Run:

```bash
npm test -- src/test/sync-status-panel.test.jsx
```

Expected: FAIL because the panel still uses the previous wording and structure.

**Step 3: Write minimal implementation**

- Add a stronger intro card for the sync monitor page.
- Update the total note text so it communicates that totals come from the latest incremental run.
- Align status chips, metric cards, and buttons with the homepage visual language.

**Step 4: Run test to verify it passes**

Run:

```bash
npm test -- src/test/sync-status-panel.test.jsx
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/components/SyncMonitorPage.jsx src/components/SyncStatusPanel.jsx src/index.css src/test/sync-status-panel.test.jsx
git commit -m "Align sync monitor with release visuals"
```

---

### Task 3: README current-state rewrite

**Files:**
- Modify: `README.md`

**Step 1: Write the target structure**

Rewrite the README around:
- What it is
- What works today
- Current screens
- Stack
- Setup and startup
- Environment variables
- Data and logs
- Current limitations

**Step 2: Implement the rewrite**

Replace the old concept-heavy copy with current-state product copy and keep startup instructions accurate.

**Step 3: Review for brevity and correctness**

Check that all commands, URLs, and current capabilities match the running app.

**Step 4: Commit**

```bash
git add README.md
git commit -m "Rewrite README for current product state"
```

---

### Task 4: Verification and release copy

**Files:**
- None for code, optional notes only

**Step 1: Run backend tests**

```bash
.venv/bin/python -m pytest -q
```

Expected: PASS.

**Step 2: Run frontend tests**

```bash
npm test
```

Expected: PASS.

**Step 3: Restart app and confirm startup**

```bash
./scripts/stop_intel_workbench.sh
./scripts/start_intel_workbench.sh
```

Expected: app available on `http://127.0.0.1:5173`.

**Step 4: Prepare Linux.do copy**

Produce one short title and one short body suitable for `资源荟萃` with `开源` and `软件开发` tags.
