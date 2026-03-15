# Config Effective Values + Log Detail View Design

Date: 2026-03-16

## Goals
- Show **effective** LLM config values (including env-derived values) in the UI.
- Mask API keys with front/back display (e.g., `sk-abcd****wxyz`).
- Add per-event **detail view** in sync logs for structured inspection.

## Non-Goals
- New log storage format or additional log persistence changes.
- Replacing existing config inputs with read-only effective values.

## Approach
### A. Effective Config Values
- Extend `/api/config` response with **effective** values and **source** metadata.
- For each provider (Packy/OpenAI), return:
  - `effective_api_url`, `effective_model`, `effective_protocol`, `effective_provider`
  - `api_key_masked` (front/back only)
  - `api_key_source`: `config` / `env` / `missing`
- UI keeps editable fields for saved config, and adds a small “生效值” row with source + masked key.
- Masking rule: show first 4 and last 4 chars; if shorter, show first 2 + `****` + last 2.

### B. Sync Log Detail View
- In `SyncLogDrawer`, add **“查看详情”** per event.
- Detail panel shows:
  - 标题 / 状态 / 版本 / 时间 / URL
  - 模型 / 提供商 / 是否 fallback
  - 错误信息
  - 结论摘要（summary/action_items）
  - `<details>` 折叠展示原始 JSON
- No new API needed; use existing run detail payload.

### C. Tests
- Backend: assert `/api/config` returns `api_key_masked` + `api_key_source`.
- Frontend: assert effective value and detail view render correctly.

## Success Criteria
- Users can see effective values even when saved fields are empty.
- API keys display masked with source info.
- Logs show per-event detail view with structured fields and JSON fallback.
