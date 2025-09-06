#!/usr/bin/env python3
"""
Dockvirt SDLC Orchestrator

Runs common lifecycle stages:
- doctor: diagnose or fix
- lint: style checks
- tests: command tests, e2e, examples
- build: package build

Usage examples:
  python scripts/sdlc.py quick
  python scripts/sdlc.py full --fix --skip-host-build
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(cmd: str, cwd: Path | None = None) -> int:
    print(f"$ {cmd}")
    p = subprocess.run(cmd, shell=True, cwd=str(cwd) if cwd else None)
    return p.returncode


def doctor(fix: bool = False) -> bool:
    args = "--fix --yes" if fix else "--summary"
    return run(f"{PY} scripts/doctor.py {args}", cwd=REPO) == 0


def lint() -> bool:
    ok1 = run("flake8", cwd=REPO) == 0
    ok2 = run("ruff check .", cwd=REPO) == 0
    return ok1 and ok2


def tests(skip_host_build: bool = True, only_quick: bool = False) -> bool:
    ok = True
    # Commands from docs
    ok = ok and (run("make test-commands", cwd=REPO) == 0)
    if only_quick:
        return ok
    # e2e
    ok = ok and (run(f"{PY} -m pytest -v -s tests/test_e2e.py", cwd=REPO) == 0)
    # examples
    env = "SKIP_HOST_BUILD=1 " if skip_host_build else ""
    ok = ok and (run(env + f"{PY} scripts/test_examples.py", cwd=REPO) == 0)
    return ok


def build_pkg() -> bool:
    return run("python -m build", cwd=REPO) == 0


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: scripts/sdlc.py [quick|full] [--fix] [--skip-host-build]")
        return 2
    mode = argv[1]
    fix = "--fix" in argv
    skip_host_build = "--skip-host-build" in argv

    if mode == "quick":
        ok = doctor(False) and tests(only_quick=True)
        return 0 if ok else 1
    if mode == "full":
        ok = doctor(fix) and lint() and tests(skip_host_build=skip_host_build) and build_pkg()
        return 0 if ok else 1

    print("Unknown mode. Use quick or full.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
