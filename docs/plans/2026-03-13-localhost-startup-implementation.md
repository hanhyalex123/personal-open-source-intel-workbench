# Localhost Startup URLs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Keep services bound to `0.0.0.0` while ensuring all user-facing URLs (auto-open, health checks, printed output) use `127.0.0.1`.

**Architecture:** Update the startup shell script defaults and help text to point to localhost for access, while leaving the Vite host binding untouched (`--host 0.0.0.0`). Validate with a small file-content test.

**Tech Stack:** Bash, pytest (Python 3.12+)

---

### Task 1: Add a failing test for localhost URLs

**Files:**
- Create: `backend/tests/test_startup_script.py`
- Modify: `scripts/start_intel_workbench.sh`

**Step 1: Write the failing test**

Create `backend/tests/test_startup_script.py`:
```python
from pathlib import Path


def test_start_script_uses_localhost_urls():
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "start_intel_workbench.sh"
    script = script_path.read_text(encoding="utf-8")

    assert 'BACKEND_URL="${INTEL_BACKEND_URL:-http://127.0.0.1:8000/api/health}"' in script
    assert 'FRONTEND_URL="${INTEL_FRONTEND_URL:-http://127.0.0.1:5173}"' in script
```

**Step 2: Run test to verify it fails**

Run: `python3.12 -m pytest backend/tests/test_startup_script.py -q`

Expected: FAIL (script still uses `0.0.0.0` in URL defaults)

**Step 3: Write minimal implementation**

Update `scripts/start_intel_workbench.sh`:
- Change `BACKEND_URL` default to `http://127.0.0.1:8000/api/health`
- Change `FRONTEND_URL` default to `http://127.0.0.1:5173`
- Update help/echo lines to show `127.0.0.1` for access
- Keep `FRONTEND_CMD` host as `0.0.0.0`

**Step 4: Run test to verify it passes**

Run: `python3.12 -m pytest backend/tests/test_startup_script.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/tests/test_startup_script.py scripts/start_intel_workbench.sh
git commit -m "fix: use localhost URLs in startup script"
```

### Task 2: Start services and verify access

**Files:**
- Modify: none

**Step 1: Start services**

Run: `bash scripts/start_intel_workbench.sh`

**Step 2: Verify access**

Run:
- `curl -fsS http://127.0.0.1:8000/api/health`
- Open `http://127.0.0.1:5173`

Expected: health check returns JSON and frontend loads.
