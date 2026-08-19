#!/usr/bin/env bash
# Bootstrap for Ubuntu and Debian (apt-based) -- native, or Debian/Ubuntu
# proot-distro running inside Termux on Android. Mirrors bootstrap_termux.sh
# step-for-step; the two are separate scripts because the package manager,
# prefix paths, and default toolchain availability genuinely differ. Ubuntu
# and Debian share one script here because both are apt/dpkg with identical
# package names for everything this needs -- a second near-duplicate file
# would just be copy-paste to maintain twice.
#
# Architecture: works on x86_64 and arm64, where PyPI ships a prebuilt
# `cryptography` wheel, and on 32-bit armhf/i386 (e.g. older Android
# devices under proot-distro), where it doesn't -- rustc+cargo are
# installed unconditionally so pip's source-build fallback always has
# what it needs, matching the Termux script's approach.
set -euo pipefail

REPO_URL="https://github.com/tewartech-node/claude-command-cli.git"
REPO_DIR="$HOME/claude-command-cli"
BRANCH="claude/termux-cli-cloudflare-nemotron-pve6ca"
RUNTIME="$HOME/.warnetech"

echo "[0] Checking distro..."
if [ -r /etc/os-release ]; then
    . /etc/os-release
    case "${ID:-}:${ID_LIKE:-}" in
        ubuntu*|debian*|*debian*) ;;
        *)
            echo "    WARNING: ${PRETTY_NAME:-this distro} is not Debian/Ubuntu-based."
            echo "    This script targets apt/dpkg systems; it may still work, but is untested elsewhere."
            ;;
    esac
else
    echo "    WARNING: /etc/os-release not found; proceeding, but this script assumes apt/dpkg."
fi

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    else
        echo "    ERROR: not running as root and no sudo available." >&2
        exit 1
    fi
fi

echo "[1] Updating apt packages..."
$SUDO apt-get update -y
$SUDO apt-get upgrade -y

echo "[2] Installing core dependencies..."
# build-essential + libssl-dev + rustc/cargo cover pip's source-build
# fallback for `cryptography` on architectures with no prebuilt wheel.
$SUDO apt-get install -y \
    python3 python3-venv python3-pip python3-dev \
    nodejs npm \
    git openssl libssl-dev pkg-config \
    build-essential rustc cargo

echo "[3] Creating Warnetech operator directories..."
mkdir -p "$RUNTIME/logs" "$RUNTIME/backups" "$RUNTIME/tmp"

STATE="$RUNTIME/state.json"
if [ ! -f "$STATE" ]; then
    echo '{"last_backup": null, "last_recall": null, "operator_events": []}' > "$STATE"
fi

echo "[4] Cloning Warnetech repo if missing..."
if [ ! -d "$REPO_DIR" ]; then
    git clone "$REPO_URL" "$REPO_DIR"
fi
cd "$REPO_DIR"
git fetch origin "$BRANCH"
git checkout "$BRANCH"

echo "[5] Installing Python dependencies..."
python3 -m pip install --upgrade pip --break-system-packages 2>/dev/null \
    || python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]" --break-system-packages 2>/dev/null \
    || python3 -m pip install -e ".[dev]"

echo "[6] Installing Node dependencies..."
npm install --silent

echo "[7] Running Python + JS tests..."
PY_OK=1; JS_OK=1
python3 -m pytest -q || PY_OK=0
npm test || JS_OK=0

echo "[8] Verifying the encryption path..."
python3 - <<'PYCHECK' || echo "    WARNING: envelope unavailable -- check the cryptography install"
from warnetech_envelope import decrypt_data, encrypt_data
assert decrypt_data(encrypt_data("bootstrap", "k"), "k") == "bootstrap"
print("    envelope round-trip OK")
PYCHECK

echo "[9] Bootstrap complete."
[ "$PY_OK" = 1 ] || echo "    Python tests FAILED"
[ "$JS_OK" = 1 ] || echo "    JS tests FAILED"
[ "$PY_OK" = 1 ] && [ "$JS_OK" = 1 ] && echo "    All tests passed."
