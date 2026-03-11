## Summary

Add repository-seeded project configuration files that only initialize local data on first run. If local `backend/data/*.json` already exists, seeds are ignored to avoid impacting existing setups.

## Decision

Use **seed JSON files** checked into the repo:
- `backend/seed/projects.json`
- `backend/seed/crawl_profiles.json`

Initialization rule:
- Only copy from seeds when local `backend/data/projects.json` or `backend/data/crawl_profiles.json` is missing.
- Never overwrite existing local data.

## Scope

In scope:
- Add seed JSON files with the default project list (including docs-only CUDA/CANN/MindSpore)
- Update JsonStore to use seeds when data files are missing
- Add tests covering seed initialization logic

Out of scope:
- Runtime merging or overwriting of local config
- Any changes to the current project configuration UI
