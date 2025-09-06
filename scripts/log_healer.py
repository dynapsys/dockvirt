#!/usr/bin/env python3
"""
Dockvirt Log Healer

Scans ~/.dockvirt/cli.log (or a given file) for known errors and proposes or applies fixes.

Usage:
  python scripts/log_healer.py                 # analyze and print suggestions
  python scripts/log_healer.py --apply         # attempt to apply fixes (may require sudo)
  python scripts/log_healer.py --file path.log # analyze specific log file
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

HOME = Path.home()
DEFAULT_LOG = HOME / ".dockvirt" / "cli.log"
REPO = Path(__file__).resolve().parents[1]
PY = os.environ.get("PY") or "python3"


def run(cmd: str, cwd: Path | None = None) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True, cwd=str(cwd) if cwd else None)
    return p.returncode, p.stdout, p.stderr


essentials = {
    "cloud-localds": "cloud-image-utils|cloud-utils",
    "virsh": "libvirt clients",
    "qemu-img": "qemu-img",
}


def analyze(lines: List[str]) -> List[str]:
    tips: List[str] = []
    text = "\n".join(lines)

    if re.search(r"Unknown operating system:\s*\w+", text):
        tips.append("Unknown OS variant detected. Run: dockvirt heal --apply")

    if re.search(r"Permission denied.*(cidata\.iso|\.qcow2|\.dockvirt)", text, re.I):
        tips.append("Permission denied under ~/.dockvirt. Run: scripts/fix_permissions.py --apply")

    if "cloud-localds: command not found" in text:
        tips.append("cloud-localds missing. Run: dockvirt check (doctor will propose distro-specific steps)")

    if re.search(r"virsh: command not found", text):
        tips.append("virsh missing. Run: dockvirt check -> install libvirt tools; ensure libvirtd active")

    return tips


def apply(tips: List[str]) -> None:
    for t in tips:
        if t.startswith("Unknown OS variant"):
            print("-> Applying: dockvirt heal --apply")
            run(f"{PY} -m dockvirt.cli heal --apply", cwd=REPO)
        elif t.startswith("Permission denied under ~/.dockvirt"):
            print("-> Applying: scripts/fix_permissions.py --apply")
            run(f"{PY} scripts/fix_permissions.py --apply", cwd=REPO)
        elif t.startswith("cloud-localds missing"):
            print("-> Running doctor --fix --yes")
            run(f"{PY} scripts/doctor.py --fix --yes", cwd=REPO)
        elif t.startswith("virsh missing"):
            print("-> Running doctor --fix --yes")
            run(f"{PY} scripts/doctor.py --fix --yes", cwd=REPO)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", type=str, help="log file to scan (default: ~/.dockvirt/cli.log)")
    p.add_argument("--apply", action="store_true", help="attempt to apply fixes")
    args = p.parse_args()

    log_file = Path(args.file) if args.file else DEFAULT_LOG
    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return 1

    lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    tips = analyze(lines)

    print("Dockvirt Log Healer - Findings:")
    if not tips:
        print("  No known issues detected.")
        return 0
    for t in tips:
        print(f"  - {t}")

    if args.apply:
        apply(tips)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
