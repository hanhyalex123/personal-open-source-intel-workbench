# LLM Provider Toggles + Codex Compatibility Design

Date: 2026-03-16

## Goals
- Add per-provider enable/disable toggles for Packy and OpenAI.
- When disabled, a provider must not participate in primary or fallback selection.
- API should return empty config for disabled providers.
- Treat `protocol=codex` as OpenAI Responses wire format to match the current Codex config.

## Non-Goals
- Changing provider authentication models beyond the existing config fields.
- Reworking provider priority or fallback strategy beyond enabled/disabled gating.

## Approach (Recommended)
1. **Config & API**
   - Add `enabled: boolean` to the persisted config for `packy` and `openai`.
   - Default both to `true` for backward compatibility.
   - `/api/llm-config` returns these flags.
   - When `enabled=false`, the API returns empty settings for that provider.

2. **Backend Selection**
   - Provider selection skips any provider with `enabled=false`.
   - Fallback is ignored when disabled or missing; empty fallback returned.
   - `protocol=codex` is treated equivalently to `openai-responses`.

3. **Frontend Settings**
   - Add two toggles: “启用 Packy 通道” and “启用 OpenAI 通道”.
   - Persist `enabled` flags with existing save flow.
   - Disabled provider UI is hidden or shown as read-only with a short hint.

4. **Tests**
   - Config normalization preserves `enabled` flags.
   - Provider selection skips disabled providers.
   - Codex protocol uses OpenAI Responses wire format.

## UX Notes
- Default state: both providers enabled.
- If both are disabled, model calls return with empty provider configuration and a clear error message from selection logic.

## Risks
- Misconfigured toggles could result in no providers available; handled with a clear “no provider enabled” error.

## Success Criteria
- Users can disable Packy/OpenAI in Settings.
- Disabled providers never appear in selection or fallback.
- `protocol=codex` sends Responses wire format requests.
- Tests cover the new behavior.
