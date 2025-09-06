#!/usr/bin/env python3
"""
Fix permissions for ~/.dockvirt when using system libvirt (qemu:///system).

By default, libvirt VMs may run as the 'qemu' user, which needs traversal and
read/write access to certain files under your home directory.

Usage:
  python scripts/fix_permissions.py --apply      # apply ACL + SELinux (if available)
  python scripts/fix_permissions.py --dry-run    # print what would be executed
"""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from typing import List

HOME = Path.home()
BASE = HOME / ".dockvirt"


def run(cmd: str, dry: bool) -> None:
    print(f"$ {cmd}")
    if not dry:
        subprocess.run(cmd, shell=True, check=False)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="apply changes with sudo")
    p.add_argument("--dry-run", action="store_true", help="print commands only")
    args = p.parse_args()

    dry = args.dry_run or not args.apply

    if not BASE.exists():
        print(f"Directory {BASE} does not exist yet. Nothing to fix.")
        return 0

    print("# Fix ownership (optional)")
    run(f"sudo chown -R $USER:$USER '{BASE}' || true", dry)

    print("\n# ACLs for qemu user")
    run(f"sudo setfacl -m u:qemu:x '{HOME}'", dry)
    run(f"sudo setfacl -R -m u:qemu:rx '{BASE}'", dry)
    run(
        f"sudo find '{BASE}' -type f -name '*.qcow2' -exec setfacl -m u:qemu:rw {{}} +",
        dry,
    )
    run(
        f"sudo find '{BASE}' -type f -name '*.iso' -exec setfacl -m u:qemu:r {{}} +",
        dry,
    )

    print("\n# SELinux labels (if SELinux is enabled)")
    run(
        f"sudo semanage fcontext -a -t svirt_image_t '{BASE}(/.*)?\\.qcow2' || true",
        dry,
    )
    run(
        f"sudo semanage fcontext -a -t svirt_image_t '{BASE}(/.*)?\\.iso' || true",
        dry,
    )
    run(f"sudo restorecon -Rv '{BASE}' || true", dry)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
