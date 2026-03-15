# LLM Provider Toggles + Codex Compatibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Packy/OpenAI enable toggles, skip disabled providers in selection, and treat `protocol=codex` as OpenAI Responses wire format.

**Architecture:** Add `enabled` flags to stored provider config, filter providers by `enabled` in backend selection, surface toggles in Settings UI, and extend protocol mapping for codex to the Responses wire format.

**Tech Stack:** Python backend (LLM selection + config), React + Vite frontend, Vitest for UI tests, Pytest for backend tests.

---

### Task 1: Add failing tests for provider enabled flags in config normalization

**Files:**
- Modify: `backend/tests/test_storage.py`

**Step 1: Write the failing test**

```python

def test_normalize_config_preserves_provider_enabled_flags_and_forces_live_mode():
    cfg = {
        "llm": {
            "mode": "local",
            "packy": {"enabled": False, "model": "claude-opus-4-6"},
            "openai": {"enabled": True, "model": "gpt-5.3-codex"},
        }
    }
    normalized = normalize_config(cfg)
    assert normalized["llm"]["mode"] == "live"
    assert normalized["llm"]["packy"]["enabled"] is False
    assert normalized["llm"]["openai"]["enabled"] is True
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_storage.py::test_normalize_config_preserves_provider_enabled_flags_and_forces_live_mode -v`
Expected: FAIL because `enabled` is dropped or missing.

**Step 3: Commit (tests only)**

```bash
git add backend/tests/test_storage.py
git commit -m "test: cover provider enabled flags in config"
```

---

### Task 2: Implement enabled flags in storage defaults and normalization

**Files:**
- Modify: `backend/storage.py`

**Step 1: Write minimal implementation**

Add `enabled: True` to `DEFAULT_LLM_CONFIG` for `packy` and `openai`, and preserve `enabled` in `normalize_config` when present.

**Step 2: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_storage.py::test_normalize_config_preserves_provider_enabled_flags_and_forces_live_mode -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/storage.py
git commit -m "feat: add provider enabled flags to config"
```

---

### Task 3: Add failing tests for skipping disabled providers

**Files:**
- Modify: `backend/tests/test_llm_requests.py`

**Step 1: Write the failing tests**

```python

def test_get_llm_settings_skips_disabled_fallback_provider():
    cfg = _sample_config()
    cfg["llm"]["provider"] = "packy"
    cfg["llm"]["packy"]["enabled"] = True
    cfg["llm"]["openai"]["enabled"] = False
    settings = get_llm_settings(cfg)
    assert settings["fallback"] == {}


def test_get_llm_settings_uses_enabled_openai_when_packy_disabled():
    cfg = _sample_config()
    cfg["llm"]["provider"] = "packy"
    cfg["llm"]["packy"]["enabled"] = False
    cfg["llm"]["openai"]["enabled"] = True
    settings = get_llm_settings(cfg)
    assert settings["provider"] == "openai"
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest backend/tests/test_llm_requests.py::test_get_llm_settings_skips_disabled_fallback_provider backend/tests/test_llm_requests.py::test_get_llm_settings_uses_enabled_openai_when_packy_disabled -v`
Expected: FAIL because disabled providers are still selected.

**Step 3: Commit (tests only)**

```bash
git add backend/tests/test_llm_requests.py
git commit -m "test: cover skipping disabled providers"
```

---

### Task 4: Implement provider enabled filtering in backend selection

**Files:**
- Modify: `backend/llm.py`

**Step 1: Write minimal implementation**

- Add helper `_is_provider_enabled(config, provider)`.
- Skip disabled providers in primary and fallback selection.
- When a provider is disabled, return empty provider config in the response shape.

**Step 2: Run tests to verify they pass**

Run: `python -m pytest backend/tests/test_llm_requests.py::test_get_llm_settings_skips_disabled_fallback_provider backend/tests/test_llm_requests.py::test_get_llm_settings_uses_enabled_openai_when_packy_disabled -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/llm.py
git commit -m "feat: skip disabled providers in selection"
```

---

### Task 5: Add failing test for codex protocol mapping

**Files:**
- Modify: `backend/tests/test_llm_requests.py`

**Step 1: Write the failing test**

```python

def test_analyze_event_uses_codex_protocol_with_responses_wire_format():
    cfg = _sample_config()
    cfg["llm"]["provider"] = "openai"
    cfg["llm"]["openai"]["protocol"] = "codex"
    payload = build_llm_request(cfg, prompt="ping")
    assert payload["wire_api"] == "responses"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_llm_requests.py::test_analyze_event_uses_codex_protocol_with_responses_wire_format -v`
Expected: FAIL because `codex` is not recognized.

**Step 3: Commit (tests only)**

```bash
git add backend/tests/test_llm_requests.py
git commit -m "test: cover codex protocol mapping"
```

---

### Task 6: Implement codex protocol mapping

**Files:**
- Modify: `backend/llm.py`

**Step 1: Write minimal implementation**

Treat `protocol=codex` like `openai-responses` for wire format selection.

**Step 2: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_llm_requests.py::test_analyze_event_uses_codex_protocol_with_responses_wire_format -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/llm.py
git commit -m "feat: map codex to responses wire format"
```

---

### Task 7: Add failing UI test for provider toggles in Settings

**Files:**
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Assert that the Settings save payload includes `enabled` fields for Packy/OpenAI based on checkbox state.

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx`
Expected: FAIL because toggles do not exist yet.

**Step 3: Commit (tests only)**

```bash
git add src/test/app.test.jsx
git commit -m "test: cover provider enable toggles"
```

---

### Task 8: Implement Settings UI toggles and payload wiring

**Files:**
- Modify: `src/components/SettingsPage.jsx`

**Step 1: Write minimal implementation**

- Add `enabled` fields to Packy/OpenAI form state.
- Initialize from config response.
- Add two checkboxes: “启用 Packy 通道”, “启用 OpenAI 通道”.
- Include `enabled` in save payload.

**Step 2: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx`
Expected: PASS

**Step 3: Commit**

```bash
git add src/components/SettingsPage.jsx
git commit -m "feat: add provider enable toggles to settings"
```

---

### Task 9: Full verification

**Step 1: Run backend tests**

Run: `python -m pytest -q`
Expected: PASS

**Step 2: Run frontend tests**

Run: `npm test`
Expected: PASS

**Step 3: Build**

Run: `npm run build`
Expected: PASS

**Step 4: Commit final verification note (optional)**

```bash
git status -sb
```

---

## Notes
- If both providers are disabled, return a clear error from selection logic (e.g., “No LLM provider enabled”).
- Keep existing config keys intact to avoid breaking older configs.
