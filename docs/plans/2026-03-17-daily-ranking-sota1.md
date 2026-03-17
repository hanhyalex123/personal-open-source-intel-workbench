# Daily Ranking (SOTA1) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a configurable SOTA1 daily ranking pipeline (multi-objective scoring + MMR diversity) with 2-day read decay and read-event tracking.

**Architecture:** Add a `daily_ranking` config block, store `read_events`, compute `base_score` per project, apply read decay, and re-rank with MMR based on diversity keys. Expose a read-event API and mark reads from the cover card, affecting future two-day ordering.

**Tech Stack:** Python (Flask, pytest), JSON store, React (Vite, Vitest)

---

### Task 1: Add daily ranking config defaults and read-event storage

**Files:**
- Modify: `backend/storage.py`
- Test: `backend/tests/test_storage.py`

**Step 1: Write the failing test**

Add assertions in `test_storage_initializes_default_json_state` to include:
- `config.daily_ranking` with defaults
- `read_events` empty list in snapshot

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_storage.py -q -k default_json_state`
Expected: FAIL (missing keys)

**Step 3: Write minimal implementation**

Update `DEFAULT_CONFIG` and `normalize_config` in `backend/storage.py` to include `daily_ranking` defaults. Extend `load_all` to include `read_events`. Add `read_events_path` plus load/save helpers.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_storage.py -q -k default_json_state`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/storage.py backend/tests/test_storage.py
git commit -m "feat: add daily ranking defaults and read events"
```

---

### Task 2: Read-event API

**Files:**
- Modify: `backend/app.py`
- Modify: `backend/storage.py`
- Test: `backend/tests/test_api.py`

**Step 1: Write the failing test**

Add test to POST `/api/read-events` then GET `/api/read-events` and assert:
- event is persisted
- schema includes `project_id`, `event_id`, `read_at`

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_api.py -q -k read_events`
Expected: FAIL (endpoint missing)

**Step 3: Write minimal implementation**

Implement:
- `GET /api/read-events`
- `POST /api/read-events` (append to store, auto-fill `read_at` if missing)

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_api.py -q -k read_events`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app.py backend/storage.py backend/tests/test_api.py
git commit -m "feat: add read events api"
```

---

### Task 3: Daily ranking scoring + read decay

**Files:**
- Create: `backend/daily_ranking.py`
- Modify: `backend/daily_summary.py`
- Test: `backend/tests/test_daily_summary.py`

**Step 1: Write the failing test**

Add tests for:
- base_score ranking uses importance/recency/evidence/source
- read decay: if project read within 2 days, score is multiplied by `read_decay_factor`

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_daily_summary.py -q -k daily_ranking`
Expected: FAIL (module missing)

**Step 3: Write minimal implementation**

Implement `backend/daily_ranking.py`:
- `compute_base_score(summary, weights, now_iso)`
- `apply_read_decay(base_score, project_id, read_events, now_iso, read_decay_days, read_decay_factor)`

Modify `build_daily_project_summaries` to attach `ranking_score` and use it in ranking stage.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_daily_summary.py -q -k daily_ranking`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/daily_ranking.py backend/daily_summary.py backend/tests/test_daily_summary.py
git commit -m "feat: add daily ranking base score and read decay"
```

---

### Task 4: MMR diversity re-rank

**Files:**
- Modify: `backend/daily_ranking.py`
- Modify: `backend/daily_summary.py`
- Test: `backend/tests/test_daily_summary.py`

**Step 1: Write the failing test**

Add a test where two top items share identical `tags/source/category`; assert MMR lifts a different project earlier when `mmr_lambda` is set to default.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_daily_summary.py -q -k mmr_rerank`
Expected: FAIL (MMR not applied)

**Step 3: Write minimal implementation**

Implement MMR in `daily_ranking.py`:
- `rerank_with_mmr(items, lambda, diversity_keys)`
- use Jaccard similarity over diversity keys

Wire it into `build_daily_project_summaries` (final ordering).

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_daily_summary.py -q -k mmr_rerank`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/daily_ranking.py backend/daily_summary.py backend/tests/test_daily_summary.py
git commit -m "feat: add mmr diversity reranking"
```

---

### Task 5: Frontend mark-as-read + config UI

**Files:**
- Modify: `src/lib/api.js`
- Modify: `src/components/ProjectSummaryCard.jsx`
- Modify: `src/components/IntelOverviewPage.jsx`
- Modify: `src/components/SettingsPage.jsx`
- Test: `src/test/app.test.jsx`

**Step 1: Write the failing test**

Add tests for:
- Clicking a cover card posts to `/api/read-events`
- Settings page can edit `daily_ranking` parameters and save

**Step 2: Run test to verify it fails**

Run: `npm test -- src/test/app.test.jsx -t "read events|daily ranking config"`
Expected: FAIL

**Step 3: Write minimal implementation**

- Add `postReadEvent` in `src/lib/api.js`
- On card click: call `postReadEvent({project_id, event_id})`
- Add config fields to settings page for `daily_ranking`

**Step 4: Run test to verify it passes**

Run: `npm test -- src/test/app.test.jsx -t "read events|daily ranking config"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lib/api.js src/components/ProjectSummaryCard.jsx src/components/IntelOverviewPage.jsx src/components/SettingsPage.jsx src/test/app.test.jsx
git commit -m "feat: add read events and daily ranking config ui"
```

---

### Task 6: End-to-end verification

**Files:**
- None

**Step 1: Run backend tests**

Run: `python3 -m pytest backend/tests/test_storage.py backend/tests/test_api.py backend/tests/test_daily_summary.py -q`
Expected: PASS

**Step 2: Run frontend tests**

Run: `npm test -- src/test/app.test.jsx -t "read events|daily ranking config|daily ranking"`
Expected: PASS

**Step 3: Run build**

Run: `npm run build`
Expected: PASS

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: sota1 daily ranking pipeline"
```
