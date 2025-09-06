#!/usr/bin/env python3
"""
repair_docs.py - Validate and auto-fix dockvirt commands across all README files.

Features:
- Scan all markdown files (README.md, examples/*/README.md, etc.)
- Extract only real CLI commands starting with 'dockvirt' (supports \\ continuations)
- Dry-run validate by appending --help where safe, using repo venv PATH first
- Auto-fix known documentation issues (when --apply):
  * os_images: -> images:
  * variant: fedora-cloud-base-38 -> variant: fedora38
  * Trim trailing ']' artifacts after dockvirt commands (e.g., 'dockvirt up]')
- Optionally write a report

Usage:
  python scripts/repair_docs.py --apply
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT = REPO_ROOT / "repair_docs_report.md"


def list_readmes(root: Path) -> List[Path]:
    files: List[Path] = []
    for pattern in ("README.md", "readme.md", "README.rst"):
        files.extend(p for p in root.rglob(pattern) if p.is_file())
    return [p for p in files if all(x not in str(p) for x in (".git", "__pycache__", "node_modules"))]


def extract_commands(md_path: Path) -> List[Tuple[str, int]]:
    """Extract dockvirt commands from fenced code blocks.
    Only lines beginning with 'dockvirt' or '$ dockvirt'. Support '\\' continuations.
    """
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    in_code = False
    buf: str | None = None
    buf_ln: int | None = None
    out: List[Tuple[str, int]] = []

    def flush():
        nonlocal buf, buf_ln
        if buf and buf_ln:
            parts = buf.strip().split()
            if len(parts) >= 2 and parts[0] == "dockvirt":
                # Skip planned features
                if parts[1] in {"stack", "exec"}:
                    pass
                else:
                    out.append((buf.strip(), buf_ln))
        buf = None
        buf_ln = None

    for ln, raw in enumerate(lines, 1):
        s = raw.strip()
        if s.startswith("```"):
            if in_code:
                flush()
            in_code = not in_code
            continue
        if s.startswith("#") or s.startswith("//"):
            continue
        if buf is not None:
            cont = s[:-1].strip() if s.endswith("\\") else s
            buf += " " + cont
            if not s.endswith("\\"):
                flush()
            continue
        if s.startswith("dockvirt") or s.startswith("$ dockvirt"):
            start = s.find("dockvirt")
            cmd = s[start:]
            if cmd.startswith("$ "):
                cmd = cmd[2:].strip()
            if cmd.endswith("\\"):
                buf = cmd[:-1].strip()
                buf_ln = ln
            else:
                parts = cmd.split()
                if len(parts) >= 2 and parts[1] not in {"stack", "exec"}:
                    out.append((cmd, ln))
    if buf is not None:
        flush()
    return out


def run_help(command: str, cwd: Path | None = None, timeout: int = 20) -> Tuple[int, str, str]:
    env = os.environ.copy()
    venv_bin = REPO_ROOT / ".venv-3.13" / "bin"
    if venv_bin.exists():
        env["PATH"] = f"{venv_bin}:{env.get('PATH','')}"
    parts = command.split()
    if "--help" not in parts and "help" not in parts:
        parts = parts + ["--help"]
    try:
        p = subprocess.run(parts, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return -1, "", str(e)


def auto_fix_content(path: Path, text: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    new = text
    # os_images -> images
    if re.search(r"^os_images:\s*$", new, flags=re.M):
        new = re.sub(r"^os_images:\s*$", "images:", new, flags=re.M)
        notes.append("os_images -> images")
    # fedora variant
    if re.search(r"variant:\s*fedora-cloud-base-38\b", new):
        new = re.sub(r"variant:\s*fedora-cloud-base-38\b", "variant: fedora38", new)
        notes.append("variant fedora-cloud-base-38 -> fedora38")
    # Trim stray trailing ']' after commands
    def _fix_bracket(m: re.Match[str]) -> str:
        notes.append("trim trailing ']' after dockvirt command")
        return m.group(1)
    new = re.sub(r"^(dockvirt[^\]\n]*?)\]\s*$", _fix_bracket, new, flags=re.M)
    return new, notes


def process_all(apply: bool, report: Path | None) -> None:
    files = list_readmes(REPO_ROOT)
    total_cmds = 0
    ok = 0
    failed = 0
    changes: Dict[str, List[str]] = {}

    # Validate
    for f in files:
        cmds = extract_commands(f)
        total_cmds += len(cmds)
        for cmd, ln in cmds:
            rc, out, err = run_help(cmd, cwd=f.parent)
            combined = (err or "") + "\n" + (out or "")
            bad = ("no such command" in combined.lower()) or ("no such option" in combined.lower())
            if rc in (0, 1, 2) and not bad:
                ok += 1
            else:
                failed += 1
    # Auto-fix docs
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        new, notes = auto_fix_content(f, text)
        if notes and new != text:
            changes[str(f.relative_to(REPO_ROOT))] = notes
            if apply:
                f.write_text(new, encoding="utf-8")

    # Report
    lines: List[str] = []
    lines.append("# Repair Docs Report")
    lines.append("")
    lines.append(f"Validated commands: {ok}/{total_cmds} OK, failed: {failed}")
    if changes:
        lines.append("\n## Changes applied:")
        for path, notes in changes.items():
            lines.append(f"- {path}:")
            for n in notes:
                lines.append(f"  - {n}")
    if report:
        report.write_text("\n".join(lines), encoding="utf-8")
    else:
        print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Apply auto-fixes to docs")
    ap.add_argument("--report", default=str(DEFAULT_REPORT), help="Where to write the report (md)")
    args = ap.parse_args()
    process_all(apply=args.apply, report=Path(args.report) if args.report else None)


if __name__ == "__main__":
    main()
