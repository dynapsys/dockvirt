#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (use sudo)." >&2
  exit 1
fi

SERVICES=(dockvirt-test-server.service dockvirt-lan-expose.service)

for SVC in "${SERVICES[@]}"; do
  systemctl disable --now "$SVC" 2>/dev/null || true
  rm -f "/etc/systemd/system/$SVC" 2>/dev/null || true
done

systemctl daemon-reload
systemctl reset-failed || true

echo "Removed services: ${SERVICES[*]}"

echo "You can re-install with:"
echo "  sudo bash scripts/install_lan_exposure_services.sh --user $(logname) --repo $(pwd) --port 8080"
