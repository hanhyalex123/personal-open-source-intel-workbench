#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_LABEL="${INTEL_E2E_RUN_LABEL:-$(date +%Y%m%d-%H%M%S)}"
RUN_DIR="$ROOT_DIR/.run/e2e-incus-${RUN_LABEL}"
DATA_DIR="$RUN_DIR/data"
API_DIR="$RUN_DIR/api"
ARTIFACT_DIR="$ROOT_DIR/output/playwright/incus-container-e2e-${RUN_LABEL}"
COMPOSE_OVERRIDE_PATH="$RUN_DIR/docker-compose.e2e.yml"
COMPOSE_PROJECT="${INTEL_E2E_COMPOSE_PROJECT:-intel-e2e-incus}"
BACKEND_PORT="${INTEL_E2E_BACKEND_PORT:-18080}"
FRONTEND_PORT="${INTEL_E2E_FRONTEND_PORT:-15173}"
BACKEND_URL=""
FRONTEND_URL=""
PROJECT_NAME="${INTEL_E2E_PROJECT_NAME:-Incus}"
PROJECT_GITHUB_URL="${INTEL_E2E_GITHUB_URL:-https://github.com/lxc/incus}"
PROJECT_DOCS_URL="${INTEL_E2E_DOCS_URL:-https://linuxcontainers.org/incus/docs/main/}"
PYTHON_BASE_IMAGE="${INTEL_E2E_PYTHON_BASE_IMAGE:-mirror.gcr.io/library/python:3.12-slim}"
NODE_BASE_IMAGE="${INTEL_E2E_NODE_BASE_IMAGE:-mirror.gcr.io/library/node:20-alpine}"
NGINX_BASE_IMAGE="${INTEL_E2E_NGINX_BASE_IMAGE:-mirror.gcr.io/library/nginx:1.27-alpine}"
CLEANUP=false

print_help() {
  cat <<EOF
Usage: bash scripts/e2e_incus_container.sh [--cleanup]

Builds the local frontend/backend containers, injects an Incus docs project,
runs a real sync against ${PROJECT_DOCS_URL}, and verifies the Docs UI with Playwright.

Environment:
  PACKY_API_KEY                     Optional when OPENAI_API_KEY is configured.
  PACKY_API_URL                     Defaults to https://code.swpumc.cn/v1/responses
  PACKY_MODEL                       Defaults to gpt-5.4
  PACKY_PROVIDER                    Defaults to OpenAI
  PACKY_PROTOCOL                    Defaults to openai-responses
  PACKY_REASONING_EFFORT            Optional. Leave empty unless the gateway supports it.
  PACKY_DISABLE_RESPONSE_STORAGE    Defaults to true
  OPENAI_API_KEY                    Optional OpenAI-compatible key. Used automatically when PACKY_API_KEY is absent.
  OPENAI_API_URL                    Optional OpenAI-compatible base URL.
  OPENAI_MODEL                      Optional OpenAI-compatible model.
  OPENAI_PROVIDER                   Optional OpenAI-compatible provider label.
  OPENAI_PROTOCOL                   Optional OpenAI-compatible protocol.
  GITHUB_TOKEN                      Optional GitHub token.
  INTEL_E2E_BACKEND_PORT            Defaults to 18080
  INTEL_E2E_FRONTEND_PORT           Defaults to 15173
  INTEL_E2E_COMPOSE_PROJECT         Defaults to intel-e2e-incus
  INTEL_E2E_PYTHON_BASE_IMAGE       Defaults to mirror.gcr.io/library/python:3.12-slim
  INTEL_E2E_NODE_BASE_IMAGE         Defaults to mirror.gcr.io/library/node:20-alpine
  INTEL_E2E_NGINX_BASE_IMAGE        Defaults to mirror.gcr.io/library/nginx:1.27-alpine

Options:
  --cleanup                         Stop containers and remove the E2E volume after the run.
  --help                            Show this message.
EOF
}

require_command() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "Missing required command: $name" >&2
    exit 1
  fi
}

port_is_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "( sport = :${port} )" | tail -n +2 | grep -q .
    return $?
  fi
  return 1
}

pick_available_port() {
  local requested_port="$1"
  local port="$requested_port"

  while port_is_in_use "$port"; do
    port="$((port + 1))"
  done

  printf '%s' "$port"
}

resolve_env_value() {
  local name="$1"
  local default_value="${2:-}"
  local dotenv_path="$ROOT_DIR/.env"

  if [[ -n "${!name:-}" ]]; then
    printf '%s' "${!name}"
    return 0
  fi

  if [[ -f "$dotenv_path" ]]; then
    local line
    line="$(grep -E "^${name}=" "$dotenv_path" | tail -n 1 || true)"
    if [[ -n "$line" ]]; then
      local value="${line#*=}"
      value="${value%\"}"
      value="${value#\"}"
      value="${value%\'}"
      value="${value#\'}"
      printf '%s' "$value"
      return 0
    fi
  fi

  printf '%s' "$default_value"
}

write_json_file() {
  local path="$1"
  local content="$2"
  printf '%s\n' "$content" >"$path"
}

prepare_workspace() {
  mkdir -p "$RUN_DIR" "$DATA_DIR" "$API_DIR" "$ARTIFACT_DIR"
  write_json_file "$DATA_DIR/config.json" '{}'
  write_json_file "$DATA_DIR/events.json" '{}'
  write_json_file "$DATA_DIR/analyses.json" '{}'
  write_json_file "$DATA_DIR/projects.json" '[]'
  write_json_file "$DATA_DIR/crawl_profiles.json" '{}'
  write_json_file "$DATA_DIR/daily_project_summaries.json" '{}'
  write_json_file "$DATA_DIR/docs_snapshots.json" '{}'
  write_json_file "$DATA_DIR/sync_runs.json" '{"runs":[]}'
  write_json_file "$DATA_DIR/state.json" '{}'
}

write_compose_override() {
  cat >"$COMPOSE_OVERRIDE_PATH" <<EOF
services:
  backend:
    build:
      args:
        PYTHON_BASE_IMAGE: ${PYTHON_BASE_IMAGE}
    ports:
      - "${BACKEND_PORT}:8000"
    volumes:
      - ${DATA_DIR}:/app/backend/data
  frontend:
    build:
      args:
        NODE_BASE_IMAGE: ${NODE_BASE_IMAGE}
        NGINX_BASE_IMAGE: ${NGINX_BASE_IMAGE}
    ports:
      - "${FRONTEND_PORT}:80"
EOF
}

compose() {
  docker compose \
    -p "$COMPOSE_PROJECT" \
    -f "$ROOT_DIR/docker-compose.yml" \
    -f "$COMPOSE_OVERRIDE_PATH" \
    "$@"
}

wait_for_url() {
  local url="$1"
  local label="$2"
  local retries="${3:-60}"

  for _ in $(seq 1 "$retries"); do
    if curl --noproxy '*' -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  echo "$label did not become ready: $url" >&2
  return 1
}

json_from_stdin() {
  local expression="$1"
  node -e '
    const fs = require("fs");
    const expression = process.argv[1];
    const input = fs.readFileSync(0, "utf8");
    const payload = JSON.parse(input);
    const value = Function("payload", `return (${expression});`)(payload);
    if (typeof value === "object") {
      process.stdout.write(JSON.stringify(value));
    } else if (value !== undefined && value !== null) {
      process.stdout.write(String(value));
    }
  ' "$expression"
}

request_json() {
  local method="$1"
  local url="$2"
  local body="${3:-}"
  local output_path="${4:-}"
  local response

  if [[ -n "$body" ]]; then
    response="$(curl --noproxy '*' -fsS -X "$method" "$url" -H 'content-type: application/json' -d "$body")"
  else
    response="$(curl --noproxy '*' -fsS -X "$method" "$url")"
  fi

  if [[ -n "$output_path" ]]; then
    printf '%s' "$response" >"$output_path"
  fi

  printf '%s' "$response"
}

poll_sync_until_complete() {
  local status_path="$API_DIR/sync-status.json"
  local max_attempts=180

  for attempt in $(seq 1 "$max_attempts"); do
    local payload
    payload="$(request_json GET "$BACKEND_URL/api/sync/status" "" "$status_path")"
    local status phase message
    status="$(printf '%s' "$payload" | json_from_stdin 'payload.status || ""')"
    phase="$(printf '%s' "$payload" | json_from_stdin 'payload.phase || ""')"
    message="$(printf '%s' "$payload" | json_from_stdin 'payload.message || ""')"
    printf '[sync %03d] status=%s phase=%s message=%s\n' "$attempt" "$status" "$phase" "$message"

    if [[ "$status" == "success" ]]; then
      return 0
    fi
    if [[ "$status" == "failed" ]]; then
      dump_failure_context
      return 1
    fi

    sleep 5
  done

  echo "Timed out waiting for sync completion." >&2
  dump_failure_context
  return 1
}

dump_failure_context() {
  echo "==== /api/sync/status ====" >&2
  curl --noproxy '*' -fsS "$BACKEND_URL/api/sync/status" >&2 || true
  echo >&2
  echo "==== docker compose logs: backend ====" >&2
  compose logs --no-color backend >&2 || true
  echo "==== docker compose logs: frontend ====" >&2
  compose logs --no-color frontend >&2 || true
}

assert_api_expectations() {
  local docs_projects_path="$API_DIR/docs-projects.json"
  local docs_detail_path="$API_DIR/docs-detail.json"
  local docs_events_path="$API_DIR/docs-events.json"
  local docs_pages_path="$API_DIR/docs-pages.json"

  request_json GET "$BACKEND_URL/api/docs/projects" "" "$docs_projects_path" >/dev/null

  local project_id
  project_id="$(
    node -e '
      const fs = require("fs");
      const items = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
      const found = items.find((item) => item.project_name === "Incus");
      if (!found) {
        process.exit(1);
      }
      process.stdout.write(found.project_id);
    ' "$docs_projects_path"
  )"

  request_json GET "$BACKEND_URL/api/docs/projects/$project_id" "" "$docs_detail_path" >/dev/null
  request_json GET "$BACKEND_URL/api/docs/projects/$project_id/events" "" "$docs_events_path" >/dev/null
  request_json GET "$BACKEND_URL/api/docs/projects/$project_id/pages" "" "$docs_pages_path" >/dev/null

  node -e '
    const fs = require("fs");
    const detail = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
    const events = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
    const pages = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));

    if (!detail.initial_read) {
      throw new Error("Missing initial_read in docs detail payload");
    }
    if (!(detail.page_count > 0)) {
      throw new Error("Expected page_count > 0");
    }
    if (!events.some((item) => item.event_kind === "docs_initial_read")) {
      throw new Error("Expected at least one docs_initial_read event");
    }
    if (!pages.some((item) => ["furo", "sphinx-html"].includes(item.extractor_hint))) {
      throw new Error("Expected at least one Furo/Sphinx page in docs pages");
    }
  ' "$docs_detail_path" "$docs_events_path" "$docs_pages_path"
}

run_browser_checks() {
  local max_attempts=3
  local attempt
  for attempt in $(seq 1 "$max_attempts"); do
    if node "$ROOT_DIR/scripts/e2e_incus_ui.mjs" "$FRONTEND_URL" "$ARTIFACT_DIR"; then
      return 0
    fi
    if [[ "$attempt" -lt "$max_attempts" ]]; then
      echo "Browser check attempt ${attempt} failed, retrying..." >&2
      sleep 5
    fi
  done
  return 1
}

cleanup_resources() {
  if [[ "$CLEANUP" == "true" ]]; then
    compose down -v --remove-orphans >/dev/null 2>&1 || true
  fi
}

trap cleanup_resources EXIT

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cleanup)
      CLEANUP=true
      ;;
    --help)
      print_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      print_help >&2
      exit 1
      ;;
  esac
  shift
done

require_command docker
require_command curl
require_command node
require_command npx

PACKY_API_KEY="$(resolve_env_value PACKY_API_KEY)"
PACKY_API_URL="$(resolve_env_value PACKY_API_URL "https://code.swpumc.cn/v1/responses")"
PACKY_MODEL="$(resolve_env_value PACKY_MODEL "gpt-5.4")"
PACKY_PROVIDER="$(resolve_env_value PACKY_PROVIDER "OpenAI")"
PACKY_PROTOCOL="$(resolve_env_value PACKY_PROTOCOL "openai-responses")"
PACKY_REASONING_EFFORT="$(resolve_env_value PACKY_REASONING_EFFORT)"
PACKY_DISABLE_RESPONSE_STORAGE="$(resolve_env_value PACKY_DISABLE_RESPONSE_STORAGE "true")"
OPENAI_API_KEY="$(resolve_env_value OPENAI_API_KEY)"
OPENAI_API_URL="$(resolve_env_value OPENAI_API_URL)"
OPENAI_MODEL="$(resolve_env_value OPENAI_MODEL "gpt-5.4")"
OPENAI_PROVIDER="$(resolve_env_value OPENAI_PROVIDER "OpenAI")"
OPENAI_PROTOCOL="$(resolve_env_value OPENAI_PROTOCOL)"
GITHUB_TOKEN="$(resolve_env_value GITHUB_TOKEN)"
INTEL_HIGRESS_REQUIRED="false"

if [[ "$PACKY_API_KEY" == "your_packy_api_key" ]]; then
  PACKY_API_KEY=""
fi
if [[ "$OPENAI_API_KEY" == "your_openai_api_key" ]]; then
  OPENAI_API_KEY=""
fi

if [[ -z "$PACKY_API_KEY" && -n "$OPENAI_API_KEY" ]]; then
  PACKY_API_KEY="$OPENAI_API_KEY"
  if [[ -n "$OPENAI_API_URL" ]]; then
    if [[ "$OPENAI_API_URL" == *"/v1/responses" || "$OPENAI_API_URL" == *"/v1/chat/completions" ]]; then
      PACKY_API_URL="$OPENAI_API_URL"
    else
      PACKY_API_URL="${OPENAI_API_URL%/}/v1/responses"
    fi
  fi
  PACKY_MODEL="$OPENAI_MODEL"
  PACKY_PROVIDER="$OPENAI_PROVIDER"
  if [[ -n "$OPENAI_PROTOCOL" ]]; then
    PACKY_PROTOCOL="$OPENAI_PROTOCOL"
  else
    PACKY_PROTOCOL="openai-responses"
  fi
fi

if [[ -z "$PACKY_API_KEY" && -z "$OPENAI_API_KEY" ]]; then
  echo "Either PACKY_API_KEY or OPENAI_API_KEY is required for the Incus E2E run, and placeholder values are not accepted." >&2
  exit 1
fi

export PACKY_API_KEY
export PACKY_API_URL
export PACKY_MODEL
export PACKY_PROVIDER
export PACKY_PROTOCOL
export PACKY_REASONING_EFFORT
export PACKY_DISABLE_RESPONSE_STORAGE
export OPENAI_API_KEY
export OPENAI_API_URL
export OPENAI_MODEL
export OPENAI_PROVIDER
export OPENAI_PROTOCOL
export GITHUB_TOKEN
export INTEL_HIGRESS_REQUIRED

resolved_backend_port="$(pick_available_port "$BACKEND_PORT")"
resolved_frontend_port="$(pick_available_port "$FRONTEND_PORT")"
if [[ "$resolved_backend_port" != "$BACKEND_PORT" ]]; then
  echo "Port ${BACKEND_PORT} is occupied, using ${resolved_backend_port} for backend."
fi
if [[ "$resolved_frontend_port" != "$FRONTEND_PORT" ]]; then
  echo "Port ${FRONTEND_PORT} is occupied, using ${resolved_frontend_port} for frontend."
fi
BACKEND_PORT="$resolved_backend_port"
FRONTEND_PORT="$resolved_frontend_port"
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}"
FRONTEND_URL="http://127.0.0.1:${FRONTEND_PORT}"

prepare_workspace
write_compose_override
compose config >/dev/null

echo "Building and starting containers..."
compose down --remove-orphans >/dev/null 2>&1 || true
compose up -d --build
wait_for_url "$BACKEND_URL/api/health" "backend"
wait_for_url "$FRONTEND_URL" "frontend"

echo "Creating Incus project..."
project_response="$(
  request_json \
    POST \
    "$BACKEND_URL/api/projects" \
    "{\"name\":\"${PROJECT_NAME}\",\"github_url\":\"${PROJECT_GITHUB_URL}\",\"docs_url\":\"${PROJECT_DOCS_URL}\"}" \
    "$API_DIR/project-create.json"
)"
project_id="$(printf '%s' "$project_response" | json_from_stdin 'payload.id || ""')"

if [[ -z "$project_id" ]]; then
  echo "Failed to resolve project id from create_project response." >&2
  exit 1
fi

request_json \
  PUT \
  "$BACKEND_URL/api/projects/$project_id" \
  '{"release_area_enabled":false,"docs_area_enabled":true}' \
  "$API_DIR/project-update.json" \
  >/dev/null

# Keep the real-site E2E bounded to a complete single-page smoke crawl.
request_json \
  PUT \
  "$BACKEND_URL/api/projects/$project_id/crawl-profile" \
  "{\"entry_urls\":[\"${PROJECT_DOCS_URL}\"],\"allowed_path_prefixes\":[\"/incus/docs/main\"],\"blocked_path_prefixes\":[\"/incus/docs/main/_static\",\"/incus/docs/main/_sources\",\"/incus/docs/main/genindex\",\"/incus/docs/main/search\",\"/incus/docs/main/search/\"],\"max_depth\":0,\"max_pages\":4,\"expand_mode\":\"auto\",\"doc_system\":\"furo\",\"initial_read_enabled\":true,\"diff_mode\":\"page\",\"category_hints\":[\"架构\",\"升级\",\"网络\",\"存储\"],\"discovery_prompt\":\"\",\"classification_prompt\":\"\"}" \
  "$API_DIR/crawl-profile.json" \
  >/dev/null

echo "Triggering sync..."
request_json POST "$BACKEND_URL/api/sync" "" "$API_DIR/sync-trigger.json" >/dev/null
poll_sync_until_complete

echo "Checking docs APIs..."
assert_api_expectations

echo "Running browser checks..."
run_browser_checks

echo "Incus container E2E completed successfully."
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "Artifacts: $ARTIFACT_DIR"
echo "API payloads: $API_DIR"
if [[ "$CLEANUP" != "true" ]]; then
  echo "Containers are still running under compose project: $COMPOSE_PROJECT"
fi
