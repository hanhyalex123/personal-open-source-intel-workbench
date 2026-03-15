# Merge Stash@{1} Page Updates Design

Date: 2026-03-16

## Goals
- Merge the **page-related UI changes** from `stash@{1}` into current `main` without regressing the already-merged provider toggles/codex changes.
- Keep the new/updated pages (Sync logs/history, Intel overview, Project monitor UI adjustments) and their required API endpoints.
- Avoid rolling back unrelated files (Docker, README, backend refactors, etc.).

## Non-Goals
- Reverting existing `main` functionality or deleting files.
- Importing unrelated backend refactors from `stash@{1}`.
- Overhauling docker/CI/README based on old stash content.

## Approach
1. **Selective transplant** from `stash@{1}`:
   - Frontend pages and layout: `src/App.jsx`, `src/components/IntelOverviewPage.jsx`, `src/components/ProjectMonitorPage.jsx`, `src/components/SyncStatusPanel.jsx`, `src/index.css`, `src/lib/api.js`, `src/test/app.test.jsx`.
   - Backend endpoints only if required by the UI: `backend/app.py` (sync runs endpoints), plus any minimal storage/runtime adjustments needed for the endpoints.
2. **Conflict resolution** in favor of current `main` for any overlapping logic not strictly part of the new pages.
3. **TDD**: add/adjust tests to cover new page behaviors; keep existing tests for current `main` intact.
4. **Verification**: run full test suite and build.

## Risk Mitigation
- Only apply a controlled subset of the stash to avoid mass rollbacks.
- Review each touched file for regressions and remove obsolete UI strings or stale API calls.
- Ensure API endpoints are additive, not destructive.

## Success Criteria
- New pages from the stash are visible and functional.
- No regressions in existing UI or backend behavior.
- Test suite and build pass.
