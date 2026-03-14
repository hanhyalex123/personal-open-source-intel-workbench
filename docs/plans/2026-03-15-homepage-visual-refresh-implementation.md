# Homepage Visual Refresh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refresh the 日报首页 layout and palette to an editorial headline style with cool blue/gray tones, without changing functionality.

**Architecture:** Keep existing data flow and components. Adjust IntelOverviewPage markup to introduce a headline hero + light info band, and update global CSS tokens for a cooler palette. No backend changes.

**Tech Stack:** React, Vitest, CSS

---

### Task 1: Add headline layout structure to the homepage

**Files:**
- Modify: `src/components/IntelOverviewPage.jsx`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Add expectations that the homepage shows a headline label and a dedicated info band container.

```jsx
expect(screen.getByText("今日头条")).toBeInTheDocument();
expect(document.querySelector(".intel-info-band")).not.toBeNull();
```

**Step 2: Run test to verify it fails**

Run:

```bash
npm test -- src/test/app.test.jsx
```

Expected: FAIL (no headline label or info band container yet).

**Step 3: Implement minimal code**

- Update `IntelOverviewPage`:
  - Add a headline label `今日头条` in the hero section.
  - Introduce a new wrapper `.intel-info-band` that holds the current stat cards.
  - Keep existing content (日报卡、增量提醒、归档) unchanged.

**Step 4: Run test to verify it passes**

Run:

```bash
npm test -- src/test/app.test.jsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/components/IntelOverviewPage.jsx src/test/app.test.jsx
git commit -m "feat: add headline layout for homepage"
```

---

### Task 2: Apply cool blue/gray palette and layout styling

**Files:**
- Modify: `src/index.css`

**Step 1: Write the failing test (visual regression not available)**

Skip test for CSS changes; ensure no lint/test failures in `npm test`.

**Step 2: Implement minimal CSS**

- Update `:root` background gradient and base text colors to blue/gray.
- Adjust `.sidebar`, `.topbar`, `.hero-card`, `.stat-card`, `.intel-section` backgrounds/borders to cool neutrals.
- Add new styles for `.intel-info-band` (horizontal, low visual weight).
- Tweak `.hero-card` typography to feel more editorial (larger headline, calmer subtitle).

**Step 3: Run tests**

Run:

```bash
npm test
```

Expected: PASS

**Step 4: Commit**

```bash
git add src/index.css
git commit -m "style: refresh homepage palette and layout"
```

---

### Task 3: Verification

**Files:**
- None unless regressions appear

**Step 1: Run full verification**

Run:

```bash
npm test
```

Expected: PASS

**Step 2: Manual smoke**

Start app:

```bash
bash scripts/start_intel_workbench.sh
```

Confirm:
- 首页头条层级明显
- 日报卡仍是主视觉
- 增量提醒与归档保留

**Step 3: Commit any fixes if necessary**

```bash
git add <files>
git commit -m "fix: polish homepage visual refresh"
```
