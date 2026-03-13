# LLM JSON Repair Design

**Goal:** Improve robustness of local JSON parsing for LLM responses so malformed outputs (e.g., unterminated strings, trailing commas, mixed prose) no longer cause frequent analysis failures, without adding extra model calls.

## Context
- Parsing occurs in `backend/llm.py` (`parse_analysis_response`, `parse_assistant_response`, `parse_project_daily_summary_response`).
- Current fallback only repairs unescaped quotes, which is insufficient for common malformed patterns.
- Failures are recorded in sync logs as JSON decode errors (e.g., “Unterminated string…”).

## Non-Goals
- No additional model calls or retries.
- No changes to prompts or model parameters.
- No changes to sync scheduling or data storage schema.

## Proposed Approach
Implement a **layered local repair pipeline** before `json.loads`:

1. **Extract probable JSON block**
   - Strip ```json / ``` fences.
   - If extra prose exists, slice from first `{` to last `}` (or `[` to `]`).

2. **Sanitize unsafe characters**
   - Replace control characters (ASCII < 0x20) with spaces, except `\n` and `\t`.

3. **Fix trailing commas**
   - Replace `,}` → `}` and `,]` → `]`.

4. **Repair unescaped quotes**
   - Keep `_repair_unescaped_quotes` (existing behavior).

5. **Minimal structural completion (only on decode failure)**
   - If JSON decode fails with “Unterminated string” or “Expecting value”, attempt:
     - Close a dangling quote at end of string.
     - Balance `{}` and `[]` by appending missing closers.

6. **Final parse attempt**
   - If still failing, return the original error and preserve a short raw snippet for observability.

## Error Handling & Observability
- Maintain failure status when parsing still fails.
- Include `raw_excerpt` (bounded length) in error logs to help diagnosis.

## Testing Strategy
- Add unit tests for each repair step with representative malformed JSON samples.
- Add regression tests for `parse_*` functions to ensure they parse:
  - fenced JSON
  - prose + JSON
  - trailing commas
  - unterminated string
- Confirm no changes to well-formed JSON parsing.

## Rollout
- Implement behind pure local parsing; no runtime toggles required.
- Re-run pytest and spot-check a failing repo (e.g., ktransformers) for error reduction.
