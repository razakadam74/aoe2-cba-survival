#!/usr/bin/env python
"""Build the CBA Survival mod: config/ + src/ -> mod/ output.

    python scripts/build.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cba_survival.builder import build_mod  # noqa: E402
from cba_survival.config import load_config  # noqa: E402


def main() -> int:
    config = load_config(ROOT / "config")
    mod_folder = build_mod(config, ROOT / "mod")
    scenario = mod_folder / "resources" / "_common" / "scenario" / f"{config.balance.mod.title}.aoe2scenario"
    print(f"Built mod:  {mod_folder}")
    print(f"Scenario:   {scenario} ({scenario.stat().st_size} bytes)")
    print("Next:       python scripts/deploy.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
