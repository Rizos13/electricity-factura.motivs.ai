#!/usr/bin/env bash
# Motivs Electricity Factura — local Mac installer
# usage:
#   curl -fsSL https://raw.githubusercontent.com/Rizos13/electricity-factura.motivs.ai/main/install.sh | bash
# or local:
#   bash install.sh

set -euo pipefail

FACTURA_REPO="${MOTIVS_FACTURA_REPO:-https://github.com/Rizos13/electricity-factura.motivs.ai.git}"
WHEEL_URL="${MOTIVS_SRE_WHEEL_URL:-https://github.com/Rizos13/sre-dist/releases/latest/download/motivs_sre-0.5.0-py3-none-any.whl}"
INSTALL_DIR="${MOTIVS_FACTURA_HOME:-$HOME/.motivs/factura}"
BIN_DIR="${MOTIVS_BIN:-$HOME/.local/bin}"
LAUNCHER="motivs-factura"

die() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }
say() { printf '\033[36m%s\033[0m\n' "$*"; }
warn() { printf '\033[33mwarning:\033[0m %s\n' "$*"; }
ok()  { printf '\033[32m✓\033[0m %s\n' "$*"; }

require_macos() {
    [ "$(uname)" = "Darwin" ] || die "this installer targets macOS only. Linux/Windows not yet supported."
}

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "$1 not found. $2"
}

require_python() {
    local py
    py=$(command -v python3 || true)
    [ -n "$py" ] || die "python3 not found. Install Python 3.11+ from python.org or 'brew install python@3.11'."
    local ver
    ver=$("$py" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
    case "$ver" in
        3.13) ok "python $ver detected" ;;
        *) die "python 3.13 required (found $ver). Install with: brew install python@3.13" ;;
    esac
}

clone_or_update() {
    if [ -d "$INSTALL_DIR/.git" ]; then
        say "existing install detected, updating..."
        git -C "$INSTALL_DIR" fetch --depth 1 origin main
        git -C "$INSTALL_DIR" reset --hard origin/main
    else
        say "cloning electricity-factura..."
        mkdir -p "$(dirname "$INSTALL_DIR")"
        git clone --depth 1 "$FACTURA_REPO" "$INSTALL_DIR"
    fi
}

setup_venv() {
    if [ ! -d "$INSTALL_DIR/.venv" ]; then
        say "creating virtual environment..."
        python3 -m venv "$INSTALL_DIR/.venv"
    fi
    "$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
}

install_sre_wheel() {
    say "downloading motivs-sre security gate..."
    local tmp_dir tmp_wheel
    tmp_dir=$(mktemp -d /tmp/motivs_sre_XXXXXX)
    tmp_wheel="$tmp_dir/motivs_sre-0.5.0-py3-none-any.whl"
    if ! curl -fsSL "$WHEEL_URL" -o "$tmp_wheel"; then
        rm -rf "$tmp_dir"
        die "failed to download motivs-sre wheel from $WHEEL_URL. Check your network or contact support."
    fi
    "$INSTALL_DIR/.venv/bin/pip" install --quiet --force-reinstall "$tmp_wheel"
    rm -rf "$tmp_dir"
    ok "motivs-sre installed"
}

install_factura_deps() {
    say "installing factura dependencies..."
    "$INSTALL_DIR/.venv/bin/pip" install --quiet \
        "fastapi>=0.115.0" "uvicorn[standard]>=0.30.0" "python-multipart>=0.0.9" \
        "pydantic-settings>=2.4.0" "orjson>=3.10.0" "pyyaml>=6.0" \
        "lancedb>=0.15.0" "pyarrow>=15.0.0" "pandas>=2.2.0" "numpy>=1.26.0" \
        "redis>=5.0.0" "httpx>=0.27.0" \
        "pdfplumber>=0.11.0" "pymupdf>=1.24.0" "pytesseract>=0.3.10" "pillow>=10.4.0"
    "$INSTALL_DIR/.venv/bin/pip" install --quiet --no-deps -e "$INSTALL_DIR"
    ok "factura installed"
}

write_env() {
    local env_file="$INSTALL_DIR/.env"
    if [ -f "$env_file" ] && grep -q "^MOTIVS_HMAC_KEY=[^d]" "$env_file" 2>/dev/null; then
        return
    fi
    say "generating per-install HMAC key..."
    cp -n "$INSTALL_DIR/.env.example" "$env_file" 2>/dev/null || true
    local hmac
    hmac=$(openssl rand -hex 32)
    if grep -q "^MOTIVS_HMAC_KEY=" "$env_file"; then
        sed -i.bak "s|^MOTIVS_HMAC_KEY=.*|MOTIVS_HMAC_KEY=$hmac|" "$env_file"
    else
        printf '\nMOTIVS_HMAC_KEY=%s\n' "$hmac" >> "$env_file"
    fi
    rm -f "$env_file.bak"
    chmod 600 "$env_file"
    ok "HMAC key generated (stored in $env_file)"
}

install_launcher() {
    mkdir -p "$BIN_DIR"
    local launcher_path="$BIN_DIR/$LAUNCHER"
    cat > "$launcher_path" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_DIR/scripts/launcher.sh" "\$@"
EOF
    chmod +x "$launcher_path"
    ok "command installed: $launcher_path"
}

check_tesseract() {
    if ! command -v tesseract >/dev/null 2>&1; then
        warn "tesseract not installed — OCR for image bills (.jpg/.png) will not work."
        warn "  PDF bills work without it. To enable OCR:"
        warn "  brew install tesseract tesseract-lang"
    fi
}

check_path() {
    case ":$PATH:" in
        *":$BIN_DIR:"*) return ;;
    esac
    warn "$BIN_DIR is not in your PATH."
    warn "  add to your shell rc file (~/.zshrc or ~/.bashrc):"
    warn "  export PATH=\"$BIN_DIR:\$PATH\""
}

main() {
    require_macos
    require_cmd git "Install with: xcode-select --install"
    require_cmd curl "Should be preinstalled on macOS."
    require_cmd openssl "Should be preinstalled on macOS."
    require_python
    clone_or_update
    setup_venv
    install_sre_wheel
    install_factura_deps
    write_env
    install_launcher
    check_tesseract
    check_path
    printf '\n'
    ok "done. Start the service:"
    printf '\n    \033[1m%s\033[0m\n\n' "$LAUNCHER"
    say "the service runs locally on your Mac. Your bills never leave your device."
}

main "$@"
