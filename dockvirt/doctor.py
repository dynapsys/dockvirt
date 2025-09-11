from __future__ import annotations

import os
import json
import logging
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
import pwd
import getpass
from typing import List, Tuple

# Constants and target context (handle sudo safely)
REPO_ROOT = Path(__file__).resolve().parents[1]

def _resolve_target_user_home() -> tuple[str, Path]:
    sudo_user = os.environ.get("SUDO_USER", "")
    if sudo_user and sudo_user != "root":
        try:
            return sudo_user, Path(pwd.getpwnam(sudo_user).pw_dir)
        except Exception:
            pass
    # Fallback to current process user
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    if not user:
        try:
            user = getpass.getuser()
        except Exception:
            user = "unknown"
    try:
        home = Path(pwd.getpwnam(user).pw_dir)
    except Exception:
        home = Path.home()
    return user, home

TARGET_USER, TARGET_HOME = _resolve_target_user_home()
CONFIG_DIR = TARGET_HOME / ".dockvirt"
IMAGES_DIR = CONFIG_DIR / "images"
GLOBAL_CONFIG = CONFIG_DIR / "config.yaml"

REQUIRED_CMDS = [
    "cloud-localds",
    "virsh",
    "virt-install",
    "qemu-img",
    "docker",
    "wget",
    "curl",
]

OPTIONAL_CMDS = [
    "make",
    "git",
]

# Logger (configured in main via setup_logging)
logger = logging.getLogger("dockvirt.doctor")

@dataclass
class Finding:
    ok: bool
    title: str
    detail: str
    fix: str | None = None

def run(cmd: str, check: bool = False, sudo: bool = False) -> Tuple[int, str, str]:
    """Run a shell command, logging inputs and outputs in detail."""
    shell_cmd = f"sudo -n bash -lc '{cmd}'" if sudo else f"bash -lc '{cmd}'"
    logger.debug("RUN: %s", shell_cmd)
    p = subprocess.run(shell_cmd, shell=True, text=True, capture_output=True)
    rc, out_s, err_s = p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    logger.debug("RC: %s", rc)
    if out_s:
        logger.debug("STDOUT:\n%s", out_s)
    if err_s:
        logger.debug("STDERR:\n%s", err_s)
    if check and rc != 0:
        raise RuntimeError(f"Command failed: {shell_cmd}\n{err_s}")
    return rc, out_s, err_s

def which(cmd: str) -> str | None:
    return shutil.which(cmd)

def detect_os() -> Tuple[str, str]:
    try:
        data = {}
        for line in (Path("/etc/os-release").read_text().splitlines()):
            if "=" in line:
                k, v = line.split("=", 1)
                data[k] = v.strip('"')
        return data.get("ID", platform.system().lower()), data.get("VERSION_ID", "")
    except Exception:
        return platform.system().lower(), platform.release()

def python_info() -> Finding:
    exe = sys.executable
    version = sys.version.replace("\n", " ")
    finding = Finding(
        ok=True,
        title="Python interpreter",
        detail=f"{exe} ({version})",
    )
    logger.info("Python: %s", finding.detail)
    return finding

def dockvirt_binding() -> List[Finding]:
    findings: List[Finding] = []
    exe_path = which("dockvirt")
    if exe_path:
        try:
            first = Path(exe_path).read_text().splitlines()[0]
        except Exception:
            first = ""
        findings.append(Finding(True, "dockvirt in PATH", exe_path))
        if first.startswith("#!"):
            findings.append(Finding(True, "dockvirt shebang", first))
        logger.info("dockvirt in PATH: %s", exe_path)
        if first:
            logger.debug("dockvirt shebang: %s", first)
    else:
        fix_hint = "pipx install dockvirt or pip install --user dockvirt"
        findings.append(Finding(False, "dockvirt in PATH", "Not found", fix=fix_hint))
        logger.warning("dockvirt not found in PATH")

    try:
        import dockvirt
        loc = getattr(dockvirt, "__file__", "<unknown>")
        findings.append(Finding(True, "dockvirt Python package", f"Loaded from {loc}"))
        logger.info("dockvirt package: %s", loc)
    except Exception as e:
        findings.append(
            Finding(
                False,
                "dockvirt Python package",
                f"Import failed: {e}",
                fix=f"{sys.executable} -m pip install -e .  # run in repo {REPO_ROOT}"
            )
        )
        logger.error("dockvirt import failed: %s", e)

    return findings

def check_commands() -> List[Finding]:
    out: List[Finding] = []
    for c in REQUIRED_CMDS + OPTIONAL_CMDS:
        p = which(c)
        if p:
            out.append(Finding(True, f"{c}", f"Found at {p}"))
        else:
            critical = c in REQUIRED_CMDS
            fix = None
            if critical:
                os_id, _ = detect_os()
                if os_id in ("ubuntu", "debian"):
                    mapping = {
                        "cloud-localds": "sudo apt install -y cloud-image-utils",
                        "virsh": "sudo apt install -y libvirt-clients libvirt-daemon-system",
                        "virt-install": "sudo apt install -y virt-install",
                        "qemu-img": "sudo apt install -y qemu-utils",
                        "docker": "curl -fsSL https://get.docker.com | sh",
                        "wget": "sudo apt install -y wget",
                        "curl": "sudo apt install -y curl",
                    }
                elif os_id in ("fedora", "centos", "rhel"):
                    mapping = {
                        "cloud-localds": "sudo dnf install -y cloud-utils",
                        "virsh": "sudo dnf install -y libvirt-client libvirt",
                        "virt-install": "sudo dnf install -y virt-install",
                        "qemu-img": "sudo dnf install -y qemu-img",
                        "docker": "curl -fsSL https://get.docker.com | sh",
                        "wget": "sudo dnf install -y wget",
                        "curl": "sudo dnf install -y curl",
                    }
                else:
                    mapping = {
                        "cloud-localds": "sudo pacman -S --noconfirm cloud-image-utils",
                        "virsh": "sudo pacman -S --noconfirm libvirt",
                        "virt-install": "sudo pacman -S --noconfirm virt-install",
                        "qemu-img": "sudo pacman -S --noconfirm qemu-img",
                        "docker": "sudo pacman -S --noconfirm docker",
                        "wget": "sudo pacman -S --noconfirm wget",
                        "curl": "sudo pacman -S --noconfirm curl",
                    }
                fix = mapping.get(c)
            finding = Finding(False, f"{c}", "Not found", fix=fix)
            out.append(finding)
            logger.warning("Missing command: %s (fix: %s)", c, fix or "n/a")
    return out

def check_services() -> List[Finding]:
    out: List[Finding] = []
    rc, out_s, _ = run("systemctl is-active libvirtd")
    if rc == 0 and out_s.strip() == "active":
        out.append(Finding(True, "libvirtd", "active"))
    else:
        fix = "sudo systemctl start libvirtd && sudo systemctl enable libvirtd"
        out.append(Finding(False, "libvirtd", "inactive", fix=fix))
        logger.warning("libvirtd inactive; fix: %s", fix)

    rc, _, _ = run("docker ps")
    if rc == 0:
        out.append(Finding(True, "docker daemon", "accessible"))
    else:
        fix = "sudo systemctl start docker && sudo systemctl enable docker"
        out.append(Finding(False, "docker daemon", "not accessible", fix=fix))
        logger.warning("docker daemon not accessible; fix: %s", fix)

    rc, nets, _ = run("virsh net-list --all")
    if rc == 0 and "default" in nets:
        if "inactive" in nets.splitlines()[-1]:
            fix = "virsh net-start default && virsh net-autostart default"
            out.append(Finding(False, "libvirt network 'default'", "present but inactive", fix=fix))
            logger.warning("libvirt network default inactive; fix: %s", fix)
        else:
            out.append(Finding(True, "libvirt network 'default'", "active"))
    else:
        fix = (
            "virsh net-define /usr/share/libvirt/networks/default.xml && "
            "virsh net-start default && virsh net-autostart default"
        )
        out.append(Finding(False, "libvirt network 'default'", "missing", fix=fix))
        logger.warning("libvirt network default missing; fix: %s", fix)

    return out

def check_groups_and_kvm() -> List[Finding]:
    out: List[Finding] = []
    rc, groups, _ = run(f"id -nG {TARGET_USER}")
    groups = groups or ""
    for g in ["libvirt", "kvm", "docker"]:
        if g in groups.split():
            out.append(Finding(True, f"group:{g}", "present"))
        else:
            fix = f"sudo usermod -aG {g} {TARGET_USER} && echo 'Relogin required'"
            out.append(Finding(False, f"group:{g}", "missing", fix=fix))
            logger.warning("Missing group '%s' for %s; fix: %s", g, TARGET_USER, fix)

    if Path("/dev/kvm").exists():
        out.append(Finding(True, "/dev/kvm", "exists"))
    else:
        fix = "Enable virtualization in BIOS/UEFI"
        out.append(Finding(False, "/dev/kvm", "missing", fix=fix))
        logger.warning("/dev/kvm missing; fix: %s", fix)

    return out

def check_config_and_project() -> List[Finding]:
    out: List[Finding] = []
    if GLOBAL_CONFIG.exists():
        out.append(Finding(True, "global config", str(GLOBAL_CONFIG)))
    else:
        fix = f"mkdir -p {CONFIG_DIR} && echo 'default_os: ubuntu22.04' > {GLOBAL_CONFIG}"
        out.append(Finding(False, "global config", "missing", fix=fix))
        logger.warning("Global config missing; fix: %s", fix)

    if IMAGES_DIR.exists():
        out.append(Finding(True, "images dir", str(IMAGES_DIR)))
    else:
        fix = f"mkdir -p {IMAGES_DIR}"
        out.append(Finding(False, "images dir", "missing", fix=fix))
        logger.warning("Images dir missing; fix: %s", fix)

    proj_file = Path.cwd() / ".dockvirt"
    if proj_file.exists():
        out.append(Finding(True, "project .dockvirt", str(proj_file)))
    else:
        fix = "Create a .dockvirt file with name/domain/image/port"
        out.append(Finding(False, "project .dockvirt", "missing", fix=fix))
        logger.warning("Project .dockvirt missing; fix: %s", fix)

    return out

def print_findings(title: str, findings: List[Finding], summary: bool = False) -> None:
    if not findings:
        return
    print(f"\n## {title}")
    for f in findings:
        status = "✅" if f.ok else "❌"
        line = f"{status} {f.title}: {f.detail}"
        print(line)
        if (not f.ok) and (f.fix) and (not summary):
            print(f"   ↳ fix: {f.fix}")
        logger.debug("%s %s: %s", status, f.title, f.detail)

def apply_fixes(findings: List[Finding], assume_yes: bool = False) -> None:
    cmds: List[str] = []
    for f in findings:
        if not f.ok and f.fix:
            cmds.append(f.fix)
    if not cmds:
        print("\n✅ No fixes required")
        return

    print("\n🔧 Proposed fixes (will run in order):")
    for c in cmds:
        print(f"  - {c}")
        logger.info("Proposed fix: %s", c)

    if not assume_yes:
        try:
            ans = input("\nProceed with fixes? [y/N]: ").strip().lower()
        except EOFError:
            ans = "n"
        if ans not in ("y", "yes"):
            print("❎ Skipping automatic fixes")
            return

    for c in cmds:
        print(f"\n▶ Running: {c}")
        rc, out_s, err_s = run(c, sudo=c.startswith("sudo"))
        if rc == 0:
            print("   ✅ success")
            logger.info("Fix OK: %s", c)
        else:
            print("   ❌ failed")
            logger.error("Fix FAILED (%s): rc=%s", c, rc)
            if out_s:
                print("   stdout:")
                print("   " + out_s.replace("\n", "\n   "))
            if err_s:
                print("   stderr:")
                print("   " + err_s.replace("\n", "\n   "))

def run_doctor(summary: bool, fix: bool, assume_yes: bool):
    os_id, os_ver = detect_os()

    print("🔍 Dockvirt Doctor")
    print("=" * 60)
    print(f"OS: {os_id} {os_ver}")
    print(f"Acting on behalf of user: {TARGET_USER} (HOME={TARGET_HOME})")

    f_py = [python_info()]
    f_dock = dockvirt_binding()
    f_cmds = check_commands()
    f_svc = check_services()
    f_grp = check_groups_and_kvm()
    f_cfg = check_config_and_project()

    print_findings("Python & Dockvirt binding", f_py + f_dock, summary)
    print_findings("Required & optional commands", f_cmds, summary)
    print_findings("Services & networks", f_svc, summary)
    print_findings("Groups & KVM", f_grp, summary)
    print_findings("Config & Project", f_cfg, summary)

    all_findings = f_py + f_dock + f_cmds + f_svc + f_grp + f_cfg

    if fix:
        apply_fixes(all_findings, assume_yes=assume_yes)
        print("\nℹ️ Some fixes (group membership) require re-login to take effect.")

    print("\nDone.")
