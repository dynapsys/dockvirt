#!/usr/bin/env python3
"""
Dockvirt Automation Agent

Automates environment diagnostics, permissions fixes, example testing (with domain
reachability), and cleanup. Designed to run with a developer venv and system libvirt.

Features:
- Doctor summary or auto-fix
- Ensure libvirt default network active (system libvirt)
- ACL + SELinux labeling helpers for ~/.dockvirt image files (qcow2, iso)
- Test examples end-to-end:
  * dockvirt up (using .dockvirt defaults)
  * get IP, HTTP by IP
  * DNS resolution check for domain (getent hosts)
  * HTTP by domain (with port)
  * optional: auto-append /etc/hosts (requires sudo) if domain not resolving
  * dockvirt down
- Generates a markdown report

Usage:
  python scripts/agent.py run --auto-fix --auto-hosts --skip-host-build

"""
import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Tuple, Optional, List

import click

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
DEFAULT_REPORT = REPO_ROOT / "agent_report.md"
DEFAULT_LIBVIRT_URI = os.environ.get("LIBVIRT_DEFAULT_URI", "qemu:///system")


def run(cmd: str, cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
    e = os.environ.copy()
    if env:
        e.update(env)
    if "LIBVIRT_DEFAULT_URI" not in e:
        e["LIBVIRT_DEFAULT_URI"] = DEFAULT_LIBVIRT_URI
    p = subprocess.run(cmd, shell=True, cwd=str(cwd) if cwd else None,
                       capture_output=True, text=True, env=e)
    return p.returncode, p.stdout, p.stderr


def parse_dockvirt(example_dir: Path) -> Dict[str, str]:
    cfg: Dict[str, str] = {}
    fpath = example_dir / ".dockvirt"
    if not fpath.exists():
        return cfg
    try:
        for line in fpath.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    except Exception:
        pass
    return cfg


def ensure_libvirt_default_network() -> List[str]:
    notes = []
    rc, out, err = run("virsh --connect qemu:///system net-info default")
    if rc != 0:
        # Try define+start+autostart
        notes.append("default network missing; attempting define/start/autostart")
        run("sudo systemctl enable --now libvirtd")
        run("sudo virsh net-define /usr/share/libvirt/networks/default.xml || true")
        run("sudo virsh net-start default || true")
        run("sudo virsh net-autostart default || true")
    else:
        if "Active: yes" not in out:
            run("sudo virsh net-start default || true")
            run("sudo virsh net-autostart default || true")
    return notes


def fix_acl_selinux(home: Path) -> List[str]:
    notes = []
    # ACLs for qemu traversal and file access
    cmds = [
        f"sudo setfacl -m u:qemu:x {home}",
        f"sudo setfacl -R -m u:qemu:rx {home}/.dockvirt",
        f"sudo find {home}/.dockvirt -type f -name '*.qcow2' -exec setfacl -m u:qemu:rw {{}} +",
        f"sudo find {home}/.dockvirt -type f -name '*.iso' -exec setfacl -m u:qemu:r {{}} +",
    ]
    for c in cmds:
        run(c)
    # SELinux labels (Fedora/SELinux): label only image files
    selinux_cmds = [
        f"sudo semanage fcontext -a -t svirt_image_t '{home}/.dockvirt(/.*)?\\.qcow2' || true",
        f"sudo semanage fcontext -a -t svirt_image_t '{home}/.dockvirt(/.*)?\\.iso' || true",
        f"sudo restorecon -Rv '{home}/.dockvirt' || true",
    ]
    for c in selinux_cmds:
        run(c)
    notes.append("Applied ACL and SELinux label fixes for ~/.dockvirt images")
    return notes


def get_vm_ip(name: str) -> str:
    # Try domifaddr (lease source)
    rc, out, _ = run(f"virsh --connect qemu:///system domifaddr {name} --source lease --full")
    if rc == 0:
        for line in out.splitlines():
            parts = line.strip().split()
            for token in parts:
                if "/" in token and token.count(".") == 3:
                    return token.split("/")[0]
    # Fallback: parse MAC and net-dhcp-leases
    rc, xml, _ = run(f"virsh --connect qemu:///system dumpxml {name}")
    if rc == 0:
        import re
        m = re.search(r"<mac address='([0-9A-Fa-f:]+)'", xml)
        if m:
            mac = m.group(1).lower()
            rc, leases, _ = run("virsh --connect qemu:///system net-dhcp-leases default")
            if rc == 0:
                for line in leases.splitlines():
                    if mac in line.lower():
                        for token in line.split():
                            if "/" in token and token.count(".") == 3:
                                return token.split("/")[0]
    return ""


def http_check(url: str, timeout: int = 15) -> Tuple[bool, int]:
    rc, out, err = run(f"curl -s -o /dev/null -w '%{{http_code}}' {url}")
    if rc == 0:
        try:
            code = int(out.strip())
            return code == 200, code
        except ValueError:
            return False, 0
    return False, 0


def ensure_domain_hosts(ip: str, domain: str) -> bool:
    # Append to /etc/hosts using sudo
    cmd = f"sudo sh -c 'echo \"{ip} {domain}\" >> /etc/hosts'"
    rc, out, err = run(cmd)
    return rc == 0


@click.group()
def cli():
    pass


@cli.command(name="run")
@click.option("--auto-fix", is_flag=True, help="Run doctor with --fix --yes and apply ACL/SELinux fixes")
@click.option("--auto-hosts", is_flag=True, help="Automatically append domain mappings to /etc/hosts if unresolved")
@click.option("--skip-host-build", is_flag=True, help="Skip host docker build; let VM build the image")
@click.option("--os", "os_list", multiple=True, default=["ubuntu22.04", "fedora38"],
              help="OS variants to test (can be repeated)")
@click.option("--example", "example_names", multiple=True, default=[], help="Specific examples to test")
@click.option("--report-file", default=str(DEFAULT_REPORT), help="Where to write the markdown report")
def run_agent(auto_fix: bool, auto_hosts: bool, skip_host_build: bool, os_list: List[str],
              example_names: List[str], report_file: str):
    """Run the Dockvirt automation agent."""
    report_lines: List[str] = []
    report_lines.append("# Dockvirt Automation Agent Report")
    report_lines.append("")

    # Environment info
    py = sys.executable
    report_lines.append(f"Python: {py}")
    report_lines.append(f"LIBVIRT_DEFAULT_URI: {os.environ.get('LIBVIRT_DEFAULT_URI', DEFAULT_LIBVIRT_URI)}")

    # Doctor
    if auto_fix:
        report_lines.append("\n## Doctor (auto-fix)")
        run(f"{py} scripts/doctor.py --fix --yes")
        ensure_libvirt_default_network()
        fix_acl_selinux(Path.home())
    else:
        report_lines.append("\n## Doctor (summary)")
        run(f"{py} scripts/doctor.py --summary")
        ensure_libvirt_default_network()

    # Examples to test
    examples: List[Path]
    if example_names:
        examples = [EXAMPLES_DIR / name for name in example_names if (EXAMPLES_DIR / name).exists()]
    else:
        examples = [p for p in EXAMPLES_DIR.iterdir() if p.is_dir() and not p.name.startswith('.')]

    for ex in examples:
        settings = parse_dockvirt(ex)
        name = settings.get("name", f"test-{ex.name}")
        domain = settings.get("domain", f"{name}.test.local")
        image = settings.get("image", f"test-{ex.name}")
        port = str(settings.get("port", "80"))

        report_lines.append(f"\n## Example: {ex.name}")
        report_lines.append(f"Domain: {domain}")
        report_lines.append(f"Image: {image}")

        for os_variant in os_list:
            vm_name = f"{name}-{os_variant}"
            report_lines.append(f"\n### OS: {os_variant}")
            # Skip host build if requested
            if not skip_host_build and (ex / "Dockerfile").exists() and shutil.which("docker"):
                run("docker build -t %s ." % image, cwd=ex)

            # Up
            cmd_up = (
                f"{py} -m dockvirt.cli up --name {vm_name} --domain {domain} "
                f"--image {image} --port {port} --os {os_variant}"
            )
            rc, out, err = run(cmd_up, cwd=ex)
            if rc != 0:
                report_lines.append(f"- ❌ up failed: {err.strip()}")
                continue
            report_lines.append("- ✅ up succeeded")

            # Wait and get IP
            ip = ""
            for _ in range(45):
                time.sleep(2)
                ip = get_vm_ip(vm_name)
                if ip:
                    break
            if not ip:
                report_lines.append("- ❌ No IP (domifaddr/leases) after 90s")
                run(f"{py} -m dockvirt.cli down --name {vm_name}")
                continue
            report_lines.append(f"- 🌐 IP: {ip}")

            # HTTP by IP
            ip_url = f"http://{ip}/" if port == "80" else f"http://{ip}:{port}/"
            ok_ip, code_ip = http_check(ip_url)
            if ok_ip:
                report_lines.append(f"- ✅ HTTP by IP OK: {ip_url}")
            else:
                report_lines.append(f"- ⚠️ HTTP by IP failed ({code_ip}): {ip_url}")

            # Domain resolve
            rc, dns_out, _ = run(f"getent hosts {domain}")
            if rc == 0 and dns_out.strip():
                report_lines.append(f"- 🧭 Domain resolves: {domain}")
            else:
                report_lines.append(f"- ❌ Domain not resolving locally: {domain}")
                if auto_hosts and ip:
                    if ensure_domain_hosts(ip, domain):
                        report_lines.append("  - ✅ Added to /etc/hosts")
                    else:
                        report_lines.append("  - ❌ Failed to add to /etc/hosts")

            # HTTP by domain
            dom_url = f"http://{domain}/" if port == "80" else f"http://{domain}:{port}/"
            ok_dom, code_dom = http_check(dom_url)
            if ok_dom:
                report_lines.append(f"- ✅ HTTP via domain OK: {dom_url}")
            else:
                report_lines.append(f"- ⚠️ HTTP via domain failed ({code_dom}): {dom_url}")

            # Down
            run(f"{py} -m dockvirt.cli down --name {vm_name}")

    # Write report
    Path(report_file).write_text("\n".join(report_lines), encoding="utf-8")
    click.echo(f"Report saved to {report_file}")


if __name__ == "__main__":
    cli()
