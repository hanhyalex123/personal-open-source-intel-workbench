# LLM Analysis Dashboard Design

**Date:** 2026-03-09

**Context**

The current app is a frontend-only GitHub activity dashboard. It shows raw commits, releases, issues, and docs feeds in English. The new goal is different: the primary output should be stable Chinese operations insights, not raw source data. Historical conclusions must be retained, and only newly discovered upstream events should trigger fresh analysis.

**Chosen Direction**

Rebuild the app around a lightweight Python backend with local JSON persistence.

- Keep the API key out of the frontend.
- Persist analyzed results locally so the page opens with ready-made Chinese summaries.
- Run background sync on a schedule so new items are discovered without waiting for a manual page refresh.
- Preserve prior analysis for version-level facts that have become fixed conclusions.

**Architecture**

The system will have two runtime parts:

1. A Python backend that:
- pulls GitHub releases and selected documentation feeds
- normalizes upstream items into a shared event format
- detects whether an event is already known
- sends only new or changed events to the LLM
- stores raw source data and structured Chinese analysis in JSON files
- exposes simple HTTP endpoints for the frontend
- runs a background scheduler for periodic sync

2. A React frontend that:
- loads precomputed Chinese analysis from the backend
- highlights important operational changes in a clear Chinese UI
- distinguishes fixed conclusions from newly discovered updates
- still allows access to source links and original upstream titles when needed

**Data Model**

JSON persistence will be split into a small set of files:

- `data/config.json`
  - watched repositories
  - watched docs feeds
  - sync interval
- `data/events.json`
  - normalized upstream events keyed by stable event id
  - raw title, link, source, version, timestamps, hashes
- `data/analyses.json`
  - Chinese analysis records keyed by event id
  - summary, detailed explanation, impact, suggested action, fixed-conclusion flag, status, analyzed_at
- `data/state.json`
  - last sync time
  - last successful analysis time
  - scheduler status
  - per-source cursors or fingerprints

This keeps the storage inspectable and easy to back up while avoiding database setup in version one.

**Event and Analysis Rules**

Events will be normalized primarily around releases and important documentation updates. Commits and issues will be secondary inputs unless they are clearly release-worthy or documentation-impacting.

Each analyzed record should include:

- Chinese title
- one-line summary
- detailed explanation
- affected scope
- operational recommendation
- urgency level
- tags
- whether the conclusion is stable after release
- original source metadata

For versioned facts, once a release-level conclusion is marked stable, it remains in history and is not reanalyzed unless the upstream source materially changes.

**LLM Workflow**

The backend will call the configured Claude-compatible endpoint for new items only.

Prompt objectives:

- translate and explain in Chinese
- focus on operational or platform impact
- avoid generic summaries
- extract concrete recommendations
- mark whether the item is a stable conclusion or a provisional signal
- output structured JSON so the backend can store and render it cleanly

The model will never be asked to reanalyze already finalized historical items unless the normalized source hash changes.

**Sync Workflow**

1. Scheduler starts with the backend.
2. It fetches configured upstream sources.
3. Raw items are normalized into events.
4. The backend compares event ids and content hashes against local JSON state.
5. Only unseen or changed events enter the analysis queue.
6. Analysis results are stored.
7. The dashboard API serves combined event and analysis views.

Manual refresh will remain available, but the core path is scheduled sync.

**Frontend UX**

The UI should stop looking like a generic repo monitor. The new home page should be an insight dashboard:

- Hero area with last sync status and monitored scope
- "Important Changes" feed in Chinese
- grouped sections such as Kubernetes, Docker, Cilium, and custom repos
- cards that show summary first and detailed Chinese explanation on expand
- badges for urgency, category, and stable/fixed conclusion
- source link and upstream original title as secondary metadata

The visual direction should be cleaner and more editorial than the current three-column raw cards. Chinese readability matters more than dense telemetry.

**Out of Scope for Version One**

- user accounts
- multi-user persistence
- database migration framework
- distributed workers
- automatic browser push notifications
- heavy issue/commit semantic clustering beyond simple heuristics

**Testing Strategy**

- backend normalization tests
- backend persistence and dedupe tests
- backend prompt output parsing tests
- backend API tests
- frontend rendering tests for Chinese analysis cards
- integration check for scheduled sync updating stored files

**Delivery Shape**

Version one will replace most of the current UI, keep the frontend stack, and add a lightweight Python service plus local JSON storage. The end state should already feel usable: open page, see Chinese conclusions immediately, and wait only for genuinely new upstream changes.
