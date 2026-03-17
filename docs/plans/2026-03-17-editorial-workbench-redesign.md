# Editorial Workbench Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the frontend into an editorial technical-magazine product with a new information architecture: `封面`, `线索台`, `专题库`, `文档台`, `研究台`, and `设置`.

**Architecture:** The work starts by replacing the global shell and design system, then migrates page-by-page into the new editorial IA. Existing data-fetching flows and backend APIs stay intact where possible. The sync Job model already completed becomes a first-class part of `线索台` rather than a standalone page identity.

**Tech Stack:** React, Vite, Vitest, CSS, existing local API layer

---

### Task 1: Lock the new navigation and shell structure

**Files:**
- Modify: `src/App.jsx`
- Modify: `src/index.css`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test for the new top-level navigation labels**

```jsx
it("shows the editorial navigation", async () => {
  render(<App />);

  expect(await screen.findByRole("button", { name: "封面" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "线索台" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "专题库" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "文档台" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "研究台" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "设置" })).toBeInTheDocument();
});
```

**Step 2: Run the focused test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "editorial navigation"`
Expected: FAIL because the old navigation labels still render.

**Step 3: Update `App.jsx` navigation metadata and root shell framing**

- Replace the old page ids and labels with the editorial IA
- Update the page-title/subtitle copy to match the new sections
- Keep the existing data-loading logic intact
- Preserve `SyncLogDrawer` behavior and selected run state

**Step 4: Add the minimal shell CSS changes**

- Adjust navigation framing, title area, and page container rules
- Do not yet redesign every child component

**Step 5: Re-run the focused test**

Run: `npm test -- src/test/app.test.jsx -t "editorial navigation"`
Expected: PASS

**Step 6: Commit**

```bash
git add src/App.jsx src/index.css src/test/app.test.jsx
git commit -m "feat: adopt editorial navigation shell"
```

### Task 2: Establish the editorial design tokens and layout primitives

**Files:**
- Modify: `src/index.css`
- Reference: `src/App.jsx`

**Step 1: Add the new global design tokens**

Implement in `src/index.css`:

- warm paper background tokens
- deep ink text tokens
- electric blue accent tokens
- spacing scale for editorial sections
- shared surface types for `masthead`, `rail`, `editorial panel`, `utility panel`
- typography rules for display, kicker, caption, meta, and body

**Step 2: Add responsive shell behavior**

Implement rules for:

- collapsed navigation on narrow screens
- stacked content rails on mobile
- page title blocks that remain readable on small widths

**Step 3: Verify visually in dev server**

Run: `npm run dev -- --host 127.0.0.1 --port 5173`
Expected: shell renders with new global styling and no obvious overflow.

**Step 4: Commit**

```bash
git add src/index.css
git commit -m "feat: add editorial design tokens"
```

### Task 3: Rebuild `封面` as the issue cover page

**Files:**
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `src/index.css`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test for the new cover identity**

```jsx
it("renders the cover page framing", async () => {
  render(<App />);
  expect(await screen.findByText("封面")).toBeInTheDocument();
  expect(screen.getByText(/今天最重要的结论/i)).toBeInTheDocument();
});
```

**Step 2: Run the focused test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "cover page framing"`
Expected: FAIL because the old daily-home wording still renders.

**Step 3: Recompose `IntelOverviewPage.jsx`**

- Turn the hero into a cover masthead
- Promote one featured item as the cover story
- Restage supporting items into secondary stories
- Add a compact news strip for recent job and update cues
- Keep existing data usage; do not invent new backend data

**Step 4: Add matching CSS**

- cover grid
- cover story hierarchy
- side rail for operational pulse
- compact secondary story layout

**Step 5: Re-run the focused test**

Run: `npm test -- src/test/app.test.jsx -t "cover page framing"`
Expected: PASS

**Step 6: Commit**

```bash
git add src/components/IntelOverviewPage.jsx src/index.css src/test/app.test.jsx
git commit -m "feat: redesign the cover page"
```

### Task 4: Rebuild `线索台` around the duty-desk model

**Files:**
- Modify: `src/components/SyncMonitorPage.jsx`
- Modify: `src/components/SyncStatusPanel.jsx`
- Modify: `src/components/SyncJobList.jsx`
- Modify: `src/components/SyncLogDrawer.jsx`
- Modify: `src/index.css`
- Test: `src/test/sync-status-panel.test.jsx`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test for the clue-desk page title and current job block**

```jsx
it("renders the clue desk and current job block", async () => {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "线索台" }));

  expect(screen.getByText("线索台")).toBeInTheDocument();
  expect(screen.getByText("当前 Job")).toBeInTheDocument();
});
```

**Step 2: Run the focused tests to verify failure**

Run: `npm test -- src/test/app.test.jsx src/test/sync-status-panel.test.jsx -t "clue desk|当前 Job|已完成，含失败项"`
Expected: FAIL where current copy or layout assumptions no longer match.

**Step 3: Recompose the sync page into a duty desk**

- Add duty overview framing
- Keep current Job and recent Jobs as one operational zone
- Add space for actionable clues rather than only logs
- Keep log drawer entry clear and immediate
- Preserve the selected-job logic already built

**Step 4: Update CSS for duty-desk composition**

- three-zone layout on desktop
- stacked sections on mobile
- stronger distinction between live state, history, and clues

**Step 5: Re-run the focused tests**

Run: `npm test -- src/test/app.test.jsx src/test/sync-status-panel.test.jsx -t "clue desk|当前 Job|已完成，含失败项"`
Expected: PASS

**Step 6: Commit**

```bash
git add src/components/SyncMonitorPage.jsx src/components/SyncStatusPanel.jsx src/components/SyncJobList.jsx src/components/SyncLogDrawer.jsx src/index.css src/test/app.test.jsx src/test/sync-status-panel.test.jsx
git commit -m "feat: redesign the clue desk"
```

### Task 5: Rebuild `专题库` from project monitor to editorial dossiers

**Files:**
- Modify: `src/components/ProjectMonitorPage.jsx`
- Modify: `src/components/InsightCard.jsx`
- Modify: `src/components/SourceSection.jsx`
- Modify: `src/index.css`

**Step 1: Identify the smallest reusable narrative card shape**

Read existing components and choose whether to evolve `InsightCard` or split a new dossier card. Prefer reuse unless it creates awkward coupling.

**Step 2: Write the failing test for topic-library wording or anchors if needed**

If component tests are missing, add a minimal render assertion around the new page title or dossier entry structure.

**Step 3: Recompose `ProjectMonitorPage.jsx`**

- Add topic stream framing
- Keep direct project lookup available
- Give each project a stronger narrative summary zone
- Preserve release/docs deep links
- Keep the outline useful but restage it as an editorial navigator

**Step 4: Update supporting component styles**

- dossier cards
- index/sidebar framing
- category subsections
- detail block spacing and meta styling

**Step 5: Run affected frontend tests**

Run: `npm test`
Expected: PASS

**Step 6: Commit**

```bash
git add src/components/ProjectMonitorPage.jsx src/components/InsightCard.jsx src/components/SourceSection.jsx src/index.css src/test/app.test.jsx
git commit -m "feat: redesign the topic library"
```

### Task 6: Rebuild `文档台` into a docs editorial workspace

**Files:**
- Modify: `src/components/DocsWorkbenchPage.jsx`
- Modify: `src/index.css`

**Step 1: Recompose the page into left rail / event stream / detail panel**

- keep current data fetching and selection logic
- improve event readability and page-diff scanning
- separate filters from content detail

**Step 2: Restage document event cards and page-diff modules**

- more editorial event cards
- stronger selected state
- clearer page-link and diff emphasis

**Step 3: Run the frontend test suite**

Run: `npm test`
Expected: PASS

**Step 4: Commit**

```bash
git add src/components/DocsWorkbenchPage.jsx src/index.css src/test/app.test.jsx
git commit -m "feat: redesign the docs desk"
```

### Task 7: Rebuild `研究台` into a research workspace

**Files:**
- Modify: `src/components/AIConsolePage.jsx`
- Modify: `src/components/SimpleMarkdown.jsx` (only if styling hooks are needed)
- Modify: `src/index.css`

**Step 1: Reframe the page layout**

- left input rail
- center report stage
- right evidence rail

**Step 2: Improve result framing**

- make report body the dominant visual object
- downgrade raw metadata blocks into supporting panels
- keep evidence and trace easy to inspect

**Step 3: Run the frontend test suite**

Run: `npm test`
Expected: PASS

**Step 4: Commit**

```bash
git add src/components/AIConsolePage.jsx src/components/SimpleMarkdown.jsx src/index.css src/test/app.test.jsx
git commit -m "feat: redesign the research desk"
```

### Task 8: Redesign `设置` to fit the editorial system

**Files:**
- Modify: `src/components/SettingsPage.jsx`
- Modify: `src/index.css`

**Step 1: Restage settings into capability sections**

- capability overview
- active/effective configuration panel
- assistant defaults
- project onboarding/admin grouping

**Step 2: Improve forms without changing API shape**

- preserve current save handlers
- reduce schema-first presentation
- keep effective-state visibility strong

**Step 3: Run the frontend test suite**

Run: `npm test`
Expected: PASS

**Step 4: Commit**

```bash
git add src/components/SettingsPage.jsx src/index.css src/test/app.test.jsx
git commit -m "feat: redesign settings"
```

### Task 9: Run final regression and polish responsive issues

**Files:**
- Modify: `src/index.css`
- Modify: any touched component files as needed

**Step 1: Run the full frontend test suite**

Run: `npm test`
Expected: PASS

**Step 2: Run a production build**

Run: `npm run build`
Expected: successful Vite build with no fatal errors

**Step 3: Verify the live app manually**

Run: `npm run dev -- --host 127.0.0.1 --port 5173`
Check:
- navigation labels and active states
- cover layout at desktop and narrow width
- clue desk current job and recent jobs layout
- topic-library scrolling and anchors
- docs desk event/detail flow
- research desk report/evidence layout
- settings forms and save affordances

**Step 4: Fix only verified visual or responsive defects**

Keep changes scoped to observed issues.

**Step 5: Re-run verification**

Run:
- `npm test`
- `npm run build`
Expected: both PASS

**Step 6: Commit**

```bash
git add src/index.css src/App.jsx src/components src/test/app.test.jsx src/test/sync-status-panel.test.jsx
git commit -m "feat: complete editorial frontend redesign"
```
