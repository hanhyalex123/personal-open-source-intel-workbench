# Sync Job Monitor Design

## Goal
Refactor the sync monitor into a Job-oriented view so users can reason about one incremental sync or one daily digest at a time, similar to Kubernetes Job mental models. In the same pass, make sync failures diagnosable at the Job/source level instead of looking like a single system-wide red alert.

## User Problem
The current page mixes live global status with incremental summary counters. That makes a completed run with some source failures look like the whole system is failing. It also blends manual sync and daily digest into one status surface, so users cannot easily answer:

- Which Job is running now?
- Which Job produced these failures?
- Is the system broken, or did specific sources fail inside an otherwise completed Job?
- Where do I inspect this specific run?

## Product Direction
Treat each incremental sync and each daily digest as an independent Job.

- One manual sync request creates one Job record with its own lifecycle.
- One scheduled incremental sync creates one Job record.
- One scheduled daily digest creates one Job record.
- The monitor page selects one Job as the primary focus.
- Logs and failure drilldown are always scoped to the selected Job.

## Recommended UX

### 1. Current Job Card
At the top of the page, show a single primary Job card.

- If a Job is currently `running`, select that Job.
- Otherwise, select the most recent Job.
- The card shows Job type, status, current phase, current project, source progress, metrics, timestamps, and log entry point.

This preserves the real-time operational feel while keeping the unit of observation explicit.

### 2. Recent Jobs List
Below the primary card, show recent Jobs as compact list items.

Each item shows:

- Job type
- Job status
- Start/end time
- Core metrics
- A brief status summary

Clicking a Job switches the selected Job in the top card and in the log drawer.

### 3. Job-Scoped Log Drawer
Keep the existing drilldown drawer, but make it clearly Job-scoped.

- It opens against the selected Job.
- It keeps the existing event filters: `all`, `new`, `analyzed`, `failed`, `skipped`.
- History remains available, but it should no longer be the primary mental model because the page itself now provides Job selection.

## Data Model

### Job Summary
Use `/api/sync/runs` as the main source for the monitor page. Each run summary is treated as one Job summary:

- `id`
- `run_kind`
- `status`
- `phase`
- `message`
- `started_at`
- `finished_at`
- `last_heartbeat_at`
- `metrics`

### Job Detail
Use `/api/sync/runs/:id` for the selected Job detail.

- `sources`
- source-level metrics
- event-level analysis and error records

### Sync Status
`/api/sync/status` remains useful, but only as supporting runtime state:

- to confirm current in-flight run metadata
- to support trigger button behavior
- to keep heartbeats accurate when a run is active

The page should no longer derive its primary meaning from the mixed global status payload.

## Failure Semantics
Failures must be expressed at the Job level, not as blanket system failure.

- `status=failed`: the Job itself failed and did not complete normally
- `status=success` with `failed_events > 0`: the Job completed, but some sources or analyses failed
- source `status=failed|timeout`: a particular source failed inside the Job

UI wording should reflect this distinction:

- `运行中`
- `已完成`
- `已完成，含失败项`
- `Job 失败`

Only true Job failure should receive the strongest danger styling.

## Root Cause Investigation Requirement
The monitor redesign alone does not solve the user’s complaint. We also need to locate why current sync runs accumulate failures.

The debugging work should follow this order:

1. Reproduce current failing behavior with stored run data and automated tests.
2. Separate failure classes:
   - source fetch errors
   - analysis/LLM errors
   - timeout errors
   - orchestration errors
3. Verify whether the current “14 failures” are:
   - event-level analysis failures inside otherwise successful Jobs
   - source-level failures
   - stale historical runs being shown as current
   - a counting bug
4. Fix root causes where reproducible in code.
5. If a failure is external and unavoidable, surface the exact reason clearly in the Job/source detail instead of treating it like a generic system failure.

## Testing Strategy

### Frontend
- Selected Job defaults to the running Job, else the most recent Job.
- The top card uses selected Job metrics, not mixed global summary fields.
- Successful Jobs with some failed items render a neutral “completed with failures” state.
- Clicking a historical Job updates the top card and log drawer target.

### Backend
- Run summaries remain available from `/api/sync/runs`.
- Manual sync and scheduled digest are recorded as distinct Job kinds.
- Failed source/error information is preserved in run detail payloads.
- Regression coverage for the failure mode identified during debugging.

## Non-Goals
- Reworking scheduler behavior beyond what is needed to correctly classify Jobs.
- Changing storage format for unrelated dashboard domains.
- Hiding all source failures. The goal is accurate diagnosis, not cosmetic suppression.

## Rollout Notes
- Backward-compatible API changes are preferred.
- The monitor page can migrate to Job-first semantics without disrupting the rest of the dashboard.
- If needed, `sync/status` can remain for other surfaces while the monitor uses `sync/runs` as its primary model.
