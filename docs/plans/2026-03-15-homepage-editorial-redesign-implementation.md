# Homepage Editorial Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the homepage into a denser editorial-style landing page that removes empty space, surfaces the main insight immediately, and keeps the existing data model unchanged.

**Architecture:** Keep the current homepage data flow intact and only reshape presentation. Recompose `IntelOverviewPage` into a tighter hero + snapshot + featured digest layout, then adjust CSS so the first screen contains the primary summary and key operational metrics without the current floating whitespace.

**Tech Stack:** React, Vite, Vitest, CSS

---

### Task 1: Update homepage test expectations for the new editorial layout

**Files:**
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**
- Add assertions for the new structure: compact operating snapshot labels, featured digest visibility in the first section, and dual-column lower content cues.
- Remove assertions tied to the current cover-only layout that will no longer exist.

**Step 2: Run test to verify it fails**
Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL because the new homepage labels/structure are not rendered yet.

**Step 3: Write minimal implementation target assertions**
- Assert for stable copy such as `运行快照`, `重点结论`, `增量快讯`, `日报归档`.
- Keep unrelated navigation and sync assertions intact.

**Step 4: Run test to verify it fails correctly**
Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL on missing homepage structure, not on unrelated fetch/setup issues.

**Step 5: Commit**
```bash
git add src/test/app.test.jsx
git commit -m "test: update homepage editorial layout expectations"
```

### Task 2: Recompose the homepage component into a denser editorial structure

**Files:**
- Modify: `src/components/IntelOverviewPage.jsx`

**Step 1: Write the minimal implementation**
- Replace the current wide cover composition with:
  - a compact top masthead
  - left editorial hero copy
  - right running snapshot card
  - a featured digest block that pulls the first homepage project into the first screen
  - a lower two-column section for incremental updates and archive
- Reuse existing `ProjectSummaryCard`, `IncrementalUpdateList`, and `DailyDigestHistory` where practical.

**Step 2: Preserve data contracts**
- Do not change prop names or response shapes.
- Add small helper components only if they reduce duplication.

**Step 3: Run the homepage test**
Run: `npm test -- src/test/app.test.jsx`
Expected: PASS for the homepage structure assertions.

**Step 4: Commit**
```bash
git add src/components/IntelOverviewPage.jsx src/test/app.test.jsx
git commit -m "feat: recompose homepage into editorial layout"
```

### Task 3: Rewrite homepage CSS for compact editorial density

**Files:**
- Modify: `src/index.css`

**Step 1: Write the minimal styling changes**
- Remove the current floating empty-space look from the homepage hero.
- Introduce a denser top grid, stronger editorial dividers, a snapshot rail, and tighter section spacing.
- Keep homepage-only selectors scoped to avoid regressions on sync/settings pages.

**Step 2: Verify responsive behavior**
- Ensure the new hero collapses cleanly on narrow screens.
- Keep all cards readable without overlapping or large dead zones.

**Step 3: Run build and tests**
Run: `npm test -- src/test/app.test.jsx && npm run build`
Expected: PASS and successful build.

**Step 4: Commit**
```bash
git add src/index.css src/components/IntelOverviewPage.jsx src/test/app.test.jsx
git commit -m "style: tighten homepage editorial layout"
```

### Task 4: Final verification

**Files:**
- Verify: `src/components/IntelOverviewPage.jsx`
- Verify: `src/index.css`
- Verify: `src/test/app.test.jsx`

**Step 1: Run frontend tests**
Run: `npm test`
Expected: all frontend tests pass.

**Step 2: Run production build**
Run: `npm run build`
Expected: build succeeds with no homepage regressions.

**Step 3: Review final diff**
Run: `git diff --stat HEAD~3..HEAD`
Expected: only homepage component, styles, and test files changed for this redesign.

**Step 4: Commit if needed**
```bash
git status
```
Expected: clean working tree except for any intentionally untracked docs.
