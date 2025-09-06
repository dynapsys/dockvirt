"""
Self-healing utilities for dockvirt.

Provides preflight checks, auto-remediation helpers, and on-error suggestions.
Designed to run without sudo by default. Functions that may require sudo will
only execute if allow_sudo=True or a specific environment flag is set.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from .config import CONFIG_DIR

LIBVIRT_URI = os.environ.get("LIBVIRT_DEFAULT_URI", "qemu:///system")


@dataclass
class HealResult:
    changed: bool
    notes: List[str]
    error: str | None = None


def _run(cmd: str, env: Dict[str, str] | None = None) -> Tuple[int, str, str]:
    e = os.environ.copy()
    if env:
        e.update(env)
    if "LIBVIRT_DEFAULT_URI" not in e:
        e["LIBVIRT_DEFAULT_URI"] = LIBVIRT_URI
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True, env=e)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def ensure_cli_log_file() -> Path:
    log_dir = CONFIG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "cli.log"
    if not log_file.exists():
        try:
            log_file.touch()
        except Exception:
            pass
    return log_file


def preflight_network() -> HealResult:
    notes: List[str] = []
    rc, out, _ = _run("virsh --connect qemu:///system net-info default")
    if rc == 0 and "Active: yes" in out:
        return HealResult(False, ["default network active"])

    # Try to activate without sudo (works if user has libvirt privileges)
    _run("virsh net-define /usr/share/libvirt/networks/default.xml || true")
    _run("virsh net-start default || true")
    _run("virsh net-autostart default || true")

    rc2, out2, _ = _run("virsh --connect qemu:///system net-info default")
    if rc2 == 0 and "Active: yes" in out2:
        notes.append("activated default network")
        return HealResult(True, notes)

    notes.append(
        "default network not active. Run: sudo virsh net-define /usr/share/libvirt/networks/default.xml && "
        "sudo virsh net-start default && sudo virsh net-autostart default"
    )
    return HealResult(False, notes)


def unify_images_mapping(config: Dict) -> HealResult:
    """Ensure 'images' and 'os_images' both exist and include known defaults."""
    changed = False
    images_map: Dict = {}
    if isinstance(config.get("images"), dict):
        images_map.update(config["images"])
    if isinstance(config.get("os_images"), dict):
        for k, v in config["os_images"].items():
            images_map.setdefault(k, v)

    # Ensure at least ubuntu22.04 and fedora38 exist if absent
    defaults = {
        "ubuntu22.04": {
            "url": "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img",
            "variant": "ubuntu22.04",
        },
        "fedora38": {
            "url": "https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/38/Cloud/x86_64/images/Fedora-Cloud-Base-38-1.6.x86_64.qcow2",
            "variant": "fedora38",
        },
    }
    for k, v in defaults.items():
        if k not in images_map:
            images_map[k] = v
            changed = True

    if images_map != config.get("images"):
        config["images"] = images_map
        changed = True
    if images_map != config.get("os_images"):
        config["os_images"] = images_map
        changed = True

    return HealResult(changed, [f"images map unified ({len(images_map)} entries)"])


def advise_acl_selinux(vm_name: str | None = None) -> HealResult:
    home = str(Path.home())
    vm_dir = f"{home}/.dockvirt/{vm_name}" if vm_name else f"{home}/.dockvirt"
    return HealResult(
        False,
        [
            "For qemu:///system, apply ACL+SELinux to allow qemu access to ~/.dockvirt:",
            f"sudo setfacl -m u:qemu:x '{home}'",
            f"sudo setfacl -R -m u:qemu:rx '{home}/.dockvirt'",
            f"sudo find '{home}/.dockvirt' -type f -name '*.qcow2' -exec setfacl -m u:qemu:rw {{}} +",
            f"sudo find '{home}/.dockvirt' -type f -name '*.iso' -exec setfacl -m u:qemu:r {{}} +",
            "# SELinux (if enabled):",
            f"sudo semanage fcontext -a -t svirt_image_t '{home}/.dockvirt(/.*)?\\.qcow2'",
            f"sudo semanage fcontext -a -t svirt_image_t '{home}/.dockvirt(/.*)?\\.iso'",
            f"sudo restorecon -Rv '{home}/.dockvirt'",
            f"(affected VM dir: {vm_dir})",
        ],
    )


def add_hosts_entry(domain: str, ip: str, allow_sudo: bool = False) -> HealResult:
    if not domain or not ip:
        return HealResult(False, ["missing domain or ip"], error="missing_args")
    if not allow_sudo and os.environ.get("DOCKVIRT_AUTO_HOSTS") != "1":
        return HealResult(False, [f"Run to add hosts entry: echo '{ip} {domain}' | sudo tee -a /etc/hosts"])
    cmd = f"sudo sh -c 'echo \"{ip} {domain}\" >> /etc/hosts'"
    rc, out, err = _run(cmd)
    if rc == 0:
        return HealResult(True, [f"added {domain} -> {ip} to /etc/hosts"]) 
    return HealResult(False, ["failed to add /etc/hosts entry", err.strip()])


def on_exception_hints(exc_text: str, vm_name: str | None = None) -> HealResult:
    txt = (exc_text or "").lower()
    if "unknown operating system" in txt:
        return HealResult(False, [
            "Unknown OS variant. Ensure your config has images/os_images keys with the requested OS.",
            "Run: dockvirt heal --apply (or python scripts/doctor.py --fix --yes)",
        ])
    if "permission denied" in txt and "cidata.iso" in txt:
        hints = advise_acl_selinux(vm_name).notes
        return HealResult(False, ["Permission denied creating cidata.iso."] + hints)
    if "cloud-localds" in txt and "not found" in txt:
        return HealResult(False, [
            "cloud-localds missing. Install cloud-image-utils/cloud-utils depending on your distro.",
            "Run 'dockvirt check' for distro-specific instructions.",
        ])
    if "virsh" in txt and "not found" in txt:
        return HealResult(False, [
            "virsh missing. Install libvirt clients and ensure libvirtd is active.",
            "Run 'dockvirt check' for fix steps.",
        ])
    return HealResult(False, ["See logs in ~/.dockvirt/cli.log and run 'dockvirt heal' for more info."])


def run_heal(apply: bool = False, auto_hosts: bool = False) -> List[str]:
    """High-level healing routine used by CLI."""
    notes: List[str] = []
    # Ensure log file
    logf = ensure_cli_log_file()
    notes.append(f"logs: {logf}")

    # Default network
    res = preflight_network()
    notes.extend(["network:"] + res.notes)

    # Optionally guidance for ACL/SELinux (printed only)
    notes.append("If you get permission denied on ~/.dockvirt/*.iso/*.qcow2, see ACL/SELinux notes.")

    # Auto-hosts is handled within add_hosts_entry() when called by agent/tests
    if auto_hosts:
        os.environ["DOCKVIRT_AUTO_HOSTS"] = "1"
        notes.append("auto-hosts enabled")

    return notes
