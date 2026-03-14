# Sync Monitor UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split “同步监控” into its own page, keep homepage focused on 日报/增量提醒, and make logs easier to access and understand.

**Architecture:** Add a new Sync Monitor page component, adjust App navigation and topbar behavior, and update SyncStatusPanel/SyncLogDrawer copy. Keep backend unchanged.

**Tech Stack:** React, Vitest, CSS, Flask API (no changes)

---

### Task 1: Add Sync Monitor page and navigation entry

**Files:**
- Create: `src/components/SyncMonitorPage.jsx`
- Modify: `src/App.jsx`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Add tests that:
- A new sidebar item `同步监控` exists.
- Clicking it shows the Sync Monitor page and hides homepage content.

Example:

```jsx
it("shows sync monitor page in navigation", async () => {
  render(<App />);
  const monitorTab = await screen.findByRole("button", { name: "同步监控" });
  fireEvent.click(monitorTab);
  expect(screen.getByText("同步监控")).toBeInTheDocument();
  expect(screen.queryByText("日报首页")).not.toBeInTheDocument();
});
```

**Step 2: Run test to verify failure**

Run:

```bash
npm test -- --runInBand src/test/app.test.jsx
```

Expected: FAIL (no Sync Monitor page exists).

**Step 3: Implement minimal code**

- Add `SyncMonitorPage` component that composes:
  - SyncStatusPanel
  - Short description
  - Log entry button (uses existing open drawer handler)
- Add nav item to `NAV_ITEMS` and route it in `App.jsx`.
- Only show `SyncStatusPanel` on this page.

**Step 4: Run test to verify pass**

Run:

```bash
npm test -- --runInBand src/test/app.test.jsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/components/SyncMonitorPage.jsx src/App.jsx src/test/app.test.jsx
git commit -m "feat: add sync monitor page"
```

---

### Task 2: Move “立即同步” and simplify homepage

**Files:**
- Modify: `src/App.jsx`
- Modify: `src/components/IntelOverviewPage.jsx`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Add tests that:
- “立即同步” appears only on the Sync Monitor page.
- Homepage shows 日报首页 but no sync panel.

**Step 2: Run test to verify failure**

Run:

```bash
npm test -- --runInBand src/test/app.test.jsx
```

Expected: FAIL

**Step 3: Implement minimal code**

- In `App.jsx`, conditionally render the topbar sync button only when `activePage === "monitor"`.
- Ensure homepage still renders `IntelOverviewPage` without any sync panel.
- Adjust any description copy if needed.

**Step 4: Run test to verify pass**

Run:

```bash
npm test -- --runInBand src/test/app.test.jsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/App.jsx src/components/IntelOverviewPage.jsx src/test/app.test.jsx
git commit -m "refactor: keep sync actions on monitor page"
```

---

### Task 3: Improve log entry copy and event readability

**Files:**
- Modify: `src/components/SyncStatusPanel.jsx`
- Modify: `src/components/SyncLogDrawer.jsx`
- Test: `src/test/sync-status-panel.test.jsx`

**Step 1: Write the failing test**

Add/adjust test to expect:
- Button label `查看日志` instead of `日志`.

**Step 2: Run test to verify failure**

Run:

```bash
npm test -- --runInBand src/test/sync-status-panel.test.jsx
```

Expected: FAIL

**Step 3: Implement minimal code**

- Rename the button to `查看日志`.
- Ensure SyncLogDrawer keeps displaying model/provider/fallback lines (already present).

**Step 4: Run test to verify pass**

Run:

```bash
npm test -- --runInBand src/test/sync-status-panel.test.jsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/components/SyncStatusPanel.jsx src/components/SyncLogDrawer.jsx src/test/sync-status-panel.test.jsx
git commit -m "feat: clarify log entry copy"
```

---

### Task 4: Add minimal styling for Sync Monitor layout

**Files:**
- Modify: `src/index.css`
- Test: `npm test` (smoke)

**Step 1: Write the failing test (visual regression not available)**

Skip test for CSS changes; ensure no lint/test failures in `npm test`.

**Step 2: Implement minimal CSS**

- Add `.sync-monitor-page` container spacing.
- Align status strip and cards with existing design tokens.

**Step 3: Run tests**

Run:

```bash
npm test
```

Expected: PASS

**Step 4: Commit**

```bash
git add src/index.css
git commit -m "style: add sync monitor layout"
```

---

### Task 5: End-to-end verification

**Files:**
- None unless regressions appear

**Step 1: Run full verification**

Run:

```bash
npm test
.venv/bin/python -m pytest -q
```

Expected: PASS

**Step 2: Manual smoke**

Start app:

```bash
bash scripts/start_intel_workbench.sh
```

Confirm:
- `同步监控` entry exists
- 日报首页无同步雷达
- 同步监控页日志入口易懂

**Step 3: Commit any fixes if necessary**

```bash
git add <files>
git commit -m "fix: polish sync monitor ux"
```
