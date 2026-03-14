# Brand Avatar And Homepage Simplification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current seal-style brand mark with a local anime-style avatar, simplify the homepage top section, and slim `README.md` into a short present-state document.

**Architecture:** Keep the existing app/data flow intact. Add one local SVG avatar asset, wire it into the sidebar and homepage brandline, remove redundant homepage fragments from `IntelOverviewPage`, and update styles so the avatar-driven brand system remains compact. `README.md` is shortened without changing setup accuracy.

**Tech Stack:** React, Vite, CSS, Vitest, Markdown

---

### Task 1: Update homepage test expectations for the simplified brand/header

**Files:**
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**
- Remove assertions for homepage copy that will be deleted.
- Add stable assertions for the local brand avatar alt text and the simplified homepage sections.

**Step 2: Run test to verify it fails**
Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL because the avatar and simplified homepage structure are not implemented yet.

**Step 3: Keep navigation and monitoring assertions intact**
- Only change homepage-related assertions.

**Step 4: Run test to verify it fails correctly**
Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL on missing avatar/updated labels, not on unrelated errors.

### Task 2: Add a local anime-style SVG avatar and wire it into the app shell

**Files:**
- Create: `src/assets/brand-avatar-anime.svg`
- Modify: `src/App.jsx`

**Step 1: Create the local SVG asset**
- Draw a compact anime-style female avatar suitable for 48-72px usage.
- Keep it self-contained and ASCII-safe.

**Step 2: Use the asset in the sidebar brand block**
- Replace the current seal glyph with the image.
- Keep the existing product name text.

**Step 3: Run the homepage test**
Run: `npm test -- src/test/app.test.jsx`
Expected: still FAIL if homepage structure is not updated yet, but avatar assertion should now be satisfiable.

### Task 3: Simplify the homepage hero and brandline

**Files:**
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `src/index.css`

**Step 1: Implement the simplified homepage layout**
- Reuse the new avatar inside the homepage brandline.
- Remove the marker card cluster and duplicated summary fragments.
- Keep only brand, main title, one explanatory note, featured conclusion, and running snapshot.

**Step 2: Adjust CSS to match the simplified structure**
- Tighten spacing.
- Keep the stronger palette from the latest pass.
- Ensure the avatar works in both sidebar and homepage without oversized decoration.

**Step 3: Run the homepage test**
Run: `npm test -- src/test/app.test.jsx`
Expected: PASS.

### Task 4: Shorten `README.md`

**Files:**
- Modify: `README.md`

**Step 1: Rewrite to a short present-state format**
- Keep: what it is, what it can do, startup, screenshots.
- Drop: long explanatory sections and repeated detail.

**Step 2: Keep operational accuracy**
- Preserve actual startup commands and environment variable names.

### Task 5: Final verification

**Files:**
- Verify: `src/App.jsx`
- Verify: `src/components/IntelOverviewPage.jsx`
- Verify: `src/index.css`
- Verify: `src/test/app.test.jsx`
- Verify: `README.md`

**Step 1: Run frontend tests**
Run: `npm test`
Expected: all frontend tests pass.

**Step 2: Run production build**
Run: `npm run build`
Expected: build succeeds.

**Step 3: Review final diff**
Run: `git diff --stat -- src/App.jsx src/components/IntelOverviewPage.jsx src/index.css src/test/app.test.jsx README.md src/assets/brand-avatar-anime.svg`
Expected: only brand/homepage/readme files changed.
