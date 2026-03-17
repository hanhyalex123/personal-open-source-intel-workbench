# Brand Icon Refresh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current sidebar avatar and missing browser favicon with a single cropped brand icon derived from the user-provided reference image.

**Architecture:** Download the reference image, crop the clearest subject into a square icon asset, then wire that asset into both the in-app brand image import and the browser tab icon reference. Verify with focused tests and a production build.

**Tech Stack:** Vite, React, CSS, local image tooling (`curl`, `sips` or Python PIL), Vitest

---

### Task 1: Prepare Icon Asset

**Files:**
- Create: `tmp/brand-source.png`
- Create: `src/assets/brand-icon.png`

**Step 1: Download the source image**

Run: `bash -lc 'curl -L "<user-image-url>" -o /tmp/brand-source.png'`
Expected: file downloaded successfully

**Step 2: Inspect image dimensions**

Run: `sips -g pixelWidth -g pixelHeight /tmp/brand-source.png`
Expected: source width and height printed

**Step 3: Crop the subject into a square icon**

Run local image tooling to crop the most legible central character area into `src/assets/brand-icon.png`.
Expected: a square icon asset exists and is visually readable at small sizes

**Step 4: Verify asset exists**

Run: `sips -g pixelWidth -g pixelHeight src/assets/brand-icon.png`
Expected: square dimensions printed

### Task 2: Wire App Branding

**Files:**
- Modify: `src/App.jsx`
- Modify: `index.html`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**
Add a focused assertion in `src/test/app.test.jsx` that the sidebar brand image source points to the new icon asset or that the favicon link exists in `index.html` via a simple file assertion approach if appropriate.

**Step 2: Run the focused test to confirm failure**
Run: `npm test -- src/test/app.test.jsx -t "brand icon"`
Expected: FAIL because the old asset is still in use

**Step 3: Implement the minimal wiring**
- Replace the sidebar image import to use `src/assets/brand-icon.png`
- Add favicon `<link rel="icon" ...>` to `index.html`

**Step 4: Run the focused test again**
Run: `npm test -- src/test/app.test.jsx -t "brand icon"`
Expected: PASS

### Task 3: Verify End-to-End

**Files:**
- Verify: `src/assets/brand-icon.png`
- Verify: `index.html`
- Verify: `src/App.jsx`

**Step 1: Run the relevant tests**
Run: `npm test -- src/test/app.test.jsx -t "brand icon|editorial navigation|cover page framing"`
Expected: PASS

**Step 2: Run production build**
Run: `npm run build`
Expected: Vite build succeeds and emits bundled assets including the new icon

**Step 3: Commit**

```bash
git add src/assets/brand-icon.png index.html src/App.jsx src/test/app.test.jsx docs/plans/2026-03-17-brand-icon-refresh-design.md docs/plans/2026-03-17-brand-icon-refresh.md
git commit -m "feat: refresh brand icon and favicon"
```
