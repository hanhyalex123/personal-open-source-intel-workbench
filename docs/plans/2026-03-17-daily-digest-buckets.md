# Daily Digest Buckets Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add two configurable daily digest buckets (must-watch 30d, emerging 3d) with recent-update filtering and fix digest source counts.

**Architecture:** Add `daily_digest` config, compute per-project latest activity within a window, partition summaries into two lists, and expose them on `/api/dashboard` while preserving `homepage_projects` for compatibility. Update daily digest progress counts to use actual feed sources.

**Tech Stack:** Python (Flask, pytest), JSON store, React (Vite, Vitest)

---

### Task 1: Add daily_digest config defaults

**Files:**
- Modify: `backend/storage.py`
- Test: `backend/tests/test_storage.py`

**Step 1: Write the failing test**

Add assertions in `test_storage_initializes_default_json_state` to include:
- `config.daily_digest.must_watch_project_ids == []`
- `config.daily_digest.emerging_project_ids == []`
- `config.daily_digest.must_watch_days == 30`
- `config.daily_digest.emerging_days == 3`

**Step 2: Run test to verify it fails**

Run: `/opt/homebrew/anaconda3/bin/python3 -m pytest backend/tests/test_storage.py -q -k default_json_state`
Expected: FAIL (missing keys)

**Step 3: Write minimal implementation**

In `backend/storage.py`:
- Add `DEFAULT_DAILY_DIGEST` block
- Extend `DEFAULT_CONFIG` with `daily_digest`
- Update `normalize_config` to return `daily_digest` with defaults

**Step 4: Run test to verify it passes**

Run: `/opt/homebrew/anaconda3/bin/python3 -m pytest backend/tests/test_storage.py -q -k default_json_state`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/storage.py backend/tests/test_storage.py
git commit -m "feat: add daily digest config defaults"
```

---

### Task 2: Partition daily summaries into must-watch and emerging

**Files:**
- Modify: `backend/daily_summary.py`
- Test: `backend/tests/test_daily_summary.py`

**Step 1: Write the failing test**

Add a test for a snapshot with 3 projects:
- A must-watch project updated within 30 days → appears in must_watch
- A must-watch project updated 40 days ago → not included
- An emerging project updated within 3 days → appears in emerging
- An emerging project updated 10 days ago → not included

Test should assert:
- returned structure has `must_watch_projects` and `emerging_projects`
- each list contains correct project_ids

**Step 2: Run test to verify it fails**

Run: `/opt/homebrew/anaconda3/bin/python3 -m pytest backend/tests/test_daily_summary.py -q -k digest_buckets`
Expected: FAIL (function missing)

**Step 3: Write minimal implementation**

In `backend/daily_summary.py`:
- Add helper `project_latest_activity_at(summary)` (use `evidence_items` published_at)
- Add `build_daily_digest_buckets(snapshot, summary_date, now_iso)`
  - call existing `build_daily_project_summaries`
  - filter by `daily_digest` config windows
  - return `{ "must_watch_projects": [...], "emerging_projects": [...] }`

**Step 4: Run test to verify it passes**

Run: `/opt/homebrew/anaconda3/bin/python3 -m pytest backend/tests/test_daily_summary.py -q -k digest_buckets`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/daily_summary.py backend/tests/test_daily_summary.py
git commit -m "feat: add daily digest buckets"
```

---

### Task 3: Expose buckets on /api/dashboard

**Files:**
- Modify: `backend/app.py`
- Test: `backend/tests/test_api.py`

**Step 1: Write the failing test**

Add a dashboard test that expects:
- `payload.must_watch_projects` and `payload.emerging_projects`
- `homepage_projects` equals concatenation of those two lists

**Step 2: Run test to verify it fails**

Run: `/opt/homebrew/anaconda3/bin/python3 -m pytest backend/tests/test_api.py -q -k digest_buckets`
Expected: FAIL (fields missing)

**Step 3: Write minimal implementation**

In `backend/app.py`:
- import `build_daily_digest_buckets`
- `_build_homepage_projects` returns list as before
- `dashboard()` adds new fields:
  - `must_watch_projects`
  - `emerging_projects`
  - `homepage_projects` stays as flat list

**Step 4: Run test to verify it passes**

Run: `/opt/homebrew/anaconda3/bin/python3 -m pytest backend/tests/test_api.py -q -k digest_buckets`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app.py backend/tests/test_api.py
git commit -m "feat: expose daily digest buckets"
```

---

### Task 4: Settings UI for must-watch / emerging lists

**Files:**
- Modify: `src/components/SettingsPage.jsx`
- Modify: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Add a test that:
- opens Settings
- selects projects into “老牌必看” and “小项目/新项目/AI”
- saves
- asserts payload contains `daily_digest.must_watch_project_ids` and `daily_digest.emerging_project_ids`

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "daily digest buckets"`
Expected: FAIL

**Step 3: Write minimal implementation**

In `SettingsPage.jsx`:
- add multi-selects for must-watch and emerging
- add day fields (30/3 defaults)
- update `handleDailyDigestSubmit` to call `onConfigSave({ daily_digest: ... })`

**Step 4: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx -t "daily digest buckets"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/components/SettingsPage.jsx src/test/app.test.jsx
git commit -m "feat: add daily digest bucket config ui"
```

---

### Task 5: Fix daily digest source counts

**Files:**
- Modify: `backend/runtime.py`
- Test: `backend/tests/test_sync_status.py`

**Step 1: Write the failing test**

Add/extend a test to assert that daily digest progress uses the number of docs feeds (not project count).

**Step 2: Run test to verify it fails**

Run: `/opt/homebrew/anaconda3/bin/python3 -m pytest backend/tests/test_sync_status.py -q -k daily_digest_sources`
Expected: FAIL

**Step 3: Write minimal implementation**

In `backend/runtime.py`:
- compute `feeds` via `collect_project_sources`
- use `len(feeds)` for `total_sources` in digest progress

**Step 4: Run test to verify it passes**

Run: `/opt/homebrew/anaconda3/bin/python3 -m pytest backend/tests/test_sync_status.py -q -k daily_digest_sources`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/runtime.py backend/tests/test_sync_status.py
git commit -m "fix: align digest source counts"
```

---

### Task 6: End-to-end verification

**Step 1: Backend tests**
Run: `/opt/homebrew/anaconda3/bin/python3 -m pytest backend/tests/test_storage.py backend/tests/test_daily_summary.py backend/tests/test_api.py backend/tests/test_sync_status.py -q`
Expected: PASS

**Step 2: Frontend tests**
Run: `npm test -- src/test/app.test.jsx -t "daily digest buckets|daily ranking config|read events"`
Expected: PASS

**Step 3: Build**
Run: `npm run build`
Expected: PASS

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: daily digest buckets"
```
