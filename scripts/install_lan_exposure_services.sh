#!/usr/bin/env bash
set -euo pipefail

# Installer for persistent DockerVirt LAN exposure services
# - dockvirt-test-server.service (Python HTTP server on localhost:PORT)
# - dockvirt-lan-expose.service  (iptables DNAT Host:80 -> localhost:PORT)

usage() {
  cat <<EOF
Usage: sudo bash scripts/install_lan_exposure_services.sh \
         --user <username> \
         --repo <absolute_repo_path> \
         [--port 8080] [--host 127.0.0.1]

Examples:
  sudo bash scripts/install_lan_exposure_services.sh \
       --user $(logname) --repo $(pwd) --port 8080
EOF
}

# Defaults
PORT=8080
HOST=127.0.0.1
USER_NAME=""
REPO_DIR=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --user) USER_NAME="$2"; shift 2;;
    --repo) REPO_DIR="$2"; shift 2;;
    --port) PORT="$2"; shift 2;;
    --host) HOST="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

# Validations
if [[ $EUID -ne 0 ]]; then
  echo "This installer must be run as root (use sudo)." >&2
  exit 1
fi

if [[ -z "$USER_NAME" || -z "$REPO_DIR" ]]; then
  echo "--user and --repo are required" >&2
  usage
  exit 1
fi

if [[ ! -f "$REPO_DIR/scripts/test_server.py" ]]; then
  echo "Missing: $REPO_DIR/scripts/test_server.py" >&2
  exit 1
fi
if [[ ! -f "$REPO_DIR/scripts/dockvirt_lan_simple.sh" ]]; then
  echo "Missing: $REPO_DIR/scripts/dockvirt_lan_simple.sh" >&2
  exit 1
fi

UNIT_DIR="/etc/systemd/system"
TEMPLATES_DIR="$REPO_DIR/scripts/systemd"

mkdir -p "$UNIT_DIR"

# Render unit: dockvirt-test-server.service
sed -e "s|{{USER}}|$USER_NAME|g" \
    -e "s|{{REPO_DIR}}|$REPO_DIR|g" \
    -e "s|{{HOST}}|$HOST|g" \
    -e "s|{{PORT}}|$PORT|g" \
    "$TEMPLATES_DIR/dockvirt-test-server.service.tmpl" \
    > "$UNIT_DIR/dockvirt-test-server.service"

# Render unit: dockvirt-lan-expose.service
sed -e "s|{{REPO_DIR}}|$REPO_DIR|g" \
    -e "s|{{PORT}}|$PORT|g" \
    "$TEMPLATES_DIR/dockvirt-lan-expose.service.tmpl" \
    > "$UNIT_DIR/dockvirt-lan-expose.service"

# Reload and enable
systemctl daemon-reload
systemctl enable --now dockvirt-test-server.service
systemctl enable --now dockvirt-lan-expose.service

# Show status summary
sleep 1
systemctl --no-pager --full status dockvirt-test-server.service | sed -n '1,25p' || true
systemctl --no-pager --full status dockvirt-lan-expose.service | sed -n '1,25p' || true

# Quick verification commands
cat <<EOVER

Next steps (verification):
  ss -tuln | grep :8080 || sudo ss -tuln | grep :8080
  sudo iptables -t nat -L PREROUTING -n | grep -E "DNAT|REDIRECT"
  curl -sS http://localhost:$PORT/ | head -3
  # Replace with your LAN IP if different:
  curl -sS http://192.168.188.226:80/ | head -3 || true

To uninstall:
  sudo bash scripts/uninstall_lan_exposure_services.sh
EOVER
