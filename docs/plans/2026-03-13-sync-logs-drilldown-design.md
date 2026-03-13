# Sync Logs Drilldown & Radar Simplification Design

## Context
The current Radar panel shows aggregate counters (new/analyzed/failed) but provides no drilldown. Backend only writes access logs, so users cannot inspect per-source or per-event outcomes. This makes high failure rates and stalled runs opaque.

## Goals
- Default to showing **current run** details when clicking counters.
- Provide **event-level** visibility (title/version/url, analysis summary, error).
- Add **history** view for recent runs.
- Simplify Radar UI to the essentials without losing key status cues.
- Allow **clear logs** to start from zero.

## Non-Goals
- Full-text search across historical runs.
- Long-term durable storage beyond recent runs.
- Rewriting sync/analyze logic outside of logging and UI hooks.

## Recommended Approach
Store structured per-run logs in a local JSON file and expose read/clear endpoints. Frontend opens a log drawer with run summary + event-level list, defaulting to the current run.

## Data Model (Local JSON)
File: `backend/data/sync_runs.json`

```json
{
  "runs": [
    {
      "id": "run_2026-03-13T07:23:20Z_manual",
      "run_kind": "manual | scheduled-incremental | scheduled-digest",
      "status": "running | success | failed",
      "phase": "queued | incremental | daily_digest | completed | failed",
      "message": "string",
      "started_at": "ISO8601",
      "finished_at": "ISO8601 | null",
      "last_heartbeat_at": "ISO8601 | null",
      "metrics": {
        "total_sources": 26,
        "processed_sources": 13,
        "new_events": 6,
        "analyzed_events": 4,
        "failed_events": 2
      },
      "sources": [
        {
          "kind": "repo | docs",
          "label": "kubernetes/kubernetes | Kubernetes 文档",
          "url": "source url",
          "status": "running | success | failed | timeout",
          "metrics": {
            "new_events": 0,
            "analyzed_events": 0,
            "failed_events": 1
          },
          "error": "string | null",
          "events": [
            {
              "event_id": "github-release:openclaw/openclaw:v2026.3.12",
              "title": "openclaw 2026.3.12",
              "version": "v2026.3.12",
              "url": "https://github.com/...",
              "published_at": "ISO8601 | null",
              "status": "new | analyzed | failed | skipped",
              "analysis": {
                "title_zh": "...",
                "summary_zh": "...",
                "urgency": "low | medium | high",
                "action_items": []
              },
              "error": "string | null"
            }
          ]
        }
      ]
    }
  ]
}
```

Notes:
- Store **only events touched in this run** (new/analyzed/failed). Do not copy the entire event corpus.
- Retain last **N=20** runs (configurable constant).

## API
- `GET /api/sync/runs?limit=20` -> list of run summaries (no events).
- `GET /api/sync/runs/<id>` -> full run detail with sources + events.
- `DELETE /api/sync/runs` -> clear log file (start from zero).
- Extend `GET /api/sync/status` to include `run_id` for the current/last run.

## UI/UX
Radar panel changes:
- Show only: Status pill, Phase, Current label, Source progress, Counters.
- Counters (`新增/已分析/失败`) are clickable.
- Add a `日志` entry in the header to open logs even when idle.

Log drawer:
- Default to **current run** using `run_id` from `/api/sync/status`.
- Two tabs: `本次同步` (current run) and `历史同步` (list of recent runs).
- Event list grouped by source with filters: `全部 / 新增 / 已分析 / 失败`.
- Each event shows `title/version`, `time`, `url`, `analysis summary` (if present) or `error`.

Empty states:
- If no runs exist, show “暂无同步日志”.
- If current run missing, fall back to latest run in history.

## Error Handling
- Record errors from fetch/analyze per event or per source.
- Timeouts recorded with `status=timeout` and error message.
- Packy/API failures captured on event errors to explain failed analysis spikes.

## Retention & Reset
- Keep last 20 runs. Older entries dropped on write.
- Support `DELETE /api/sync/runs` to clear logs.
- On rollout, perform a one-time clear to “start from zero”.

## Testing
Backend:
- Unit tests for log writer (run creation, append events, retention).
- API tests for list/detail/clear endpoints.
- Sync status includes `run_id`.

Frontend:
- Radar renders simplified layout.
- Clicking counters opens drawer and loads current run.
- History tab loads run list and details.

