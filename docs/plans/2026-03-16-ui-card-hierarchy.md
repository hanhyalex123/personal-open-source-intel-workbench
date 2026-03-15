# UI Card Hierarchy Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Effective Config and Sync Log Detail sections feel like higher‑hierarchy cards with stronger borders, shadows, and clearer headers.

**Architecture:** Pure CSS adjustments + minimal markup tweaks; no behavioral changes.

**Tech Stack:** React + CSS.

---

### Task 1: Add failing visual assertions (lightweight)

**Files:**
- Modify: `src/test/app.test.jsx`

**Step 1: Add a test that checks for new class hooks**

Assert presence of `llm-effective` and `sync-log-detail` containers (already exist), and new header chips if added.

**Step 2: Run test to verify failure (if hooks added)**

Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL if new hooks not present.

**Step 3: Commit (tests only)**

```bash
git add src/test/app.test.jsx
git commit -m "test: cover card hierarchy hooks"
```

---

### Task 2: Update Effective Config card styles

**Files:**
- Modify: `src/index.css`

**Step 1: Strengthen card styles**
- White background, stronger border, soft shadow
- Header chip for “生效值”
- Emphasize key row

**Step 2: Run tests**

Run: `npm test -- src/test/app.test.jsx`
Expected: PASS

**Step 3: Commit**

```bash
git add src/index.css
git commit -m "style: elevate effective config card"
```

---

### Task 3: Update Sync Log Detail card styles

**Files:**
- Modify: `src/index.css`

**Step 1: Strengthen detail card hierarchy**
- Header bar + divider lines
- Row separators, stronger titles
- JSON area inset card

**Step 2: Run tests**

Run: `npm test -- src/test/app.test.jsx`
Expected: PASS

**Step 3: Commit**

```bash
git add src/index.css
git commit -m "style: elevate sync log detail card"
```

---

### Task 4: Full verification

**Step 1: Run frontend tests**

Run: `npm test`
Expected: PASS

**Step 2: Build**

Run: `npm run build`
Expected: PASS
