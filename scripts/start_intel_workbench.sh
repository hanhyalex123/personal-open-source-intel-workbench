#!/bin/bash

set -euo pipefail

ROOT_DIR="${INTEL_WORKBENCH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$ROOT_DIR/logs"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
BACKEND_URL="${INTEL_BACKEND_URL:-http://127.0.0.1:8000/api/health}"
FRONTEND_URL="${INTEL_FRONTEND_URL:-http://127.0.0.1:5173}"
FRONTEND_CMD="${INTEL_FRONTEND_CMD:-./node_modules/.bin/vite --host 0.0.0.0 --port 5173}"
OPEN_BROWSER_CMD="${INTEL_OPEN_CMD:-open}"
HIGRESS_HEALTH_URL="${INTEL_HIGRESS_HEALTH_URL:-http://127.0.0.1:8001/}"
HIGRESS_CONTAINER="${INTEL_HIGRESS_CONTAINER:-project-dashboard-higress}"
HIGRESS_REQUIRED="${INTEL_HIGRESS_REQUIRED:-false}"

detect_backend_python() {
  if [[ -n "${INTEL_BACKEND_PYTHON:-}" ]]; then
    echo "$INTEL_BACKEND_PYTHON"
    return 0
  fi

  for candidate in python3.12 /opt/homebrew/anaconda3/bin/python3 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done

  echo "python3"
}

BACKEND_PYTHON="$(detect_backend_python)"
BACKEND_CMD="${INTEL_BACKEND_CMD:-$BACKEND_PYTHON -m backend.server}"

print_help() {
  cat <<'EOF'
Usage: bash scripts/start_intel_workbench.sh

Starts:
- Flask backend on http://127.0.0.1:8000
- Vite frontend on http://127.0.0.1:5173

Writes:
- PID files under .run/
- logs under logs/
EOF
}

is_running() {
  local pid_file="$1"
  if [[ ! -f "$pid_file" ]]; then
    return 1
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1

  local state
  state="$(ps -p "$pid" -o state= 2>/dev/null | tr -d '[:space:]')"
  [[ -n "$state" ]] || return 1
  [[ "$state" != Z* ]]
}

cleanup_stale_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]] && ! is_running "$pid_file"; then
    rm -f "$pid_file"
  fi
}

wait_for_process_url() {
  local pid_file="$1"
  local url="$2"
  local label="$3"
  local retries=30
  local stable_delay=1

  for _ in $(seq 1 "$retries"); do
    if ! is_running "$pid_file"; then
      echo "$label process exited before readiness" >&2
      return 1
    fi
    if curl --noproxy '*' -fsS "$url" >/dev/null 2>&1; then
      sleep "$stable_delay"
      if ! is_running "$pid_file"; then
        echo "$label process exited after readiness probe" >&2
        return 1
      fi
      return 0
    fi
    sleep 1
  done

  echo "$label did not become ready: $url" >&2
  return 1
}

check_higress() {
  if curl --noproxy '*' -fsS "$HIGRESS_HEALTH_URL" >/dev/null 2>&1; then
    return 0
  fi

  if [[ "$HIGRESS_REQUIRED" == "true" ]]; then
    echo "Higress is not responding at $HIGRESS_HEALTH_URL" >&2
    echo "Start it with: docker start $HIGRESS_CONTAINER" >&2
    exit 1
  fi

  echo "Warning: Higress not available at $HIGRESS_HEALTH_URL; starting local frontend/backend without it." >&2
}

start_backend() {
  if is_running "$BACKEND_PID_FILE"; then
    echo "backend already running"
    return 0
  fi

  echo "starting backend..."
  (
    cd "$ROOT_DIR"
    nohup bash -lc "$BACKEND_CMD" >"$BACKEND_LOG" 2>&1 &
    echo $! >"$BACKEND_PID_FILE"
  )
}

start_frontend() {
  if is_running "$FRONTEND_PID_FILE"; then
    echo "frontend already running"
    return 0
  fi

  echo "starting frontend..."
  (
    cd "$ROOT_DIR"
    nohup bash -lc "$FRONTEND_CMD" >"$FRONTEND_LOG" 2>&1 &
    echo $! >"$FRONTEND_PID_FILE"
  )
}

if [[ "${1:-}" == "--help" ]]; then
  print_help
  exit 0
fi

mkdir -p "$RUN_DIR" "$LOG_DIR"
cleanup_stale_pid "$BACKEND_PID_FILE"
cleanup_stale_pid "$FRONTEND_PID_FILE"

check_higress

start_backend
start_frontend

wait_for_process_url "$BACKEND_PID_FILE" "$BACKEND_URL" "backend"
wait_for_process_url "$FRONTEND_PID_FILE" "$FRONTEND_URL" "frontend"

"$OPEN_BROWSER_CMD" "$FRONTEND_URL"

echo "架构师开源情报站 is running."
echo "frontend: $FRONTEND_URL"
echo "backend:  http://127.0.0.1:8000"
echo "logs:     $LOG_DIR"
