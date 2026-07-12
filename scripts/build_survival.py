#!/usr/bin/env python
"""Build the 7v1 survival mod on top of a local CBA base scenario.

    python scripts/build_survival.py [path-to-base.aoe2scenario]

Defaults to base/cba6x_2026_1_team.aoe2scenario (git-ignored, local only).
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cba_survival.survival import build_survival_mod  # noqa: E402

DEFAULT_BASE = ROOT / "base" / "cba_requiem_v292.aoe2scenario"


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BASE
    if not base.exists():
        print(f"Base scenario not found: {base}", file=sys.stderr)
        print("Put a CBA base .aoe2scenario at base/ or pass its path.", file=sys.stderr)
        return 1
    mod_folder = build_survival_mod(base, ROOT / "mod")
    scenario = next((mod_folder / "resources" / "_common" / "scenario").glob("*.aoe2scenario"))
    print(f"Built survival mod: {mod_folder}")
    print(f"Scenario: {scenario} ({scenario.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
