# Docs-Only Projects Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add CUDA 工具链、昇腾 CANN、MindSpore as docs-only projects (docs enabled, release disabled) using official docs entry points.

**Architecture:** Update the JSON-based project registry and crawl profiles, and add a small unit test to ensure docs-only projects produce docs feeds without repo releases. No new crawler logic required.

**Tech Stack:** Flask backend, JSON store (`backend/data/*.json`), pytest.

---

### Task 1: Add failing test for docs-only project sources

**Files:**
- Modify: `backend/tests/test_projects.py`

**Step 1: Write the failing test**

```python
def test_collect_project_sources_docs_only_project_returns_docs_feed_only():
    from backend.projects import collect_project_sources

    repos, feeds = collect_project_sources(
        [
            {
                "id": "cuda-toolkit",
                "name": "CUDA 工具链",
                "repo": "",
                "docs_url": "https://docs.nvidia.com/cuda/",
                "enabled": True,
                "release_area_enabled": False,
                "docs_area_enabled": True,
            }
        ],
        {
            "cuda-toolkit": {
                "entry_urls": ["https://docs.nvidia.com/cuda/"],
                "allowed_path_prefixes": ["/cuda"],
                "blocked_path_prefixes": [],
                "max_depth": 3,
            }
        },
    )

    assert repos == []
    assert feeds == [
        {
            "id": "cuda-toolkit:docs",
            "project_id": "cuda-toolkit",
            "name": "CUDA 工具链 文档",
            "url": "https://docs.nvidia.com/cuda/",
            "type": "page",
            "entry_urls": ["https://docs.nvidia.com/cuda/"],
            "allowed_path_prefixes": ["/cuda"],
            "blocked_path_prefixes": [],
            "max_depth": 3,
            "max_pages": 40,
            "category_hints": [],
            "discovery_prompt": "",
            "classification_prompt": "",
        }
    ]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_projects.py::test_collect_project_sources_docs_only_project_returns_docs_feed_only -v`  
Expected: FAIL (docs-only behavior not guaranteed yet).

---

### Task 2: Add docs-only projects to registry and crawl profiles

**Files:**
- Modify: `backend/data/projects.json`
- Modify: `backend/data/crawl_profiles.json`

**Step 1: Update project registry**

Add three entries (release disabled, docs enabled):

```json
{
  "id": "cuda-toolkit",
  "name": "CUDA 工具链",
  "github_url": "",
  "repo": "",
  "docs_url": "https://docs.nvidia.com/cuda/",
  "enabled": true,
  "release_area_enabled": false,
  "docs_area_enabled": true,
  "sync_interval_minutes": 60,
  "created_at": "2026-03-11T00:00:00Z",
  "updated_at": "2026-03-11T00:00:00Z"
}
```

```json
{
  "id": "ascend-cann",
  "name": "昇腾 CANN",
  "github_url": "",
  "repo": "",
  "docs_url": "https://www.hiascend.com/document",
  "enabled": true,
  "release_area_enabled": false,
  "docs_area_enabled": true,
  "sync_interval_minutes": 60,
  "created_at": "2026-03-11T00:00:00Z",
  "updated_at": "2026-03-11T00:00:00Z"
}
```

```json
{
  "id": "mindspore",
  "name": "MindSpore",
  "github_url": "",
  "repo": "",
  "docs_url": "https://www.mindspore.cn/docs/",
  "enabled": true,
  "release_area_enabled": false,
  "docs_area_enabled": true,
  "sync_interval_minutes": 60,
  "created_at": "2026-03-11T00:00:00Z",
  "updated_at": "2026-03-11T00:00:00Z"
}
```

**Step 2: Add crawl profiles**

Add matching entries in `crawl_profiles.json`:

```json
"cuda-toolkit": {
  "entry_urls": ["https://docs.nvidia.com/cuda/"],
  "allowed_path_prefixes": ["/cuda"],
  "blocked_path_prefixes": [],
  "max_depth": 3,
  "max_pages": 40,
  "category_hints": [],
  "discovery_prompt": "",
  "classification_prompt": ""
}
```

```json
"ascend-cann": {
  "entry_urls": ["https://www.hiascend.com/document"],
  "allowed_path_prefixes": ["/document"],
  "blocked_path_prefixes": [],
  "max_depth": 3,
  "max_pages": 40,
  "category_hints": [],
  "discovery_prompt": "",
  "classification_prompt": ""
}
```

```json
"mindspore": {
  "entry_urls": ["https://www.mindspore.cn/docs/"],
  "allowed_path_prefixes": ["/docs"],
  "blocked_path_prefixes": [],
  "max_depth": 3,
  "max_pages": 40,
  "category_hints": [],
  "discovery_prompt": "",
  "classification_prompt": ""
}
```

---

### Task 3: Make the test pass

**Files:**
- Modify: `backend/projects.py` (if needed)

**Step 1: Ensure docs-only projects do not add repos**

If the test fails because empty `repo` is still being added, update `collect_project_sources()` to skip repos when `release_area_enabled` is false or `repo` is empty.

**Step 2: Run the test**

Run: `python3 -m pytest backend/tests/test_projects.py::test_collect_project_sources_docs_only_project_returns_docs_feed_only -v`  
Expected: PASS.

---

### Task 4: Full verification

Run:
- `python3 -m pytest backend/tests -q`

Expected: PASS.

---

### Task 5: Commit

```bash
git add backend/tests/test_projects.py backend/data/projects.json backend/data/crawl_profiles.json backend/projects.py
git commit -m "feat: add docs-only projects for CUDA, Ascend CANN, MindSpore"
```
