#!/usr/bin/env python3
"""
Dockvirt Doctor: Diagnose and (optionally) fix environment issues.

Goals
- Detect mismatched Python interpreter vs installed dockvirt package
- Verify required system tools (cloud-localds, virsh, virt-install, qemu-img,
  docker, wget)
- Verify libvirtd service and libvirt default network
- Verify user groups (libvirt, kvm, docker) and KVM availability (/dev/kvm)
- Verify config directories (~/.dockvirt, images/) and permissions
- Verify project-level .dockvirt for defaults

Usage
  python3 scripts/doctor.py                # diagnostics only
  python3 scripts/doctor.py --summary      # compact diagnostics
  python3 scripts/doctor.py --verbose      # detailed console logging
  python3 scripts/doctor.py --log-file     # write detailed log to file
  python3 scripts/doctor.py --json         # machine-readable JSON summary
  python3 scripts/doctor.py --fix          # attempt non-destructive fixes
  python3 scripts/doctor.py --fix --yes    # auto-approve when needed

This script is safe by default. It will NOT run privileged commands unless
--fix is provided. Some fixes require sudo; they will be printed first and
you will be asked to confirm unless --yes is used.
"""

from __future__ import annotations

import argparse
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


def is_wsl() -> bool:
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except Exception:
        return False


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
        # Try to read shebang
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

    # Try importing the module with current interpreter
    try:
        import dockvirt  # type: ignore
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


def check_home_dir_permissions() -> List[Finding]:
    out: List[Finding] = []
    try:
        if CONFIG_DIR.exists():
            uid = pwd.getpwnam(TARGET_USER).pw_uid
            st = CONFIG_DIR.stat()
            if st.st_uid != uid:
                fix = f"sudo chown -R {TARGET_USER}:{TARGET_USER} {CONFIG_DIR}"
                out.append(Finding(False, "~/.dockvirt ownership", "owned by another user", fix=fix))
            else:
                out.append(Finding(True, "~/.dockvirt ownership", "correct"))
        else:
            out.append(Finding(True, "~/.dockvirt dir", "will be created on first run"))
    except Exception as e:
        out.append(Finding(False, "~/.dockvirt check failed", str(e)))
    return out


def check_environment_settings() -> List[Finding]:
    out: List[Finding] = []
    uri = os.environ.get("LIBVIRT_DEFAULT_URI", "")
    if uri:
        ok = uri == "qemu:///system"
        fix = None if ok else "export LIBVIRT_DEFAULT_URI=qemu:///system"
        out.append(Finding(ok, "LIBVIRT_DEFAULT_URI", uri, fix=fix))
    else:
        out.append(Finding(False, "LIBVIRT_DEFAULT_URI", "not set", fix="export LIBVIRT_DEFAULT_URI=qemu:///system"))
    return out


def check_services() -> List[Finding]:
    out: List[Finding] = []
    # libvirtd active
    rc, out_s, _ = run("systemctl is-active libvirtd")
    if rc == 0 and out_s.strip() == "active":
        out.append(Finding(True, "libvirtd", "active"))
    else:
        fix = "sudo systemctl start libvirtd && sudo systemctl enable libvirtd"
        out.append(Finding(False, "libvirtd", "inactive", fix=fix))
        logger.warning("libvirtd inactive; fix: %s", fix)

    # docker daemon accessible
    rc, _, _ = run("docker ps")
    if rc == 0:
        out.append(Finding(True, "docker daemon", "accessible"))
    else:
        fix = "sudo systemctl start docker && sudo systemctl enable docker"
        out.append(Finding(False, "docker daemon", "not accessible", fix=fix))
        logger.warning("docker daemon not accessible; fix: %s", fix)

    # libvirt default network
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
    # Global config (for TARGET_USER)
    if GLOBAL_CONFIG.exists():
        out.append(Finding(True, "global config", str(GLOBAL_CONFIG)))
    else:
        fix = f"mkdir -p {CONFIG_DIR} && echo 'default_os: ubuntu22.04' > {GLOBAL_CONFIG}"
        out.append(Finding(False, "global config", "missing", fix=fix))
        logger.warning("Global config missing; fix: %s", fix)

    # Images dir
    if IMAGES_DIR.exists():
        out.append(Finding(True, "images dir", str(IMAGES_DIR)))
    else:
        fix = f"mkdir -p {IMAGES_DIR}"
        out.append(Finding(False, "images dir", "missing", fix=fix))
        logger.warning("Images dir missing; fix: %s", fix)

    # Project .dockvirt
    proj_file = Path.cwd() / ".dockvirt"
    if proj_file.exists():
        # Minimal validation
        content = proj_file.read_text()
        required = ["name=", "domain=", "image=", "port="]
        missing = [k for k in required if k not in content]
        if missing:
            msg = f"present but missing keys: {', '.join(missing)}"
            out.append(Finding(False, "project .dockvirt", msg))
            logger.warning("Project .dockvirt incomplete: %s", msg)
        else:
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
            # Multi-command lines separated by '&&' should be one shell execution
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


def setup_logging(verbose: bool = False, log_file: Path | None = None) -> None:
    """Configure console and optional file logging."""
    logger.setLevel(logging.DEBUG)
    # Avoid duplicate handlers on repeated runs
    if not logger.handlers:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.DEBUG if verbose else logging.INFO)
        sh.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(sh)
        if log_file is not None:
            try:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                fh = logging.FileHandler(log_file)
                fh.setLevel(logging.DEBUG)
                fh.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(levelname)s - %(message)s"
                    )
                )
                logger.addHandler(fh)
            except Exception:
                # Fall back silently if file logging can't be set up
                pass


def findings_to_json(sections: List[tuple[str, List[Finding]]]) -> str:
    data = []
    for title, items in sections:
        data.append({
            "section": title,
            "findings": [
                {"ok": f.ok, "title": f.title, "detail": f.detail, "fix": f.fix}
                for f in items
            ],
        })
    return json.dumps({"doctor": data}, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dockvirt Doctor")
    parser.add_argument("--summary", action="store_true", help="Print compact summary only")
    parser.add_argument("--fix", action="store_true", help="Attempt non-destructive fixes (may require sudo)")
    parser.add_argument("--yes", action="store_true", help="Assume 'yes' for prompts when using --fix")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose console logging")
    parser.add_argument("--log-file", help="Write detailed log to this file (default: ~/.dockvirt/doctor.log)")
    parser.add_argument("--json", action="store_true", help="Print JSON summary of findings and exit")
    args = parser.parse_args()

    # Configure logging
    default_log = CONFIG_DIR / "doctor.log"
    log_path = Path(args.log_file).expanduser() if args.log_file else default_log
    setup_logging(verbose=bool(args.verbose), log_file=log_path)

    os_id, os_ver = detect_os()
    wsl = is_wsl()

    print("🔍 Dockvirt Doctor")
    print("=" * 60)
    print(f"OS: {os_id} {os_ver}{' (WSL)' if wsl else ''}")
    # Show target context (handles sudo safely)
    print(f"Acting on behalf of user: {TARGET_USER} (HOME={TARGET_HOME})")

    f_py = [python_info()]
    f_dock = dockvirt_binding()
    f_cmds = check_commands()
    f_svc = check_services()
    f_grp = check_groups_and_kvm()
    f_cfg = check_config_and_project()
    f_perm = check_home_dir_permissions()
    f_env = check_environment_settings()

    summary = args.summary
    print_findings("Python & Dockvirt binding", f_py + f_dock, summary)
    print_findings("Required & optional commands", f_cmds, summary)
    print_findings("Services & networks", f_svc, summary)
    print_findings("Groups & KVM", f_grp, summary)
    print_findings("Config & Project", f_cfg, summary)
    print_findings("Directory ownership", f_perm, summary)
    print_findings("Environment", f_env, summary)

    all_findings = f_py + f_dock + f_cmds + f_svc + f_grp + f_cfg + f_perm + f_env

    # Optional JSON output
    if args.json:
        sections = [
            ("Python & Dockvirt binding", f_py + f_dock),
            ("Required & optional commands", f_cmds),
            ("Services & networks", f_svc),
            ("Groups & KVM", f_grp),
            ("Config & Project", f_cfg),
            ("Directory ownership", f_perm),
            ("Environment", f_env),
        ]
        print(findings_to_json(sections))
        return

    if args.fix:
        apply_fixes(all_findings, assume_yes=args.yes)
        print("\nℹ️ Some fixes (group membership) require re-login to take effect.")

    print("\nDone.")


if __name__ == "__main__":
    main()
