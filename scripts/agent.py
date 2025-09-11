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
import socket
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from queue import Queue, Empty
from datetime import datetime
import click
import json
import base64

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
    """Periodically checks VM health and logs to a report with advanced diagnostics."""
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

        # Advanced DNS diagnostics
        rc, dns_out, dns_err = run(f"getent hosts {report.domain}")
        report.add(
            f"Domain: {report.domain} ({'Resolves' if rc == 0 else 'Not Resolving'})"
        )
        if rc == 0 and dns_out.strip():
            report.add(f"DNS Output: {dns_out.strip()}")
        else:
            report.add(f"DNS Error: {dns_err.strip() if dns_err else 'No error output'}")

        # Ping test for basic network connectivity
        ping_rc, ping_out, ping_err = run(f"ping -c 4 {report.ip}")
        if ping_rc == 0:
            report.add(f"Ping to {report.ip}: Successful")
            report.add(f"Ping Output: {ping_out.strip()}")
        else:
            report.add(f"Ping to {report.ip}: Failed")
            report.add(f"Ping Error: {ping_err.strip() if ping_err else 'No error output'}")

        # TCP reachability checks (IP and domain)
        try:
            p = int(report.port)
        except Exception:
            p = 80
        ok_tcp_ip, err_tcp_ip = tcp_check(report.ip, p, timeout=3)
        if ok_tcp_ip:
            report.add(f"TCP: {report.ip}:{p} reachable")
        else:
            report.add(f"TCP: {report.ip}:{p} NOT reachable ({err_tcp_ip})")

        ok_tcp_dom, err_tcp_dom = tcp_check(report.domain, p, timeout=3)
        if ok_tcp_dom:
            report.add(f"TCP: {report.domain}:{p} reachable")
        else:
            report.add(f"TCP: {report.domain}:{p} NOT reachable ({err_tcp_dom})")

        # HTTP check with content retrieval
        http_url = f"http://{report.ip}:{report.port}/"
        header = f"-H 'Host: {report.domain}'" if report.domain else ""
        curl_cmd = f"curl -sS -L --connect-timeout 5 --max-time 10 {header} {http_url} -o /tmp/curl_output -w '%{{http_code}}'"
        curl_rc, curl_out, curl_err = run(curl_cmd)
        if curl_rc == 0:
            try:
                code = int(curl_out.strip())
                ok = code == 200
                report.add(f"HTTP: {http_url} -> {code} ({'OK' if ok else 'Failed'})")
                # Retrieve content from temporary file
                content_rc, content_out, _ = run("cat /tmp/curl_output")
                if content_rc == 0 and content_out.strip():
                    report.add(f"HTTP Content (first 200 chars): {content_out[:200]}...")
                else:
                    report.add("HTTP Content: Empty or not retrieved")
            except ValueError:
                report.add(f"HTTP: {http_url} -> Invalid response code ({curl_out.strip()})")
                report.add(f"HTTP Error: {curl_err.strip() if curl_err else 'No error output'}")
        else:
            report.add(f"HTTP: {http_url} -> 0 (Failed)")
            report.add(f"HTTP Error: {curl_err.strip() if curl_err else 'No error output'}")

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


def ensure_libvirt_default_network(auto_fix: bool = False, verbose: bool = False) -> List[str]:
    """Ensure the libvirt default network is active.

    In summary mode (auto_fix=False), do not run sudo commands; just report
    the situation and provide guidance.
    """
    notes: List[str] = []
    rc, out, err = run("virsh --connect qemu:///system net-info default", echo=verbose)
    if rc != 0:
        notes.append("libvirt default network not found")
        if auto_fix:
            notes.append("attempting define/start/autostart of default network")
            run("sudo systemctl enable --now libvirtd", echo=verbose)
            run("sudo virsh net-define /usr/share/libvirt/networks/default.xml || true", echo=verbose)
            run("sudo virsh net-start default || true", echo=verbose)
            run("sudo virsh net-autostart default || true", echo=verbose)
        else:
            notes.append("summary mode: no sudo changes; run 'make agent-fix' or start libvirtd and default network manually")
    else:
        if "Active: yes" not in out:
            notes.append("libvirt default network present but inactive")
            if auto_fix:
                run("sudo virsh net-start default || true", echo=verbose)
                run("sudo virsh net-autostart default || true", echo=verbose)
            else:
                notes.append("summary mode: not starting network; run 'make agent-fix' to auto-fix")
        else:
            notes.append("libvirt default network active")
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
        notes = ensure_libvirt_default_network(auto_fix=True, verbose=verbose)
        report_lines.extend(f"- {n}" for n in notes)
        click.echo("[agent] Applying ACL/SELinux fixes (if needed)...")
        report_lines.extend(f"- {n}" for n in fix_acl_selinux(Path.home(), verbose=verbose))
    else:
        report_lines.append("\n## Doctor (summary)")
        click.echo("[agent] Running doctor (summary)...")
        run(f"{py} scripts/doctor.py --summary", echo=verbose)
        click.echo("[agent] Ensuring default libvirt network...")
        notes = ensure_libvirt_default_network(auto_fix=False, verbose=verbose)
        report_lines.extend(f"- {n}" for n in notes)

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

            # Ensure default network is active before starting VM
            click.echo(f"[agent] Ensuring default libvirt network is active before starting {vm_name}...")
            ensure_libvirt_default_network(auto_fix=auto_fix, verbose=verbose)

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
            # Add a longer delay to allow services in the VM to start
            time.sleep(60)  # Wait for 60 seconds before starting health checks
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

            # Try to fetch deploy logs from inside the VM for diagnostics (via QGA)
            vm_logs = _fetch_vm_logs(vm_name, os_variant)
            for path, content in vm_logs:
                lines = content.splitlines()
                tail = "\n".join(lines[-200:])
                report_lines.append(f"  - VM log tail: {path}\n```text\n{tail}\n```")

            # VM live diagnostics via QGA (while VM is up)
            vm_diag_sections = _collect_vm_diagnostics(vm_name, os_variant, service_name=vm_name, vm_ip=ip)
            for title, output in vm_diag_sections:
                if output and output.strip():
                    report_lines.append(f"  - VM diag: {title}\n```text\n{output.strip()}\n```")

            # Host-side network diagnostics (while VM is still up)
            host_diags = _host_network_diagnostics(vm_name, ip, domain)
            for title, output in host_diags:
                if output and output.strip():
                    report_lines.append(f"  - Host diag: {title}\n```text\n{output.strip()}\n```")

            # Root-cause checklist using collected diagnostics
            ping_rc, _, _ = run(f"ping -c 2 {ip}")
            ping_ok = ping_rc == 0
            try:
                p_int = int(port)
            except Exception:
                p_int = 80
            tcp_ok, _ = tcp_check(ip, p_int, timeout=3)
            http_ip_ok = ok_ip
            http_ip_code = code_ip
            _, dns_out_chk, _ = run(f"getent hosts {domain}")
            domain_maps_to_ip = (ip in (dns_out_chk or ""))
            checklist = _render_root_cause_checklist(
                vm_name=vm_name,
                vm_ip=ip,
                domain=domain,
                service_name=vm_name,
                ping_ok=ping_ok,
                tcp80_ok=tcp_ok,
                http_ip_ok=http_ip_ok,
                http_ip_code=http_ip_code,
                domain_maps_to_ip=domain_maps_to_ip,
                diag_sections=vm_diag_sections,
            )
            report_lines.append(checklist)

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


def tcp_check(host: str, port: int, timeout: int = 3) -> Tuple[bool, str]:
    """Attempt a TCP connection to host:port, return (ok, error)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, ""
    except Exception as e:
        return False, str(e)


def _qga_cmd(vm_name: str, payload: dict, timeout: int = 5) -> Tuple[bool, dict | str]:
    """Execute a QEMU guest agent command via virsh qemu-agent-command.

    Returns (ok, data) where data is parsed JSON on success or stderr string on failure.
    """
    p_json = json.dumps(payload)
    rc, out, err = run(
        f"virsh --connect qemu:///system qemu-agent-command {vm_name} '{p_json}' --timeout {timeout}",
        echo=False,
    )
    if rc != 0:
        return False, err.strip()
    try:
        return True, json.loads(out.strip())
    except Exception as e:
        return False, f"parse_error: {e} | raw={out.strip()}"


def _qga_file_read(vm_name: str, path: str, chunk: int = 32768) -> str:
    """Read a file from inside the VM using qemu-guest-agent file APIs."""
    ok, resp = _qga_cmd(vm_name, {"execute": "guest-file-open", "arguments": {"path": path, "mode": "r"}})
    if not ok or not isinstance(resp, dict) or "return" not in resp:
        return ""
    handle = resp["return"]
    buf: list[str] = []
    try:
        while True:
            ok, resp = _qga_cmd(vm_name, {"execute": "guest-file-read", "arguments": {"handle": handle, "count": chunk}})
            if not ok or not isinstance(resp, dict) or "return" not in resp:
                break
            r = resp["return"]
            data_b64 = r.get("buf-b64", "")
            if data_b64:
                try:
                    buf.append(base64.b64decode(data_b64).decode("utf-8", errors="replace"))
                except Exception:
                    pass
            if r.get("eof"):
                break
    finally:
        _qga_cmd(vm_name, {"execute": "guest-file-close", "arguments": {"handle": handle}})
    return "".join(buf)


def _fetch_vm_logs(vm_name: str, os_variant: str) -> List[Tuple[str, str]]:
    """Try to fetch useful logs from inside the VM via qemu-guest-agent.

    Returns list of (path, content) that were successfully read.
    """
    user = "ubuntu" if "ubuntu" in os_variant else ("fedora" if "fedora" in os_variant else "ubuntu")
    candidates = [f"/home/{user}/deploy.log", "/var/log/cloud-init-output.log"]
    out: List[Tuple[str, str]] = []
    for p in candidates:
        try:
            data = _qga_file_read(vm_name, p)
            if data:
                out.append((p, data))
        except Exception:
            continue
    return out


def _collect_vm_diagnostics(vm_name: str, os_variant: str, service_name: str, vm_ip: str) -> List[Tuple[str, str]]:
    """Collect useful runtime diagnostics from inside the VM via QGA."""
    user = "ubuntu" if "ubuntu" in os_variant else ("fedora" if "fedora" in os_variant else "ubuntu")
    cmds: List[Tuple[str, str]] = [
        ("basic", "uname -a; echo; uptime; echo; whoami"),
        ("network", "ip addr; echo; ip route; echo; (ss -ltnp || netstat -ltnp || true)"),
        ("systemd: docker", "systemctl is-active docker; echo; systemctl status docker --no-pager -l | tail -n 120 || true"),
        ("systemd: qemu-guest-agent", "systemctl is-active qemu-guest-agent; echo; systemctl status qemu-guest-agent --no-pager -l | tail -n 120 || true"),
        ("cloud-init status", "(cloud-init status || true) && echo && (journalctl -u cloud-init -n 80 --no-pager || true)"),
        ("docker ps", "docker ps -a --format '{{.ID}}  {{.Names}}  {{.Status}}  {{.Ports}}' || true"),
        ("compose ps", "(docker compose ps || docker-compose ps) || true"),
        ("caddy logs", "(docker compose logs --no-color --tail 200 reverse-proxy || docker-compose logs --no-color --tail 200 reverse-proxy) || true"),
        (f"app logs ({service_name})", f"(docker compose logs --no-color --tail 200 {service_name} || docker-compose logs --no-color --tail 200 {service_name}) || true"),
        ("http local 127.0.0.1:80", "curl -sSI --max-time 5 http://127.0.0.1:80/ || true"),
        ("http self ip:80", f"curl -sSI --max-time 5 http://{vm_ip}:80/ || true"),
        ("firewall", "(ufw status || true); echo; (firewall-cmd --state || true); echo; (iptables -S || true); echo; (iptables -t nat -S || nft list ruleset || true)"),
        ("trace to host", "(tracepath -n -m 5 192.168.122.1 || traceroute -n -m 5 192.168.122.1 || ping -c 1 192.168.122.1 || true)"),
        ("deploy.log tail", f"tail -n 200 /home/{user}/deploy.log || true"),
        ("cloud-init-output.log tail", "tail -n 200 /var/log/cloud-init-output.log || true"),
    ]
    out: List[Tuple[str, str]] = []
    for title, cmd in cmds:
        rc, o, e = _qga_exec(vm_name, cmd)
        combined = o + ("\n" + e if e else "")
        out.append((title, combined))
    return out


def _host_network_diagnostics(vm_name: str, ip: str, domain: str) -> List[Tuple[str, str]]:
    """Run host-side diagnostics to understand routing and libvirt state."""
    cmds: List[Tuple[str, str]] = [
        ("host ping -> VM", f"ping -c 4 {ip}"),
        ("host tracepath -> VM", f"(tracepath -n -m 5 {ip} || traceroute -n -m 5 {ip} || true)"),
        ("host ip/route/ports", "ip addr; echo; ip route; echo; (ss -ltnp || true)"),
        ("libvirt domiflist", f"virsh --connect qemu:///system domiflist {vm_name} || true"),
        ("libvirt leases", "virsh --connect qemu:///system net-dhcp-leases default || true"),
        ("libvirt net-info/xml", "virsh --connect qemu:///system net-info default; echo; virsh --connect qemu:///system net-dumpxml default || true"),
    ]
    res: List[Tuple[str, str]] = []
    for title, cmd in cmds:
        rc, out, err = run(cmd)
        res.append((title, (out or "") + ("\n" + err if err else "")))
    return res


def _render_root_cause_checklist(
    vm_name: str,
    vm_ip: str,
    domain: str,
    service_name: str,
    ping_ok: bool,
    tcp80_ok: bool,
    http_ip_ok: bool,
    http_ip_code: int,
    domain_maps_to_ip: bool,
    diag_sections: List[Tuple[str, str]],
) -> str:
    diag = {t: (o or "") for t, o in diag_sections}
    net_txt = diag.get("network", "")
    docker_txt = diag.get("systemd: docker", "")
    qga_txt = diag.get("systemd: qemu-guest-agent", "")
    compose_ps_txt = diag.get("compose ps", "")
    docker_ps_txt = diag.get("docker ps", "")
    caddy_logs_txt = diag.get("caddy logs", "")
    http_local_txt = diag.get("http local 127.0.0.1:80", "")
    http_self_txt = diag.get("http self ip:80", "")
    cloud_status_txt = diag.get("cloud-init status", "")

    def contains_listener_80(s: str) -> bool:
        return ":80" in s or "0.0.0.0:80" in s or "[::]:80" in s

    vm_listens_80 = contains_listener_80(net_txt)
    docker_active = docker_txt.splitlines()[0:1] and ("active" in docker_txt.splitlines()[0])
    qga_active = qga_txt.splitlines()[0:1] and ("active" in qga_txt.splitlines()[0])
    http_127_ok = "200" in http_local_txt or "HTTP/1.1 200" in http_local_txt
    http_self_ok = "200" in http_self_txt or "HTTP/1.1 200" in http_self_txt
    app_up = (service_name in compose_ps_txt and ("Up" in compose_ps_txt or "running" in compose_ps_txt)) or (service_name in docker_ps_txt and "Up" in docker_ps_txt)
    rp_up = ("reverse-proxy" in compose_ps_txt and ("Up" in compose_ps_txt or "running" in compose_ps_txt)) or ("reverse-proxy" in docker_ps_txt and "Up" in docker_ps_txt)
    cloud_done = ("status: done" in cloud_status_txt) or ("status: disabled" in cloud_status_txt) or ("finished" in cloud_status_txt.lower())

    def chk(val: Optional[bool], label: str, extra: str = "") -> str:
        mark = "✅" if val is True else ("❌" if val is False else "⚠️")
        return f"- {mark} {label}{(' - ' + extra) if extra else ''}"

    lines: List[str] = []
    lines.append("\n## Root cause checklist")
    lines.append(chk(True, f"VM has IP {vm_ip}"))
    lines.append(chk(ping_ok, "Host -> VM ping"))
    lines.append(chk(tcp80_ok, "Host -> VM TCP :80 reachable"))
    lines.append(chk(vm_listens_80 if qga_active else None, "VM listens on :80 (ss)"))
    lines.append(chk(docker_active if qga_active else None, "Docker service active in VM"))
    lines.append(chk(app_up if qga_active else None, f"App container '{service_name}' up"))
    lines.append(chk(rp_up if qga_active else None, "Reverse-proxy container up"))
    lines.append(chk(http_127_ok if qga_active else None, "HTTP 200 at 127.0.0.1:80 inside VM"))
    lines.append(chk(http_ip_ok, f"HTTP by IP from host (code {http_ip_code})"))
    lines.append(chk(domain_maps_to_ip, "Domain resolves to VM IP", extra=f"{domain} -> {vm_ip}" if domain_maps_to_ip else "mismatch"))
    lines.append(chk(qga_active, "QEMU Guest Agent active in VM"))
    lines.append(chk(cloud_done if qga_active else None, "cloud-init completed"))
    # Quick hint if common failure
    if ping_ok and not tcp80_ok:
        lines.append("  Hint: TCP refused -> serwis HTTP nie nasłuchuje w VM (sprawdź Docker/Caddy).")
    if not domain_maps_to_ip:
        lines.append("  Hint: Domenę zmapuj w /etc/hosts lub popraw DNS na IP VM.")
    return "\n".join(lines)


def _qga_exec(vm_name: str, cmd: str, timeout: int = 20) -> Tuple[int, str, str]:
    """Run a shell command inside the VM via qemu-guest-agent and capture output.

    Returns (exitcode, stdout, stderr).
    """
    ok, resp = _qga_cmd(
        vm_name,
        {
            "execute": "guest-exec",
            "arguments": {
                "path": "/bin/sh",
                "arg": ["-lc", cmd],
                "capture-output": True,
            },
        },
        timeout=timeout,
    )
    if not ok or not isinstance(resp, dict) or "return" not in resp:
        return 1, "", (resp if isinstance(resp, str) else "guest-exec failed")
    pid = resp["return"].get("pid")
    # Poll status
    waited = 0
    while waited < timeout:
        ok, st = _qga_cmd(vm_name, {"execute": "guest-exec-status", "arguments": {"pid": pid}}, timeout=timeout)
        if not ok or not isinstance(st, dict) or "return" not in st:
            break
        r = st["return"]
        if r.get("exited"):
            rc = int(r.get("exitcode", 1))
            out_b64 = r.get("out-data", "")
            err_b64 = r.get("err-data", "")
            out = base64.b64decode(out_b64).decode("utf-8", errors="replace") if out_b64 else ""
            err = base64.b64decode(err_b64).decode("utf-8", errors="replace") if err_b64 else ""
            return rc, out, err
        time.sleep(0.5)
        waited += 1
    return 124, "", "guest-exec timeout"


if __name__ == "__main__":
    cli()
