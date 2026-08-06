#!/usr/bin/env bash

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$APP_DIR/.venv/bin/python"
URL="http://127.0.0.1:5085"

STATE_DIR="$HOME/.local/state/ga-social-studies-testing-program"
LOG_FILE="$STATE_DIR/app.log"
PID_FILE="$STATE_DIR/app.pid"

mkdir -p "$STATE_DIR"
mkdir -p "$HOME/KIDS-HW/grades"

show_error() {
    local message="$1"

    if command -v notify-send >/dev/null 2>&1; then
        notify-send \
            "Georgia Social Studies Testing Program" \
            "$message"
    else
        printf '%s\n' "$message" >&2
    fi
}

server_is_running() {
    curl \
        --silent \
        --fail \
        --max-time 2 \
        "$URL/health" \
        >/dev/null 2>&1
}

if [[ ! -x "$PYTHON" ]]; then
    show_error "Python environment is missing. Run ./install-desktop.sh"
    exit 1
fi

if ! server_is_running; then
    cd "$APP_DIR"

    nohup "$PYTHON" "$APP_DIR/app.py" \
        >>"$LOG_FILE" 2>&1 &

    SERVER_PID=$!
    printf '%s\n' "$SERVER_PID" > "$PID_FILE"

    for attempt in $(seq 1 40); do
        if server_is_running; then
            break
        fi

        if ! kill -0 "$SERVER_PID" 2>/dev/null; then
            show_error "The program stopped during startup. Check $LOG_FILE"
            exit 1
        fi

        sleep 0.25
    done
fi

if ! server_is_running; then
    show_error "Unable to start the server. Check $LOG_FILE"
    exit 1
fi

if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
    open "$URL"
else
    printf 'Open this address in your browser:\n%s\n' "$URL"
fi
