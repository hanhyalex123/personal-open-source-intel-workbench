# Sync Concurrency Design

**Goal**
Make sync noticeably faster by running GitHub release pulls and docs crawling in parallel while preserving current progress/status reporting and failure isolation.

**Context**
The current sync pipeline processes sources sequentially. Large docs sites and GitHub rate limits make the hourly sync feel “stuck.” We already separated hourly incremental (releases only) from daily docs crawling. Concurrency should apply to both release sources and docs sources when they are included in a run.

## Requirements
- Run sources in parallel with a configurable concurrency limit (default 4).
- Preserve existing status fields: `processed_sources`, `current_label`, `last_heartbeat_at` updates.
- Single-source failures must not fail the whole run.
- Keep data model unchanged for events/analyses.
- No async rewrite.

## Non-Goals
- Per-page concurrency inside a single docs site.
- Replacing requests with async HTTP clients.
- Reworking scheduler or UI beyond the sync status label.

## Approach Options
1. **Thread pool by source (Recommended)**
   - Each repo/docs source becomes a task in a ThreadPoolExecutor.
   - Tasks fetch + analyze; shared state guarded by a lock.
   - Low change risk, keeps existing API contracts.

2. **Thread pool + per-source timeout budget**
   - Same as option 1 but cancel tasks that exceed a time budget.
   - Slightly more logic but avoids “never finishing” sources.

3. **Async rewrite (Not now)**
   - Best throughput but high complexity and risk.

## Chosen Design
**Option 1 with a lightweight per-source timeout guard.**

### Data Flow
- `run_sync_once` receives `repos` + `feeds` and a `max_workers` + `source_timeout`.
- Build tasks for each source (repo or docs feed).
- Run tasks in a thread pool.
- Each task:
  - emits a “started” progress update
  - pulls items, normalizes, decides if analysis is needed, and writes to shared `events`/`analyses` with a lock
  - increments shared counters
- The orchestrator increments `processed_sources` when each task completes.

### Progress & Status
- `progress_callback` is called:
  - at task start (sets `current_label`, `message`)
  - at task completion (updates `processed_sources` + counters)
- `last_heartbeat_at` continues to update on each progress call.

### Failure Handling
- Exceptions in a single task increment `failed_events` and continue.
- If a task times out, mark it failed and continue.

### Configuration
- Add `sync_concurrency` (default 4)
- Add `sync_source_timeout_seconds` (default 120)
- Stored in config, exposed via API; UI is optional for now.

### Rollout
- Apply to both incremental sync (release sources) and daily docs crawl (doc sources only).
- Manual sync remains the same flow but uses the concurrent runner internally.

### Tests
- Unit test for concurrency config default.
- Unit test that per-source failure does not stop other sources.
- Unit test that a timeout marks a failure and run completes.

