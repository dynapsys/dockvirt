"""
Structured event logging for Dockvirt self-healing.

Writes JSONL entries to ~/.dockvirt/logdb/events.jsonl so that automation and
LLM-based helpers can reason about past failures and attempted fixes.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".dockvirt"
LOGDB_DIR = CONFIG_DIR / "logdb"
EVENTS_FILE = LOGDB_DIR / "events.jsonl"


def append_event(event_type: str, data: Dict[str, Any]) -> None:
    LOGDB_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": int(time.time()),
        "type": event_type,
        "data": data,
    }
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
