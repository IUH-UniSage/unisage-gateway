"""Secrets for the dataset tools: the environment first, else the gateway repo's .env
(git-ignored). Passwords are never written into the dataset files."""

from __future__ import annotations

import os
import re
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


def env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value and ENV_FILE.is_file():
        m = re.search(rf"^{name}=(.*)$", ENV_FILE.read_text(encoding="utf-8"), re.M)
        value = m[1].strip().strip('"').strip("'") if m else ""
    if not value:
        raise SystemExit(f"{name} is not set (environment or {ENV_FILE})")
    return value
