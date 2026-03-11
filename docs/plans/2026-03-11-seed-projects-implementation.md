# Seed Projects Initialization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add repo-committed seed project and crawl profile JSON files that initialize local data only when `backend/data/*.json` is missing.

**Architecture:** Introduce `backend/seed/projects.json` and `backend/seed/crawl_profiles.json`, and update `JsonStore._load_json` to load from seed files when the corresponding `backend/data/` file does not exist. Add tests to ensure seed loading occurs only on first run and never overwrites existing local data.

**Tech Stack:** Python (Flask backend), JSON store, pytest.

---

### Task 1: Add failing tests for seed initialization

**Files:**
- Modify: `backend/tests/test_storage.py`

**Step 1: Write the failing tests**

```python
def test_seed_projects_loaded_when_data_missing(tmp_path):
    from backend.storage import JsonStore

    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "projects.json").write_text('[{"id":"seed","name":"Seed","repo":"","docs_url":"https://example.com","enabled":true,"release_area_enabled":false,"docs_area_enabled":true,"sync_interval_minutes":60,"created_at":"2026-03-11T00:00:00Z","updated_at":"2026-03-11T00:00:00Z"}]', encoding="utf-8")
    (seed_dir / "crawl_profiles.json").write_text('{"seed":{"entry_urls":["https://example.com"],"allowed_path_prefixes":["/"],"blocked_path_prefixes":[],"max_depth":3,"max_pages":40,"expand_mode":"auto","category_hints":[],"discovery_prompt":"","classification_prompt":""}}', encoding="utf-8")

    store = JsonStore(tmp_path)
    store.seed_dir = seed_dir
    snapshot = store.load_all()

    assert snapshot["projects"][0]["id"] == "seed"
    assert snapshot["crawl_profiles"]["seed"]["entry_urls"] == ["https://example.com"]


def test_seed_projects_not_overwrite_existing_data(tmp_path):
    from backend.storage import JsonStore

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "projects.json").write_text('[{"id":"local","name":"Local","repo":"","docs_url":"","enabled":true,"release_area_enabled":false,"docs_area_enabled":false,"sync_interval_minutes":60,"created_at":"2026-03-11T00:00:00Z","updated_at":"2026-03-11T00:00:00Z"}]', encoding="utf-8")
    (data_dir / "crawl_profiles.json").write_text('{"local":{"entry_urls":[],"allowed_path_prefixes":[],"blocked_path_prefixes":[],"max_depth":3,"max_pages":40,"expand_mode":"auto","category_hints":[],"discovery_prompt":"","classification_prompt":""}}', encoding="utf-8")

    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "projects.json").write_text('[{"id":"seed","name":"Seed","repo":"","docs_url":"https://example.com","enabled":true,"release_area_enabled":false,"docs_area_enabled":true,"sync_interval_minutes":60,"created_at":"2026-03-11T00:00:00Z","updated_at":"2026-03-11T00:00:00Z"}]', encoding="utf-8")
    (seed_dir / "crawl_profiles.json").write_text('{"seed":{"entry_urls":["https://example.com"],"allowed_path_prefixes":["/"],"blocked_path_prefixes":[],"max_depth":3,"max_pages":40,"expand_mode":"auto","category_hints":[],"discovery_prompt":"","classification_prompt":""}}', encoding="utf-8")

    store = JsonStore(data_dir)
    store.seed_dir = seed_dir
    snapshot = store.load_all()

    assert snapshot["projects"][0]["id"] == "local"
    assert "seed" not in snapshot["crawl_profiles"]
```

**Step 2: Run the tests**

Run: `python3 -m pytest backend/tests/test_storage.py::test_seed_projects_loaded_when_data_missing -v`  
Expected: FAIL (seed logic missing).

---

### Task 2: Add seed JSON files

**Files:**
- Create: `backend/seed/projects.json`
- Create: `backend/seed/crawl_profiles.json`

**Step 1: Create seed files**

Populate `projects.json` with:
- CUDA 工具链 (docs-only)
- 昇腾 CANN (docs-only)
- MindSpore (docs-only)
- Existing default projects (OpenClaw, Kubernetes, NVIDIA GPU Operator, Cilium, iPerf3, vLLM, SGLang, KTransformers)

Populate `crawl_profiles.json` with the corresponding profiles, including Kubernetes’s concept entry list.

**Step 2: Run the tests**

Run: `python3 -m pytest backend/tests/test_storage.py::test_seed_projects_loaded_when_data_missing -v`  
Expected: still FAIL (JsonStore not using seeds).

---

### Task 3: Wire seed initialization into JsonStore

**Files:**
- Modify: `backend/storage.py`

**Step 1: Implement seed support**

- Add `self.seed_dir` defaulting to `backend/seed`
- In `_load_json`, when the target file does not exist:
  - If a matching seed file exists, load and write it to the data path
  - Otherwise use the current default value

**Step 2: Run tests**

Run: `python3 -m pytest backend/tests/test_storage.py::test_seed_projects_loaded_when_data_missing -v`  
Expected: PASS.

---

### Task 4: Full verification

Run:
- `python3 -m pytest backend/tests -q`

Expected: PASS.

---

### Task 5: Commit

```bash
git add backend/seed/projects.json backend/seed/crawl_profiles.json backend/storage.py backend/tests/test_storage.py
git commit -m "feat: seed docs-only projects on first run"
```
