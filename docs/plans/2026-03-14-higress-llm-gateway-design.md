# Higress LLM Gateway Design

**Date:** 2026-03-14

## Goal

Add a local Higress AI gateway in front of `/Users/hanhaoyuan/zc/Personal/openclaw_data/project-dashboard` so the project service uses one localhost model endpoint with automatic fallback from Claude to GLM when the primary path fails.

## Verified Context

- The project backend currently sends Claude-style requests directly to `https://www.packyapi.com/v1/messages` in [backend/llm.py](/Users/hanhaoyuan/zc/Personal/openclaw_data/project-dashboard/backend/llm.py).
- The current request shape is Anthropic-compatible: `x-api-key`, `anthropic-version`, and `messages`.
- Live checks against Packy confirmed:
  - `sk-uzb...` works with `claude-sonnet-4-6`
  - `sk-uzb...` works with `claude-opus-4-6`
  - `sk-iEe...` works with `glm-5`
  - `sk-iEe...` does not work with Claude models and returns `model_not_found` in the `bailian` group
- The user wants one long-lived `main` branch only. No extra long-lived feature branches should remain after delivery.
- Higress deployment files should live outside the repo at `/Users/hanhaoyuan/zc/Personal/Higress`.

## Options Considered

### 1. Higress as local AI gateway

- Deploy Higress via Docker in `/Users/hanhaoyuan/zc/Personal/Higress`
- Route all project LLM traffic through localhost
- Use Claude Sonnet as primary and GLM as fallback
- Centralize retries, failover, and provider logging

**Pros**
- Clean separation between business code and provider routing
- Better future path for rate limits, observability, and policy
- Keeps provider secrets outside the project repo

**Cons**
- Adds a gateway layer to install and monitor

### 2. Application-level fallback in `backend/llm.py`

- Add second-key fallback logic directly in backend code

**Pros**
- Faster initial coding

**Cons**
- Provider logic leaks into app code
- Harder to observe and tune
- Worse long-term maintenance

### 3. Manual switch only

- Keep one provider active at a time and change env vars when needed

**Pros**
- Minimal change

**Cons**
- No automatic recovery
- Does not solve current availability problem

## Selected Design

Use Higress as a local AI gateway, deployed with Docker, with:

- Primary upstream: Packy + `sk-uzb...` + `claude-sonnet-4-6`
- Fallback upstream: Packy + `sk-iEe...` + `glm-5`
- One localhost gateway URL used by the project service

Claude Sonnet is the correct primary model because it matches the current backend protocol and has already been verified with the project's existing request shape. GLM becomes the reliability fallback for provider-side errors and timeouts.

## Architecture

### Runtime Topology

1. Frontend talks to the local backend as it does now.
2. Backend sends every LLM call to local Higress on `127.0.0.1`.
3. Higress forwards requests to Packy using the configured upstream key/model pair.
4. If the primary upstream fails, Higress retries on the fallback upstream.

### Request Path

- Project backend keeps emitting Anthropic-style `/v1/messages` requests.
- The project-level `PACKY_API_URL` changes from Packy remote URL to the local Higress gateway URL.
- The project-level `PACKY_API_KEY` becomes a local gateway credential or placeholder, depending on Higress routing needs.
- Real upstream keys stay in Higress-local configuration only.

## Deployment Layout

### External deployment directory

Use `/Users/hanhaoyuan/zc/Personal/Higress` for:

- Docker compose or equivalent deployment files
- Higress-local `.env`
- Gateway route and provider configuration
- Startup and shutdown helpers if needed

### Project repo changes

Limit repo changes to:

- Local gateway endpoint wiring in [backend/llm.py](/Users/hanhaoyuan/zc/Personal/openclaw_data/project-dashboard/backend/llm.py) and related configuration handling
- Startup script checks in [scripts/start_intel_workbench.sh](/Users/hanhaoyuan/zc/Personal/openclaw_data/project-dashboard/scripts/start_intel_workbench.sh)
- Better logging and failure classification for gateway/provider errors
- Frontend log presentation improvements if needed so fallback activity is visible

## Error Handling

### Gateway failover triggers

Higress should fail over from Claude to GLM on:

- HTTP `5xx`
- request timeout
- connection reset / connection refused
- HTTP `429`

### Application behavior

The backend should:

- distinguish gateway errors from source crawl errors
- emit clear log messages for primary failure, fallback success, and fallback failure
- avoid turning a temporary provider `503` into an opaque sync failure without context

## Logging And Observability

Keep three log surfaces:

- Project backend log: `logs/backend.log`
- Project frontend log: `logs/frontend.log`
- Higress container/service logs in `/Users/hanhaoyuan/zc/Personal/Higress`

The UI should continue to default to "本次同步" and expose enough detail so model errors and fallback outcomes are clickable and inspectable.

## Startup Model

Startup should be deterministic:

1. Start Higress or confirm it is healthy
2. Start backend and frontend
3. Only advertise localhost access URLs such as `http://127.0.0.1:5173`

The project startup script should no longer leave the user guessing whether the model gateway is running.

## Acceptance Criteria

The design is complete when all of the following are true:

1. `project-dashboard` uses one localhost model endpoint rather than direct Packy upstream access.
2. A forced failure on the Claude path still allows sync analysis to continue through `glm-5`.
3. Logs clearly show whether a failure happened in crawl, gateway, or provider execution.
4. Startup and health checks tell the user which layer is missing.
5. No provider secret is added to git-tracked project files.
