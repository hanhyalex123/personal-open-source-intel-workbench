#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$ROOT_DIR/logs"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
BACKEND_URL="http://127.0.0.1:8000/api/health"
FRONTEND_URL="http://127.0.0.1:5173"

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
  kill -0 "$pid" 2>/dev/null
}

cleanup_stale_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]] && ! is_running "$pid_file"; then
    rm -f "$pid_file"
  fi
}

wait_for_url() {
  local url="$1"
  local label="$2"
  local retries=30

  for _ in $(seq 1 "$retries"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  echo "$label did not become ready: $url" >&2
  return 1
}

start_backend() {
  if is_running "$BACKEND_PID_FILE"; then
    echo "backend already running"
    return 0
  fi

  echo "starting backend..."
  (
    cd "$ROOT_DIR"
    nohup python3 -m backend.server >"$BACKEND_LOG" 2>&1 &
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
    nohup ./node_modules/.bin/vite --host 127.0.0.1 --port 5173 >"$FRONTEND_LOG" 2>&1 &
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

start_backend
start_frontend

wait_for_url "$BACKEND_URL" "backend"
wait_for_url "$FRONTEND_URL" "frontend"

open "$FRONTEND_URL"

echo "Intel Workbench is running."
echo "frontend: $FRONTEND_URL"
echo "backend:  http://127.0.0.1:8000"
echo "logs:     $LOG_DIR"
