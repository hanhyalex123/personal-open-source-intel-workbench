# Card Hierarchy Visual Refresh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Strengthen visual hierarchy for LLM config cards and sync log detail using tiered card styling without changing layout or behavior.

**Architecture:** Introduce reusable tier classes (`card-tier--hero`, `card-tier--focus`, `card-tier--base`) backed by CSS tokens, then apply them to LLM provider cards, effective config panel, and sync log detail panel. Enhance those sections with clearer separators and contrast while preserving the existing glass aesthetic.

**Tech Stack:** React (JSX), CSS, Jest + Testing Library.

---

### Task 1: Add failing tests for card tier classes

**Files:**
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**

```jsx
it("applies card tier classes to LLM config and sync log detail", async () => {
  render(<App />);

  await waitFor(() => {
    expect(screen.getByText("日报首页")).toBeInTheDocument();
  });

  fireEvent.click(screen.getAllByRole("button", { name: "配置中心" })[0]);
  await waitFor(() => {
    expect(screen.getByText("AI 能力管理")).toBeInTheDocument();
  });

  const effectivePanel = document.querySelector(".llm-effective");
  expect(effectivePanel).toHaveClass("card-tier--hero");

  document
    .querySelectorAll(".llm-provider-card")
    .forEach((card) => expect(card).toHaveClass("card-tier--focus"));

  fireEvent.click(screen.getByRole("button", { name: "同步监控" }));
  fireEvent.click(screen.getAllByRole("button", { name: "查看日志" })[0]);

  await waitFor(() => {
    expect(screen.getByRole("dialog", { name: "同步日志" })).toBeInTheDocument();
  });

  fireEvent.click(screen.getAllByRole("button", { name: "查看详情" })[0]);
  const detailPanel = screen.getByTestId("sync-log-detail");
  expect(detailPanel).toHaveClass("card-tier--focus");
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL with missing `card-tier--hero` / `card-tier--focus` classes.

### Task 2: Apply tier classes in components

**Files:**
- Modify: `src/components/SettingsPage.jsx`
- Modify: `src/components/SyncLogDrawer.jsx`

**Step 1: Write minimal implementation**

```jsx
// SettingsPage.jsx
<div className="llm-effective card-tier--hero">

<section className={`llm-provider-card card-tier--focus ${llmForm.activeProvider === "packy" ? "llm-provider-card--active" : ""}`}>

<section className={`llm-provider-card card-tier--focus ${llmForm.activeProvider === "openai" ? "llm-provider-card--active" : ""}`}>

// SyncLogDrawer.jsx
<section className="sync-log-detail card-tier--focus" data-testid="sync-log-detail">
```

**Step 2: Run tests to verify Task 1 passes**

Run: `npm test -- src/test/app.test.jsx`
Expected: PASS for the new tier test (other tests remain green).

### Task 3: Implement tiered styling and stronger hierarchy

**Files:**
- Modify: `src/index.css`

**Step 1: Write minimal implementation**

Add tier tokens in `:root`:

```css
--card-hero-bg: rgba(255, 255, 255, 0.96);
--card-hero-border: rgba(28, 48, 68, 0.22);
--card-hero-shadow: 0 18px 40px rgba(30, 52, 77, 0.16);
--card-focus-bg: rgba(255, 255, 255, 0.88);
--card-focus-border: rgba(28, 48, 68, 0.18);
--card-focus-shadow: 0 12px 28px rgba(30, 52, 77, 0.12);
--card-base-bg: rgba(255, 255, 255, 0.82);
--card-base-border: rgba(28, 48, 68, 0.12);
--card-base-shadow: 0 8px 18px rgba(30, 52, 77, 0.1);
```

Add tier classes:

```css
.card-tier--hero {
  background: var(--card-hero-bg);
  border: 1px solid var(--card-hero-border);
  box-shadow: var(--card-hero-shadow);
}

.card-tier--focus {
  background: var(--card-focus-bg);
  border: 1px solid var(--card-focus-border);
  box-shadow: var(--card-focus-shadow);
}

.card-tier--base {
  background: var(--card-base-bg);
  border: 1px solid var(--card-base-border);
  box-shadow: var(--card-base-shadow);
}
```

Update `.llm-effective` and `.sync-log-detail` to enhance separators/contrast (remove dashed border, add row dividers, polish `pre` background, update header separator).

**Step 2: Run tests**

Run: `npm test -- src/test/app.test.jsx`
Expected: PASS.

**Step 3: Manual visual check**

Run: `npm run dev`
Expected: LLM config cards and sync log detail show clear hierarchy and stronger card depth.

**Step 4: Commit**

```bash
git add src/components/SettingsPage.jsx src/components/SyncLogDrawer.jsx src/index.css src/test/app.test.jsx
git commit -m "style: strengthen card hierarchy for LLM config and logs"
```
