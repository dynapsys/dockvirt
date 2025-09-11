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
from queue import Queue, Empty
from datetime import datetime
import click

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
LOGS_DIR = REPO_ROOT / "logs"
DEFAULT_REPORT = REPO_ROOT / "agent_report.md"
DEFAULT_LIBVIRT_URI = os.environ.get("LIBVIRT_DEFAULT_URI", "qemu:///system")


class HealthReport:
    """Data class for health check results."""

    def __init__(self, vm_name: str, domain: str, ip: str, port: str):
        self.vm_name = vm_name
        self.domain = domain
        self.ip = ip
        self.port = port
        self.report_path = (
            LOGS_DIR / f"health_report_{vm_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        LOGS_DIR.mkdir(exist_ok=True)
        self.report_path.touch()
        print(f"[agent] Health reports for {vm_name} will be saved to {self.report_path}")

    def add(self, msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        print(f"[health-check:{self.vm_name}] {msg}")
        with self.report_path.open("a", encoding="utf-8") as f:
            f.write(line)


def health_check_worker(queue: Queue, report: HealthReport, interval: int):
    """Periodically checks VM health and logs to a report."""
    report.add("Health monitoring started.")
    while True:
        try:
            if queue.get_nowait() == "stop":
                report.add("Health monitoring stopping.")
                break
        except Empty:
            pass

        current_ip = get_vm_ip(report.vm_name)
        if current_ip:
            if report.ip != current_ip:
                report.add(f"IP changed from {report.ip} to {current_ip}")
                report.ip = current_ip
            report.add(f"IP: {current_ip} (OK)")
        else:
            report.add("IP: Not found (Error)")

        rc, _, _ = run(f"getent hosts {report.domain}")
        report.add(
            f"Domain: {report.domain} ({'Resolves' if rc == 0 else 'Not Resolving'})")

        http_url = f"http://{report.ip}:{report.port}/"
        ok, code = http_check(http_url, host=report.domain)
        report.add(f"HTTP: {http_url} -> {code} ({'OK' if ok else 'Failed'})")

        cli_log_tail = _tail(Path.home() / ".dockvirt" / "cli.log", 10)
        if cli_log_tail:
            report.add(f"--- cli.log tail ---\n{cli_log_tail}\n--------------------")

        time.sleep(interval)


import threading

def run(
    cmd: str,
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    echo: bool = False,
) -> Tuple[int, str, str]:
    e = os.environ.copy()
    if env:
        e.update(env)
    if "LIBVIRT_DEFAULT_URI" not in e:
        e["LIBVIRT_DEFAULT_URI"] = DEFAULT_LIBVIRT_URI
    if echo:
        print(f"$ {cmd}")
    p = subprocess.run(
        cmd,
        shell=True,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        env=e,
    )
    if echo and (p.stdout or p.stderr):
        if p.stdout:
            print(p.stdout, end="")
        if p.stderr:
            print(p.stderr, end="")
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
# Allow importing dockvirt source and scripts helpers
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:  # Structured event logging (JSONL)
    from dockvirt.logdb import append_event as log_event  # type: ignore
except Exception:  # fallback no-op
    def log_event(event_type: str, data: Dict[str, str]) -> None:  # type: ignore
        return

try:  # Local LLM helper (ollama)
    from llm_helper import available as llm_available, suggest_fixes  # type: ignore
except Exception:
    def llm_available() -> bool:  # type: ignore
        return False

    def suggest_fixes(context: str, max_tokens: int = 256):  # type: ignore
        return []


def ensure_libvirt_default_network(verbose: bool = False) -> List[str]:
    notes = []
    rc, out, err = run("virsh --connect qemu:///system net-info default", echo=verbose)
    if rc != 0:
        # Try define+start+autostart
        notes.append("default network missing; attempting define/start/autostart")
        run("sudo systemctl enable --now libvirtd", echo=verbose)
        run("sudo virsh net-define /usr/share/libvirt/networks/default.xml || true", echo=verbose)
        run("sudo virsh net-start default || true", echo=verbose)
        run("sudo virsh net-autostart default || true", echo=verbose)
    else:
        if "Active: yes" not in out:
            run("sudo virsh net-start default || true", echo=verbose)
            run("sudo virsh net-autostart default || true", echo=verbose)
    return notes


def fix_acl_selinux(home: Path, verbose: bool = False) -> List[str]:
    notes = []
    # ACLs for qemu traversal and file access
    cmds = [
        f"sudo setfacl -m u:qemu:x {home}",
        f"sudo setfacl -R -m u:qemu:rx {home}/.dockvirt",
        f"sudo find {home}/.dockvirt -type f -name '*.qcow2' -exec setfacl -m u:qemu:rw {{}} +",
        f"sudo find {home}/.dockvirt -type f -name '*.iso' -exec setfacl -m u:qemu:r {{}} +",
    ]
    for c in cmds:
        run(c, echo=verbose)
    # SELinux labels (Fedora/SELinux): label only image files
    selinux_cmds = [
        f"sudo semanage fcontext -a -t svirt_image_t '{home}/.dockvirt(/.*)?\\.qcow2' || true",
        f"sudo semanage fcontext -a -t svirt_image_t '{home}/.dockvirt(/.*)?\\.iso' || true",
        f"sudo restorecon -Rv '{home}/.dockvirt' || true",
    ]
    for c in selinux_cmds:
        run(c, echo=verbose)
    notes.append("Applied ACL and SELinux label fixes for ~/.dockvirt images")
    return notes


def fix_ownership(home: Path, verbose: bool = False) -> List[str]:
    """Ensure ~/.dockvirt belongs to the current user to avoid write errors."""
    notes: List[str] = []
    cmd = f"sudo chown -R $USER:$USER '{home}/.dockvirt' || true"
    run(cmd, echo=verbose)
    notes.append("Ownership of ~/.dockvirt corrected (if needed)")
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


def http_check(url: str, timeout: int = 15, host: str | None = None) -> Tuple[bool, int]:
    header = f"-H 'Host: {host}'" if host else ""
    # Add connect/read timeouts and follow redirects
    rc, out, err = run(
        f"curl -sS -L --connect-timeout 5 --max-time 10 -o /dev/null -w '%{{http_code}}' {header} {url}"
    )
    if rc == 0:
        try:
            code = int(out.strip())
            return code == 200, code
        except ValueError:
            return False, 0
    return False, 0


def wait_http(url: str, seconds: int = 300, interval: int = 5, host: str | None = None) -> Tuple[bool, int]:
    """Poll HTTP until 200 or timeout."""
    elapsed = 0
    while elapsed < seconds:
        ok, code = http_check(url, host=host)
        if ok:
            return True, code
        time.sleep(interval)
        elapsed += interval
    return False, code if 'code' in locals() else 0


def ensure_domain_hosts(ip: str, domain: str) -> bool:
    # Append to /etc/hosts using sudo
    cmd = f"sudo sh -c 'echo \"{ip} {domain}\" >> /etc/hosts'"
    rc, out, err = run(cmd)
    return rc == 0


def _tail(path: Path, n: int = 200) -> str:
    try:
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(lines[-n:])
    except Exception:
        return ""


def collect_context(report_lines: List[str]) -> str:
    """Collect context from report, cli.log and logdb events."""
    home = Path.home()
    cli_log = home / ".dockvirt" / "cli.log"
    events = home / ".dockvirt" / "logdb" / "events.jsonl"
    ctx = []
    ctx.append("# Agent report tail\n" + "\n".join(report_lines[-200:]))
    t1 = _tail(cli_log, 200)
    if t1:
        ctx.append("# cli.log tail\n" + t1)
    t2 = _tail(events, 200)
    if t2:
        ctx.append("# events.jsonl tail\n" + t2)
    ctx.append(f"LIBVIRT_DEFAULT_URI={os.environ.get('LIBVIRT_DEFAULT_URI', DEFAULT_LIBVIRT_URI)}")
    return "\n\n".join(ctx)


ALLOWED_PREFIXES = (
    "sudo virsh net-define ",
    "sudo virsh net-start default",
    "sudo virsh net-autostart default",
    "sudo systemctl enable --now libvirtd",
    "sudo setfacl ",
    "sudo semanage fcontext ",
    "sudo restorecon -Rv ",
    "sudo chown -R $USER:$USER ",
)


def apply_llm_suggestions(context: str, verbose: bool) -> List[str]:
    """Query local LLM and apply only whitelisted, non-destructive suggestions."""
    if not llm_available():
        return []
    cmds = suggest_fixes(context)
    if not cmds:
        return []
    applied: List[str] = []
    for c in cmds:
        if any(c.startswith(pfx) for pfx in ALLOWED_PREFIXES):
            rc, out, err = run(c, echo=verbose)
            ok = rc == 0
            applied.append(f"{'✅' if ok else '❌'} {c}")
            log_event("agent.llm.apply", {"cmd": c, "rc": str(rc)})
        else:
            applied.append(f"⏭️ skipped (not in whitelist): {c}")
    return applied


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
@click.option("--verbose", is_flag=True, help="Print progress and command outputs while running")
def run_agent(auto_fix: bool, auto_hosts: bool, skip_host_build: bool, os_list: List[str],
              example_names: List[str], report_file: str, verbose: bool):
    """Run the Dockvirt automation agent."""
    report_lines: List[str] = []
    report_lines.append("# Dockvirt Automation Agent Report")
    report_lines.append("")

    # Environment info
    py = sys.executable
    report_lines.append(f"Python: {py}")
    report_lines.append(f"LIBVIRT_DEFAULT_URI: {os.environ.get('LIBVIRT_DEFAULT_URI', DEFAULT_LIBVIRT_URI)}")
    log_event("agent.start", {"auto_fix": str(auto_fix), "auto_hosts": str(auto_hosts)})

    # Doctor
    if auto_fix:
        report_lines.append("\n## Doctor (auto-fix)")
        click.echo("[agent] Running doctor --fix --yes...")
        run(f"{py} scripts/doctor.py --fix --yes", echo=verbose)
        # Fix ownership early to prevent cloud-localds write errors
        report_lines.extend(f"- {n}" for n in fix_ownership(Path.home(), verbose=verbose))
        click.echo("[agent] Ensuring default libvirt network...")
        ensure_libvirt_default_network(verbose=verbose)
        click.echo("[agent] Applying ACL/SELinux fixes (if needed)...")
        fix_acl_selinux(Path.home(), verbose=verbose)
    else:
        report_lines.append("\n## Doctor (summary)")
        click.echo("[agent] Running doctor (summary)...")
        run(f"{py} scripts/doctor.py --summary", echo=verbose)
        click.echo("[agent] Ensuring default libvirt network...")
        ensure_libvirt_default_network(verbose=verbose)

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
            click.echo(f"[agent] Example {ex.name} -> OS {os_variant}: starting up...")
            # Pre-teardown to avoid leftover locks from previous interrupted runs
            run(f"{py} -m dockvirt.cli down --name {vm_name}", echo=verbose)
            # Skip host build if requested
            if not skip_host_build and (ex / "Dockerfile").exists() and shutil.which("docker"):
                run("docker build -t %s ." % image, cwd=ex, echo=verbose)

            # Up
            cmd_up = (
                f"{py} -m dockvirt.cli up --name {vm_name} --domain {domain} "
                f"--image {image} --port {port} --os {os_variant}"
            )
            rc, out, err = run(cmd_up, cwd=ex, echo=verbose)
            if rc != 0:
                # Prefer stderr, fall back to stdout, and include cli.log tail for context
                msg = (err or "").strip() or (out or "").strip() or "(no output)"
                report_lines.append(f"- ❌ up failed: {msg}")
                # Attach cli.log tail if available
                cli_log = Path.home() / ".dockvirt" / "cli.log"
                tail = _tail(cli_log, 120)
                if tail:
                    report_lines.append("  - cli.log tail:\n```text\n" + tail + "\n```")
                click.echo(f"[agent] up failed for {vm_name}")
                log_event("vm.up.error", {"name": vm_name, "error": msg})
                continue
            report_lines.append("- ✅ up succeeded")
            click.echo(f"[agent] up succeeded for {vm_name}")
            log_event("vm.up.success", {"name": vm_name})

            # Wait and get IP
            ip = ""
            for _ in range(45):
                time.sleep(2)
                ip = get_vm_ip(vm_name)
                if ip:
                    break
            if not ip:
                report_lines.append("- ❌ No IP (domifaddr/leases) after 90s")
                click.echo(f"[agent] Tearing down {vm_name}...")
                run(f"{py} -m dockvirt.cli down --name {vm_name}", echo=verbose)
                ctx = collect_context(report_lines)
                llm_notes = apply_llm_suggestions(ctx, verbose=verbose)
                if llm_notes:
                    report_lines.append("\n## LLM remediation")
                    report_lines.extend(f"- {n}" for n in llm_notes)
                continue
            report_lines.append(f"- 🌐 IP: {ip}")

            # Start health check worker
            health_queue = Queue()
            health_report = HealthReport(vm_name, domain, ip, str(port))
            health_thread = threading.Thread(
                target=health_check_worker, args=(health_queue, health_report, 60)
            )
            health_thread.daemon = True
            health_thread.start()

            # HTTP by IP
            ip_url = f"http://{ip}/" if port == "80" else f"http://{ip}:{port}/"
            ok_ip, code_ip = wait_http(ip_url, seconds=120, interval=5, host=domain)
            if ok_ip:
                report_lines.append(f"- ✅ HTTP by IP OK: {ip_url}")
            else:
                report_lines.append(f"- ⚠️ HTTP by IP failed ({code_ip}): {ip_url}")

            # Domain resolve
            rc, dns_out, _ = run(f"getent hosts {domain}", echo=verbose)
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
            ok_dom, code_dom = wait_http(dom_url, seconds=120, interval=5)
            if ok_dom:
                report_lines.append(f"- ✅ HTTP via domain OK: {dom_url}")
            else:
                report_lines.append(f"- ⚠️ HTTP via domain failed ({code_dom}): {dom_url}")

            # Stop health check worker and tear down
            health_queue.put("stop")
            health_thread.join(timeout=5)

            # Down
            run(f"{py} -m dockvirt.cli down --name {vm_name}")

    # Write report
    # Optional: LLM remediation pass
    ctx = collect_context(report_lines)
    llm_notes = apply_llm_suggestions(ctx, verbose=verbose)
    if llm_notes:
        report_lines.append("\n## LLM remediation")
        report_lines.extend(f"- {n}" for n in llm_notes)
    Path(report_file).write_text("\n".join(report_lines), encoding="utf-8")
    click.echo(f"Report saved to {report_file}")


if __name__ == "__main__":
    cli()
