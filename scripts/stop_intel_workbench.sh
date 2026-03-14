#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"

print_help() {
  cat <<'EOF'
Usage: bash scripts/stop_intel_workbench.sh

Stops the frontend and backend started by start_intel_workbench.sh.
EOF
}

stop_pid_file() {
  local pid_file="$1"
  local label="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$label not running"
    return 0
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -z "$pid" ]]; then
    rm -f "$pid_file"
    echo "$label pid file was empty"
    return 0
  fi

  if kill -0 "$pid" 2>/dev/null; then
    echo "stopping $label..."
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 10); do
      if ! kill -0 "$pid" 2>/dev/null; then
        break
      fi
      sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  else
    echo "$label already stopped"
  fi

  rm -f "$pid_file"
}

if [[ "${1:-}" == "--help" ]]; then
  print_help
  exit 0
fi

stop_pid_file "$FRONTEND_PID_FILE" "frontend"
stop_pid_file "$BACKEND_PID_FILE" "backend"

echo "架构师开源情报站 stopped."
