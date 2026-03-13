# LLM JSON Repair Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a layered local JSON repair pipeline so malformed LLM outputs parse successfully without extra model calls, reducing analysis failures.

**Architecture:** Introduce a small set of helper functions in `backend/llm.py` to normalize/repair raw text (strip fences, extract JSON slice, sanitize control chars, remove trailing commas, repair quotes, balance brackets) and use a single `parse_json_with_repair` path in all parse functions. Failures should return clear errors with a bounded raw excerpt for observability.

**Tech Stack:** Python 3.12, pytest.

---

### Task 1: Add Regression Tests For Malformed JSON Responses

**Files:**
- Create: `backend/tests/test_llm_parsing.py`

**Step 1: Write failing tests for analysis parsing**
```python
from backend.llm import parse_analysis_response

def test_parse_analysis_response_repairs_trailing_commas_and_prose():
    payload = {
        "content": [
            {"type": "text", "text": "Here is the result:\n```json\n{\n  \"title_zh\": \"t\",\n  \"summary_zh\": \"s\",\n  \"impact_scope\": \"scope\",\n  \"suggested_action\": \"act\",\n  \"urgency\": \"low\",\n  \"tags\": [\"k\"],\n  \"is_stable\": true,\n}\n```"}
        ]
    }
    parsed = parse_analysis_response(payload)
    assert parsed["title_zh"] == "t"
```

**Step 2: Run the test to confirm it fails**
Run: `python -m pytest backend/tests/test_llm_parsing.py::test_parse_analysis_response_repairs_trailing_commas_and_prose -v`
Expected: FAIL with `json.decoder.JSONDecodeError`.

**Step 3: Add failing tests for unterminated string repair**
```python
from backend.llm import parse_analysis_response

def test_parse_analysis_response_repairs_unterminated_string():
    payload = {
        "content": [
            {"type": "text", "text": "{\n  \"title_zh\": \"t\",\n  \"summary_zh\": \"s\",\n  \"impact_scope\": \"scope\",\n  \"suggested_action\": \"act\",\n  \"urgency\": \"low\",\n  \"tags\": [\"k\"],\n  \"is_stable\": true,\n  \"details_zh\": \"missing end\n"}
        ]
    }
    parsed = parse_analysis_response(payload)
    assert parsed["summary_zh"] == "s"
```

**Step 4: Run all new tests to confirm failures**
Run: `python -m pytest backend/tests/test_llm_parsing.py -v`
Expected: FAIL with JSON parse errors.

**Step 5: Commit tests**
```bash
git add backend/tests/test_llm_parsing.py
git commit -m "test: add llm malformed json regression cases"
```

---

### Task 2: Implement JSON Repair Pipeline In `backend/llm.py`

**Files:**
- Modify: `backend/llm.py`

**Step 1: Add repair helpers**
```python
def _extract_json_block(text: str) -> str:
    # strip ```json / ``` fences and slice to first {..} or [..]
    ...

def _sanitize_control_chars(text: str) -> str:
    ...

def _remove_trailing_commas(text: str) -> str:
    ...

def _balance_brackets(text: str) -> str:
    ...

def _prepare_json_text(text: str) -> str:
    text = _extract_json_block(text)
    text = _sanitize_control_chars(text)
    text = _remove_trailing_commas(text)
    text = _repair_unescaped_quotes(text)
    return text
```

**Step 2: Create a single parse helper**
```python
def _parse_json_with_repair(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = _prepare_json_text(text)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            repaired = _balance_brackets(repaired)
            return json.loads(repaired)
```

**Step 3: Use the new helper in all parse functions**
- `parse_analysis_response`
- `parse_assistant_response`
- `parse_project_daily_summary_response`

**Step 4: Add bounded raw excerpt to raised errors**
- If still failing, raise `ValueError` including a short `raw_excerpt` (e.g. 400 chars) to aid log diagnosis.

**Step 5: Run tests**
Run: `python -m pytest backend/tests/test_llm_parsing.py -v`
Expected: PASS.

**Step 6: Commit**
```bash
git add backend/llm.py
git commit -m "fix: repair malformed llm json locally"
```

---

### Task 3: Verify Full Suite

**Step 1: Run backend tests**
Run: `python -m pytest -q`
Expected: PASS (0 failures).

**Step 2: Commit (if any follow-up fixes were required)**
```bash
git add -A
git commit -m "chore: stabilize llm json repair"
```

---

## Completion Criteria
- Malformed JSON outputs in tests parse successfully without extra model calls.
- Full `pytest` passes with no JSON decode failures.
- Analysis failures show bounded raw excerpts when parse still cannot be recovered.
