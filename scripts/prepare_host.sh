#!/usr/bin/env bash
set -euo pipefail

# Dockvirt host preparation helper (Fedora/Ubuntu/Arch compatible)
# - Ensures libvirt default network and storage pool are active
# - Fixes ACLs and SELinux labels for ~/.dockvirt (qemu access)
# - Optionally appends LIBVIRT_DEFAULT_URI to shell profile
#
# Usage:
#   bash scripts/prepare_host.sh
#
# Notes:
# - Will prompt for sudo where needed
# - Idempotent: safe to re-run

LOG() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
OK()  { printf "\033[1;32m[ OK ]\033[0m %s\n" "$*"; }
WARN(){ printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
ERR() { printf "\033[1;31m[FAIL]\033[0m %s\n" "$*"; }

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="${HOME}"
BASE_DIR="${HOME_DIR}/.dockvirt"
VENV_PY="${REPO_ROOT}/.venv-3.13/bin/python"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    ERR "Missing command: $1"
    return 1
  fi
}

run_sudo() {
  local cmd="$*"
  LOG "sudo $cmd"
  if ! sudo bash -c "$cmd"; then
    ERR "Command failed: sudo $cmd"
    exit 1
  fi
}

try_sudo() {
  local cmd="$*"
  LOG "sudo $cmd (ignore errors)"
  sudo bash -c "$cmd" || true
}

# 0) Basic checks
LOG "Checking required commands..."
require_cmd virsh || true
require_cmd qemu-img || true
require_cmd cloud-localds || true
require_cmd docker || true

# 1) Ensure base directories
LOG "Ensuring ${BASE_DIR} exists"
mkdir -p "${BASE_DIR}/images"
OK "Created/verified ${BASE_DIR}/images"

# 2) Ensure libvirt default network
LOG "Ensuring libvirt default network is defined and active"
if virsh net-info default >/dev/null 2>&1; then
  if virsh net-info default | grep -q "Active: *yes"; then
    OK "Network 'default' already active"
  else
    run_sudo "virsh net-start default"
    run_sudo "virsh net-autostart default"
  fi
else
  # Define from system XML if available, otherwise create a minimal NAT network
  if [ -f /usr/share/libvirt/networks/default.xml ]; then
    run_sudo "virsh net-define /usr/share/libvirt/networks/default.xml"
  else
    LOG "Creating minimal NAT network XML for 'default'"
    TMPXML="$(mktemp)"
    cat >"${TMPXML}" <<'XML'
<network>
  <name>default</name>
  <uuid/>
  <forward mode='nat'/>
  <bridge name='virbr0' stp='on' delay='0'/>
  <ip address='192.168.122.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.122.2' end='192.168.122.254'/>
    </dhcp>
  </ip>
</network>
XML
    run_sudo "virsh net-define ${TMPXML}"
    rm -f "${TMPXML}"
  fi
  run_sudo "virsh net-start default"
  run_sudo "virsh net-autostart default"
fi

# 3) Ensure libvirt default storage pool
LOG "Ensuring libvirt storage pool 'default' is active"
if virsh pool-info default >/dev/null 2>&1; then
  if virsh pool-info default | grep -q "Active: *yes"; then
    OK "Pool 'default' already active"
  else
    run_sudo "virsh pool-start default"
    run_sudo "virsh pool-autostart default"
  fi
else
  run_sudo "mkdir -p /var/lib/libvirt/images"
  run_sudo "virsh pool-define-as default dir --target /var/lib/libvirt/images"
  run_sudo "virsh pool-build default"
  run_sudo "virsh pool-start default"
  run_sudo "virsh pool-autostart default"
fi

# 4) Fix ACLs and SELinux contexts for ~/.dockvirt
LOG "Fixing ACLs and SELinux contexts for ${BASE_DIR}"
if [ -x "${VENV_PY}" ]; then
  "${VENV_PY}" "${REPO_ROOT}/scripts/fix_permissions.py" --apply
else
  WARN "Venv python not found at ${VENV_PY}; falling back to system python"
  python3 "${REPO_ROOT}/scripts/fix_permissions.py" --apply || true
fi

# 5) Optionally set LIBVIRT_DEFAULT_URI in user's shell profile
if ! grep -qs "LIBVIRT_DEFAULT_URI=qemu:///system" "${HOME_DIR}/.bashrc" 2>/dev/null \
   && ! grep -qs "LIBVIRT_DEFAULT_URI=qemu:///system" "${HOME_DIR}/.zshrc" 2>/dev/null; then
  LOG "Adding LIBVIRT_DEFAULT_URI to ~/.bashrc"
  echo "export LIBVIRT_DEFAULT_URI=qemu:///system" >> "${HOME_DIR}/.bashrc"
  OK "Appended to ~/.bashrc (open a new shell to apply)"
else
  OK "LIBVIRT_DEFAULT_URI already present in shell profile"
fi

OK "Host preparation completed"
