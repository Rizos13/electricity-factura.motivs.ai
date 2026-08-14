#!/usr/bin/env bash
# motivs-factura launcher
# usage: motivs-factura [start|stop|update|logs|status]

set -euo pipefail

INSTALL_DIR="${MOTIVS_FACTURA_HOME:-$HOME/.motivs/factura}"
PORT="${MOTIVS_FACTURA_PORT:-8765}"
LOG_FILE="$INSTALL_DIR/.run.log"
PID_FILE="$INSTALL_DIR/.run.pid"

cmd="${1:-start}"

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }

ensure_install() {
    [ -d "$INSTALL_DIR/.venv" ] || die "not installed at $INSTALL_DIR. Re-run install.sh."
    [ -f "$INSTALL_DIR/backend/app/main.py" ] || die "install corrupted, missing backend. Re-run install.sh."
}

case "$cmd" in
    start)
        ensure_install
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            say "already running (pid $(cat "$PID_FILE")). Opening browser."
            open "http://127.0.0.1:$PORT" 2>/dev/null || true
            exit 0
        fi
        cd "$INSTALL_DIR"
        source .venv/bin/activate
        nohup .venv/bin/uvicorn backend.app.main:app --port "$PORT" --host 127.0.0.1 \
            >"$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        say "starting on port $PORT..."
        for _ in 1 2 3 4 5 6 7 8 9 10; do
            sleep 0.5
            curl -s "http://127.0.0.1:$PORT/healthz" >/dev/null 2>&1 && break
        done
        open "http://127.0.0.1:$PORT" 2>/dev/null || say "open http://127.0.0.1:$PORT in your browser"
        say "logs: motivs-factura logs"
        say "stop: motivs-factura stop"
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            pid=$(cat "$PID_FILE")
            kill "$pid" 2>/dev/null && say "stopped (pid $pid)" || say "process already gone"
            rm -f "$PID_FILE"
        else
            pkill -f "uvicorn backend.app.main" 2>/dev/null && say "stopped (orphan process)" || say "not running"
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            say "running (pid $(cat "$PID_FILE")), http://127.0.0.1:$PORT"
        else
            say "not running"
        fi
        ;;
    logs)
        [ -f "$LOG_FILE" ] || die "no log file yet ($LOG_FILE)"
        tail -f "$LOG_FILE"
        ;;
    update)
        ensure_install
        cd "$INSTALL_DIR"
        say "fetching latest factura..."
        git pull --rebase --quiet
        source .venv/bin/activate
        if [ -n "${MOTIVS_SRE_WHEEL_URL:-}" ]; then
            # a wheel pulled from a url the caller chose needs the checksum the
            # caller expects, otherwise the refresh installs whatever answers
            [ -n "${MOTIVS_SRE_WHEEL_SHA256:-}" ] || \
                die "MOTIVS_SRE_WHEEL_URL is set without MOTIVS_SRE_WHEEL_SHA256, refusing to install an unverified wheel"
            say "refreshing motivs-sre wheel..."
            # pip parses the wheel filename for metadata, keep the original name
            tmp_dir=$(mktemp -d /tmp/motivs_sre_XXXXXX)
            tmp="$tmp_dir/$(basename "$MOTIVS_SRE_WHEEL_URL")"
            curl -fsSL "$MOTIVS_SRE_WHEEL_URL" -o "$tmp"
            actual=$(shasum -a 256 "$tmp" | awk '{print $1}')
            if [ "$actual" != "$MOTIVS_SRE_WHEEL_SHA256" ]; then
                rm -rf "$tmp_dir"
                die "wheel checksum mismatch, expected $MOTIVS_SRE_WHEEL_SHA256, got $actual"
            fi
            pip install --quiet --force-reinstall "$tmp"
            rm -rf "$tmp_dir"
        fi
        say "done"
        ;;
    *)
        say "usage: motivs-factura [start|stop|status|logs|update]"
        exit 1
        ;;
esac
