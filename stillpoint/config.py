from __future__ import annotations
import os
from pathlib import Path

def root() -> Path:
    return Path(os.environ.get("STILLPOINT_ROOT", Path.cwd()))

def state_dir() -> Path:
    p = root() / "state"
    p.mkdir(parents=True, exist_ok=True)
    return p
