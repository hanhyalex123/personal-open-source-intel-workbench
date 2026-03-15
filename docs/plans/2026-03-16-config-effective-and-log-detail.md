# Effective Config Display + Log Detail Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show effective LLM config values (including env-derived values) with masked keys, and add per-event log detail view in sync logs.

**Architecture:** Extend backend config response to include effective values and key source metadata; update Settings UI to display effective values; add detail panel in SyncLogDrawer using existing run detail payload.

**Tech Stack:** Flask backend, React frontend, Pytest + Vitest.

---

### Task 1: Add failing backend test for effective config values

**Files:**
- Modify: `backend/tests/test_api.py`

**Step 1: Write the failing test**

```python

def test_config_response_includes_effective_values_and_key_source(tmp_path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

    monkeypatch.setenv("PACKY_API_KEY", "sk-packy-1234567890")
    monkeypatch.setenv("PACKY_API_URL", "https://env.packy.test/v1/messages")
    monkeypatch.setenv("PACKY_MODEL", "claude-opus-4-6")

    store = JsonStore(tmp_path)
    app = create_app(store=store)
    client = app.test_client()

    response = client.get("/api/config")
    payload = response.get_json()

    assert payload["llm"]["packy"]["api_key_masked"].startswith("sk-p")
    assert payload["llm"]["packy"]["api_key_source"] == "env"
    assert payload["llm"]["packy"]["effective_api_url"] == "https://env.packy.test/v1/messages"
    assert payload["llm"]["packy"]["effective_model"] == "claude-opus-4-6"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_api.py::test_config_response_includes_effective_values_and_key_source -v`
Expected: FAIL (fields missing).

**Step 3: Commit (tests only)**

```bash
git add backend/tests/test_api.py
git commit -m "test: require effective config values in api"
```

---

### Task 2: Implement effective config values in backend

**Files:**
- Modify: `backend/llm.py`
- Modify: `backend/app.py`

**Step 1: Add helpers in `build_llm_config_view`**

- Compute effective values using env fallback.
- Add `api_key_masked` + `api_key_source`.
- Add `effective_api_url`, `effective_model`, `effective_protocol`, `effective_provider`.

**Step 2: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_api.py::test_config_response_includes_effective_values_and_key_source -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/llm.py backend/app.py
git commit -m "feat: expose effective config values and key source"
```

---

### Task 3: Add failing frontend test for effective config display

**Files:**
- Modify: `src/test/app.test.jsx`

**Step 1: Write failing test**

Assert Settings page shows masked key and effective value label for Packy/OpenAI.

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL (UI missing).

**Step 3: Commit (tests only)**

```bash
git add src/test/app.test.jsx
git commit -m "test: cover effective config display"
```

---

### Task 4: Implement Settings UI effective display

**Files:**
- Modify: `src/components/SettingsPage.jsx`

**Step 1: Add display rows**

Add “生效值” section showing effective API URL, model, protocol, provider, and masked key + source.

**Step 2: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx`
Expected: PASS

**Step 3: Commit**

```bash
git add src/components/SettingsPage.jsx
git commit -m "feat: show effective config values"
```

---

### Task 5: Add failing test for log detail view

**Files:**
- Modify: `src/test/app.test.jsx`

**Step 1: Write failing test**

Assert clicking “查看详情” opens detail panel with structured fields.

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL

**Step 3: Commit (tests only)**

```bash
git add src/test/app.test.jsx
git commit -m "test: cover log event detail view"
```

---

### Task 6: Implement log detail view in SyncLogDrawer

**Files:**
- Modify: `src/components/SyncLogDrawer.jsx`
- Modify: `src/index.css` (if needed for layout)

**Step 1: Add detail panel state + rendering**

- Store selected event.
- Render structured view + `<details>` JSON.

**Step 2: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx`
Expected: PASS

**Step 3: Commit**

```bash
git add src/components/SyncLogDrawer.jsx src/index.css
git commit -m "feat: add sync log event detail view"
```

---

### Task 7: Full verification

**Step 1: Run backend tests**

Run: `python -m pytest -q`
Expected: PASS

**Step 2: Run frontend tests**

Run: `npm test`
Expected: PASS

**Step 3: Build**

Run: `npm run build`
Expected: PASS
