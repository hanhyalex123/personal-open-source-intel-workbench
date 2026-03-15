# AI Live Research Assistant Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current AI console with a live-only research assistant that plans queries, retrieves public web evidence, reranks relevance, and returns a Markdown research report.

**Architecture:** Keep the existing `/api/assistant/query` endpoint but replace the internals with a planner-driven live retrieval pipeline. The frontend removes mode switching and renders Markdown plus structured evidence metadata.

**Tech Stack:** Flask, React, Vitest, pytest, requests, browser-assisted fallback extraction, Markdown rendering for React

---

### Task 1: Lock The Current Assistant Behavior Behind Failing Tests

**Files:**
- Modify: `backend/tests/test_api.py`
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing backend tests**

Add tests that assert:
- `openclaw` queries do not return unrelated CUDA evidence
- related cross-project evidence is allowed only when relation text is present
- `/api/assistant/query` returns `report_markdown` instead of the current plain `answer`-centric payload

**Step 2: Run the backend tests to verify they fail**

Run: `../../.venv/bin/python -m pytest -q backend/tests/test_api.py`

Expected: assistant tests fail because the old ranking and payload shape are still active.

**Step 3: Write the failing frontend tests**

Add tests that assert:
- the AI console no longer renders the mode selector
- Markdown headings/lists render in the answer area
- evidence rows show relation and timestamp metadata

**Step 4: Run the frontend tests to verify they fail**

Run: `npm test -- src/test/app.test.jsx`

Expected: FAIL because the UI still uses mode selection and plain text output.

**Step 5: Commit**

```bash
git add backend/tests/test_api.py src/test/app.test.jsx
git commit -m "test: define live research assistant behavior"
```

### Task 2: Add Query Planning And Live Retrieval Pipeline

**Files:**
- Modify: `backend/assistant.py`
- Modify: `backend/prompts.py`
- Modify: `backend/search.py`
- Test: `backend/tests/test_api.py`

**Step 1: Write the failing planner test**

Add a unit/integration test for planner output normalization and query plan application.

**Step 2: Run the targeted backend test**

Run: `../../.venv/bin/python -m pytest -q backend/tests/test_api.py -k assistant`

Expected: FAIL because planner fields and live-only pipeline do not exist.

**Step 3: Implement minimal planner + retrieval orchestration**

Add:
- structured query plan builder
- multi-query live search execution
- result dedupe
- payload fields `applied_plan` and `search_trace`

**Step 4: Re-run targeted backend tests**

Run: `../../.venv/bin/python -m pytest -q backend/tests/test_api.py -k assistant`

Expected: PASS for planner payload and basic retrieval behavior.

**Step 5: Commit**

```bash
git add backend/assistant.py backend/prompts.py backend/search.py backend/tests/test_api.py
git commit -m "feat: add planner-driven live assistant retrieval"
```

### Task 3: Add Evidence Filtering And Browser Fallback

**Files:**
- Modify: `backend/assistant.py`
- Modify: `backend/search.py`
- Test: `backend/tests/test_api.py`

**Step 1: Write failing tests for relevance filtering and fallback behavior**

Add tests for:
- dropping unrelated CUDA evidence for `openclaw`
- allowing related CUDA evidence for `vllm` only when relation is explicit
- browser fallback used when HTTP extraction is weak

**Step 2: Run targeted backend tests**

Run: `../../.venv/bin/python -m pytest -q backend/tests/test_api.py -k assistant`

Expected: FAIL on relevance/fallback assertions.

**Step 3: Implement minimal reranker and fallback extraction**

Implement:
- primary entity boost
- relation-required cross-project acceptance
- fallback extraction path flagging browser usage in `search_trace`

**Step 4: Re-run targeted backend tests**

Run: `../../.venv/bin/python -m pytest -q backend/tests/test_api.py -k assistant`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/assistant.py backend/search.py backend/tests/test_api.py
git commit -m "feat: filter live evidence by project relevance"
```

### Task 4: Generate Markdown Research Reports

**Files:**
- Modify: `backend/prompts.py`
- Modify: `backend/assistant.py`
- Test: `backend/tests/test_api.py`

**Step 1: Write a failing report-format test**

Add an assertion that the assistant response contains Markdown sections like `## 结论摘要`.

**Step 2: Run targeted backend tests**

Run: `../../.venv/bin/python -m pytest -q backend/tests/test_api.py -k assistant`

Expected: FAIL because plain text answer formatting is still returned.

**Step 3: Implement Markdown report generation**

Return:
- `report_markdown`
- `report_outline`
- normalized evidence metadata

**Step 4: Re-run targeted backend tests**

Run: `../../.venv/bin/python -m pytest -q backend/tests/test_api.py -k assistant`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/assistant.py backend/prompts.py backend/tests/test_api.py
git commit -m "feat: return markdown research reports"
```

### Task 5: Redesign The AI Console UI

**Files:**
- Modify: `src/components/AIConsolePage.jsx`
- Modify: `src/App.jsx`
- Modify: `src/index.css`
- Modify: `src/lib/api.js`
- Test: `src/test/app.test.jsx`

**Step 1: Write/extend failing frontend tests**

Cover:
- no mode selector
- Markdown report rendering
- evidence rows with timestamp + relation metadata
- optional search trace block

**Step 2: Run the frontend test**

Run: `npm test -- src/test/app.test.jsx`

Expected: FAIL

**Step 3: Implement minimal UI changes**

Implement:
- live-only hero copy
- Markdown render area
- evidence metadata layout
- trace disclosure

**Step 4: Re-run the frontend test**

Run: `npm test -- src/test/app.test.jsx`

Expected: PASS

**Step 5: Commit**

```bash
git add src/components/AIConsolePage.jsx src/App.jsx src/index.css src/lib/api.js src/test/app.test.jsx
git commit -m "feat: redesign ai console for live research"
```

### Task 6: Verify End-To-End And Prepare Merge

**Files:**
- Verify only

**Step 1: Run backend suite**

Run: `../../.venv/bin/python -m pytest -q`

Expected: PASS or only documented known failures outside this feature.

**Step 2: Run frontend suite**

Run: `npm test`

Expected: PASS

**Step 3: Build frontend**

Run: `npm run build`

Expected: PASS

**Step 4: Review git status and summarize remaining risks**

Run: `git status --short`

Expected: only intended changes tracked in this branch.

**Step 5: Commit**

```bash
git add .
git commit -m "feat: ship live research assistant"
```
