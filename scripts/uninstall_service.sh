#!/usr/bin/env bash
# =============================================================================
# uninstall_service.sh — Remove base-inference systemd service
# =============================================================================
#
# Stops the service, disables auto-start, and removes the unit file.
# Must be run as root (called via ``sudo ./base-inference service uninstall``).
# =============================================================================

set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────────────────

UNIT_NAME="base-inference"
UNIT_FILE="/etc/systemd/system/${UNIT_NAME}.service"

# A host provisioned before 2026-09-10 has the unit under its old name. Remove
# that one too, or `uninstall` leaves behind the very service it was asked to
# take away.
LEGACY_UNIT_NAME="idia-server"
LEGACY_UNIT_FILE="/etc/systemd/system/${LEGACY_UNIT_NAME}.service"

# ── Colours ──────────────────────────────────────────────────────────────────

if [ -t 1 ] && command -v tput &>/dev/null; then
    GREEN="$(tput setaf 2)"
    YELLOW="$(tput setaf 3)"
    RED="$(tput setaf 1)"
    RESET="$(tput sgr0)"
else
    GREEN="" YELLOW="" RED="" RESET=""
fi

_info()  { echo "${GREEN}[✓]${RESET} $*"; }
_warn()  { echo "${YELLOW}[⚠]${RESET} $*"; }

# ── Pre-flight checks ────────────────────────────────────────────────────────

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Use:  sudo ./base-inference service uninstall" >&2
    exit 1
fi

if [ ! -f "$UNIT_FILE" ] && [ ! -f "$LEGACY_UNIT_FILE" ]; then
    echo "Unit file not found at $UNIT_FILE — already uninstalled?" >&2
    exit 0
fi

# ── Remove the pre-rename unit, if this host still has it ────────────────────
# Checked before the current unit, because a host provisioned before
# 2026-09-10 may have only the old one — and exiting early on the absence of
# the new name would leave the old service running while reporting success.

if [ -f "$LEGACY_UNIT_FILE" ]; then
    systemctl disable --now "${LEGACY_UNIT_NAME}.service" 2>/dev/null || true
    rm -f "$LEGACY_UNIT_FILE"
    _info "Pre-rename unit removed: $LEGACY_UNIT_FILE"
fi

if [ ! -f "$UNIT_FILE" ]; then
    systemctl daemon-reload
    _info "systemd daemon reloaded"
    exit 0
fi

# ── Disable and stop ─────────────────────────────────────────────────────────

if systemctl is-active --quiet "$UNIT_NAME" 2>/dev/null; then
    systemctl stop "$UNIT_NAME"
    _info "Service stopped"
else
    _info "Service was not running"
fi

if systemctl is-enabled --quiet "$UNIT_NAME" 2>/dev/null; then
    systemctl disable "$UNIT_NAME"
    _info "Service disabled"
else
    _info "Service was not enabled"
fi

# ── Remove unit file ─────────────────────────────────────────────────────────

rm -f "$UNIT_FILE"
_info "Unit file removed: $UNIT_FILE"

systemctl daemon-reload
_info "systemd daemon reloaded"

echo ""
echo "${GREEN}[✓]${RESET} base-inference service uninstalled."
echo "    The server will no longer start automatically on boot."
echo "    Use \`./base-inference deploy local\` to start manually."
echo ""
