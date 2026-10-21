#!/usr/bin/env python3
"""Fetch immutable, reviewed source inputs on the modern Docker host."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
lock = json.loads((ROOT / "sources.lock.json").read_text())
cache = ROOT / ".cache/sources"
cache.mkdir(parents=True, exist_ok=True)
for name, expected in lock["files"].items():
    path = cache / name
    if not path.exists():
        temporary = path.with_suffix(path.suffix + ".part")
        with urllib.request.urlopen(lock["base_url"] + name, timeout=120) as src:
            temporary.write_bytes(src.read())
        temporary.replace(path)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit("Source checksum mismatch: " + name)
    print(actual + "  " + name)
