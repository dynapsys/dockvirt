#!/usr/bin/env python3
"""
Local LLM helper for Dockvirt self-healing.

Tries to invoke a small local model (around 3B parameters) using `ollama`.
This is optional and best-effort. If `ollama` or the model is missing, it
silently returns no suggestions.

Environment variables:
- DOCKVIRT_USE_LLM=1            # enable LLM suggestions (default off)
- DOCKVIRT_LLM_MODEL=llama3.2:3b  # preferred model; fallbacks to phi3:mini

Output format from the model is expected to be a JSON list of shell commands.
Example: ["sudo virsh net-start default", "sudo setfacl -m u:qemu:x $HOME"]
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
from typing import List
import shutil


def _run(cmd: str) -> tuple[int, str, str]:
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return p.returncode, p.stdout, p.stderr


def available() -> bool:
    if os.environ.get("DOCKVIRT_USE_LLM", "0") != "1":
        return False
    return shutil.which("ollama") is not None


def suggest_fixes(context: str, max_tokens: int = 256) -> List[str]:
    try:
        import shutil  # local import to keep import tree light
        if os.environ.get("DOCKVIRT_USE_LLM", "0") != "1":
            return []
        if shutil.which("ollama") is None:
            return []
        # Choose model
        model = os.environ.get("DOCKVIRT_LLM_MODEL", "llama3.2:3b")
        # Prompt asking for a JSON array of shell commands only
        prompt = (
            "You are a DevOps assistant. Based on the following logs/errors, "
            "propose safe, non-destructive shell commands to fix the environment. "
            "Output ONLY a JSON array of commands, nothing else.\n\n" + context
        )
        cmd = f"ollama run {shlex.quote(model)} --prompt {shlex.quote(prompt)}"
        rc, out, err = _run(cmd)
        if rc != 0:
            # Fallback model
            cmd2 = f"ollama run phi3:mini --prompt {shlex.quote(prompt)}"
            rc, out, err = _run(cmd2)
            if rc != 0:
                return []
        # Try to parse as JSON array
        out_stripped = out.strip()
        # Some models wrap JSON in code fences
        if out_stripped.startswith("```"):
            out_stripped = out_stripped.strip("`\n ")
        data = json.loads(out_stripped)
        if isinstance(data, list) and all(isinstance(x, str) for x in data):
            return data
    except Exception:
        return []
    return []
