# Sync Status Incremental Metrics Design

## Goal
Ensure the homepage “本次合计（全来源）” always reflects the **latest incremental sync summary** (including skipped), even when the current status is showing the daily digest phase. The real-time phase/label/progress should remain live.

## Non-Goals
- Changing log storage format.
- Altering how events are analyzed or skipped.
- Redesigning the UI layout beyond metric sourcing.

## Problem
`/api/sync/status` is a live status snapshot. During manual runs, the status transitions from incremental sync to daily digest. In the digest phase, the status fields used for summary metrics (new/analyzed/failed/skipped) are not updated, so the homepage totals no longer match the incremental run that just completed. The logs show accurate skipped counts, but the homepage totals can look “wrong.”

## Approach (Recommended)
Add a stable summary object on the backend for “last incremental metrics” and have the frontend use it for “本次合计（全来源）.”

### Backend
- Extend sync status payload to include:
  - `last_incremental_metrics`: `{ new_events, analyzed_events, failed_events, skipped_events, total_sources, processed_sources, finished_at }`
- Populate the field when incremental sync completes (scheduled or manual), using the incremental result.
- This value should persist across the daily digest phase and be returned in subsequent `/api/sync/status` calls.

### Frontend
- In the sync status panel, compute the “本次合计（全来源）” values from `status.last_incremental_metrics` when present.
- If the field is missing (first run), fall back to the current `status.*` metrics as before.
- Keep “当前阶段 / 当前项目 / 来源进度 / 心跳状态 / 最后心跳” tied to the live status.

## Data Flow
1. Incremental sync completes → produces result summary.
2. Sync coordinator stores summary into status (`last_incremental_metrics`).
3. Status endpoint returns live state + stable incremental summary.
4. Frontend displays totals from `last_incremental_metrics` while phase indicators remain live.

## Error Handling
- If `last_incremental_metrics` is missing, show “0” or “暂无” as today.
- If incremental run fails, retain the previous `last_incremental_metrics` and surface error in status.

## Testing
- Backend unit test verifying `last_incremental_metrics` is set after incremental completion.
- Frontend test verifying totals prefer `last_incremental_metrics` and fallback works.

## Rollout
- Backward compatible: existing clients ignore new fields.
- UI change is purely a data-source swap for totals.
