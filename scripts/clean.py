#!/usr/bin/env python
"""Remove built mod output under mod/ (keeps mod/README.md).

    python scripts/clean.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_DIR = ROOT / "mod"


def main() -> int:
    if not MOD_DIR.exists():
        print("Nothing to clean.")
        return 0
    removed = 0
    for child in MOD_DIR.iterdir():
        if child.name == "README.md":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        removed += 1
    print(f"Removed {removed} item(s) from {MOD_DIR}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
