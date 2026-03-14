# Higress LLM Gateway Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Route all `project-dashboard` LLM traffic through a local Higress gateway with Claude Sonnet as primary and GLM as automatic fallback, while improving startup, logging, and failure visibility.

**Architecture:** Higress runs locally in `/Users/hanhaoyuan/zc/Personal/Higress` and exposes one localhost Anthropic-compatible `/v1/messages` endpoint. The backend stops talking directly to Packy and instead targets the gateway. Gateway and app logs are surfaced separately so crawl failures, gateway failures, and provider failures can be distinguished quickly.

**Tech Stack:** Docker, Higress, Bash, Python, Flask, requests, React, Vitest, pytest

---

### Task 1: Add backend tests for gateway-aware LLM configuration and error classification

**Files:**
- Modify: `backend/tests/test_llm_requests.py`
- Modify: `backend/llm.py`

**Step 1: Write the failing tests**

Add tests covering:

```python
def test_get_llm_settings_prefers_local_gateway(monkeypatch):
    monkeypatch.setenv("PACKY_API_URL", "http://127.0.0.1:8080/v1/messages")
    monkeypatch.setenv("PACKY_MODEL", "claude-sonnet-4-6")
    monkeypatch.setenv("PACKY_API_KEY", "gateway-key")

    from backend.llm import get_llm_settings

    settings = get_llm_settings()
    assert settings["api_url"] == "http://127.0.0.1:8080/v1/messages"
    assert settings["model"] == "claude-sonnet-4-6"


def test_analyze_event_raises_gateway_error_with_context(monkeypatch):
    from backend.llm import analyze_event

    class FakeResponse:
        status_code = 503
        text = "upstream unavailable"

        def raise_for_status(self):
            raise requests.exceptions.HTTPError("503 Server Error")

        def json(self):
            return {}
```

Assert the raised exception includes enough context to identify:

- gateway URL
- model name
- HTTP status code

**Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_llm_requests.py -q
```

Expected: new tests fail because the error messages are still too generic.

**Step 3: Write minimal implementation**

In `backend/llm.py`:

- keep `get_llm_settings()` as the single config source
- wrap `raise_for_status()` failures with a message that includes `api_url`, `model`, and `status_code`
- keep existing retry logic for read timeouts

Sketch:

```python
try:
    response.raise_for_status()
except requests.exceptions.HTTPError as exc:
    status_code = getattr(response, "status_code", "unknown")
    raise RuntimeError(
        f"LLM gateway request failed: url={settings['api_url']} model={settings['model']} status={status_code}"
    ) from exc
```

**Step 4: Run tests to verify pass**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_llm_requests.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/llm.py backend/tests/test_llm_requests.py
git commit -m "fix: improve llm gateway error context"
```

### Task 2: Create local Higress Docker deployment and provider config

**Files:**
- Create: `/Users/hanhaoyuan/zc/Personal/Higress/docker-compose.yml`
- Create: `/Users/hanhaoyuan/zc/Personal/Higress/.env`
- Create: `/Users/hanhaoyuan/zc/Personal/Higress/README.md`
- Create: `/Users/hanhaoyuan/zc/Personal/Higress/config/` files required by the chosen Higress Docker deployment

**Step 1: Write the deployment contract**

Document exact runtime values in `README.md`:

- gateway bind address: `127.0.0.1`
- gateway port: `8080` unless occupied
- primary upstream: Packy Claude using `claude-sonnet-4-6`
- fallback upstream: Packy GLM using `glm-5`
- health check command
- log inspection command

**Step 2: Validate Docker configuration before launch**

Run:

```bash
docker compose -f /Users/hanhaoyuan/zc/Personal/Higress/docker-compose.yml config
```

Expected: config renders successfully.

**Step 3: Write minimal deployment files**

Ensure:

- secrets come from `/Users/hanhaoyuan/zc/Personal/Higress/.env`
- project repo does not store real provider keys
- Higress can expose one localhost endpoint used by `project-dashboard`
- fallback policy covers `5xx`, `429`, timeout, and connection failure if supported directly; unsupported cases should be covered by the smallest possible compatible configuration

**Step 4: Launch and verify gateway health**

Run:

```bash
docker compose -f /Users/hanhaoyuan/zc/Personal/Higress/docker-compose.yml up -d
curl -sS http://127.0.0.1:8080/ | head
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Expected: Higress containers are healthy and the gateway port is bound locally.

**Step 5: Smoke-test both model routes**

Run gateway test requests that prove:

- Claude request succeeds with `claude-sonnet-4-6`
- Forced primary failure can fall back to `glm-5` or a dedicated backup route can be hit successfully

Record the exact commands in `README.md`.

**Step 6: Commit project-side references only**

Do not commit `/Users/hanhaoyuan/zc/Personal/Higress/.env`.

If any repo-tracked documentation is added for local setup:

```bash
git add docs/... scripts/... 
git commit -m "docs: document local higress gateway setup"
```

### Task 3: Wire project startup to require and report Higress health

**Files:**
- Modify: `scripts/start_intel_workbench.sh`
- Modify: `scripts/stop_intel_workbench.sh`
- Modify: `backend/server.py`

**Step 1: Write the failing behavior checks**

Add a shell-level verification checklist and encode the easiest pieces directly in script output expectations:

```bash
bash scripts/start_intel_workbench.sh
```

Expected before implementation:

- startup does not mention Higress
- output still mentions `0.0.0.0`
- failures do not identify whether the gateway is down

**Step 2: Implement minimal startup health checks**

Update `scripts/start_intel_workbench.sh` to:

- check Higress health endpoint before backend readiness
- print a clear message if Higress is unavailable
- keep advertised access URLs on `127.0.0.1`

Update `scripts/stop_intel_workbench.sh` to optionally stop or preserve Higress explicitly, but keep the behavior predictable and documented.

If backend startup performs an immediate sync, ensure gateway-related failure messages are explicit in `backend/server.py`.

**Step 3: Verify startup behavior**

Run:

```bash
bash scripts/stop_intel_workbench.sh
bash scripts/start_intel_workbench.sh
curl -sS http://127.0.0.1:8000/api/health
curl -sS http://127.0.0.1:5173 >/dev/null
```

Expected:

- startup output names Higress status
- frontend URL is `http://127.0.0.1:5173`
- backend health is OK

**Step 4: Commit**

```bash
git add scripts/start_intel_workbench.sh scripts/stop_intel_workbench.sh backend/server.py
git commit -m "fix: gate startup on higress health"
```

### Task 4: Surface gateway and fallback outcomes in sync logs and UI

**Files:**
- Modify: `backend/sync.py`
- Modify: `backend/sync_runs.py`
- Modify: `src/components/SyncLogDrawer.jsx`
- Modify: `src/components/SyncStatusPanel.jsx`
- Modify: `src/test/app.test.jsx`
- Modify: `src/test/sync-status-panel.test.jsx`
- Modify: `backend/tests/test_sync.py`

**Step 1: Write failing backend tests**

Add a sync test that injects a gateway/provider failure marker and expects event logs to retain structured error details:

```python
def test_run_sync_once_records_gateway_failure_context(tmp_path):
    ...
    assert event["error_kind"] == "llm_gateway"
    assert "fallback" in event["error"]
```

**Step 2: Write failing frontend tests**

Add UI assertions that a gateway failure is visible and clickable from:

- the failed count entry in `SyncStatusPanel`
- the event detail rows in `SyncLogDrawer`

**Step 3: Implement minimal logging shape**

Update backend logging to preserve fields such as:

- `error_kind`
- `provider`
- `model`
- `used_fallback`

Update frontend rendering to show those details without making the panel denser than it is now.

**Step 4: Run targeted tests**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_sync.py -q
npm test -- --runInBand src/test/app.test.jsx src/test/sync-status-panel.test.jsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/sync.py backend/sync_runs.py src/components/SyncLogDrawer.jsx src/components/SyncStatusPanel.jsx src/test/app.test.jsx src/test/sync-status-panel.test.jsx backend/tests/test_sync.py
git commit -m "feat: expose llm gateway failures in sync logs"
```

### Task 5: Run end-to-end verification, stabilize timeouts, and review on `main`

**Files:**
- Modify only if verification exposes real defects

**Step 1: Run full project verification**

Run:

```bash
npm test
.venv/bin/python -m pytest -q
```

Expected: all tests pass.

**Step 2: Run service smoke tests**

Run:

```bash
bash scripts/stop_intel_workbench.sh
bash scripts/start_intel_workbench.sh
curl -sS http://127.0.0.1:8000/api/health
curl -sS http://127.0.0.1:5173 >/dev/null
```

Then trigger one sync and inspect:

- `logs/backend.log`
- `logs/frontend.log`
- `docker logs <higress-container-name>`

Expected:

- no misleading `0.0.0.0` access message
- gateway is reachable
- sync can survive a temporary primary-model outage

**Step 3: Review the delivered system**

Use `superpowers:requesting-code-review` before declaring completion. Review should specifically cover:

- remaining timeout edges
- frontend click-through for logs and counts
- startup/shutdown predictability
- secret handling
- any stale references to direct Packy upstream URLs

**Step 4: Final commit if fixes were needed**

```bash
git add <exact files changed during verification>
git commit -m "fix: close remaining higress integration issues"
```

**Step 5: Keep branch policy clean**

Because the user wants one long-lived branch only, integrate all completed work back on `main` and remove any temporary worktrees or branches used during execution.
