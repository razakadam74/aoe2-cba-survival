#!/usr/bin/env python
"""Build the 7v1 survival mod on top of a local CBA base scenario.

    python scripts/build_survival.py [path-to-base.aoe2scenario] [--deploy]

Defaults to base/cba_requiem_v293_team_free.aoe2scenario (git-ignored, local only).
CBA assigns random civs in-game each play, so no build-time civ options are needed.
--deploy copies the built scenario into your AoE2 DE profile scenario folder(s).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cba_survival.survival import build_survival_mod  # noqa: E402

DEFAULT_BASE = ROOT / "base" / "cba_requiem_v293_team_free.aoe2scenario"


def find_profile_scenario_dirs() -> list[Path]:
    """Discover ``.../Age of Empires 2 DE/<id>/resources/_common/scenario`` dirs."""
    base = Path.home() / "Games" / "Age of Empires 2 DE"
    if not base.exists():
        return []
    found: list[Path] = []
    for profile in sorted(base.iterdir()):
        # Real player profiles are long numeric ids; skip helpers like 0/logs/metadata.
        if profile.is_dir() and profile.name.isdigit() and len(profile.name) >= 6 and (profile / "mods").exists():
            found.append(profile / "resources" / "_common" / "scenario")
    return found


def deploy(scenario_file: Path) -> None:
    targets = find_profile_scenario_dirs()
    if not targets:
        print("No AoE2 DE profile found to deploy into; skipping deploy.", file=sys.stderr)
        return
    for scenario_dir in targets:
        scenario_dir.mkdir(parents=True, exist_ok=True)
        dest = scenario_dir / scenario_file.name
        try:
            shutil.copy2(scenario_file, dest)
            print(f"Deployed: {dest}")
        except PermissionError:
            print(f"Permission denied writing {dest}. Close AoE2 DE and retry.", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the CBA Survival 7v1 scenario.")
    parser.add_argument("base", nargs="?", default=str(DEFAULT_BASE), help="CBA base .aoe2scenario")
    parser.add_argument("--deploy", action="store_true", help="Copy into the AoE2 DE profile scenario folder(s).")
    args = parser.parse_args()

    base = Path(args.base)
    if not base.exists():
        print(f"Base scenario not found: {base}", file=sys.stderr)
        print("Put a CBA base .aoe2scenario at base/ or pass its path.", file=sys.stderr)
        return 1

    mod_folder = build_survival_mod(base, ROOT / "mod")
    scenario = next((mod_folder / "resources" / "_common" / "scenario").glob("*.aoe2scenario"))
    print(f"Built survival mod: {mod_folder}")
    print(f"Scenario: {scenario} ({scenario.stat().st_size} bytes)")
    if args.deploy:
        deploy(scenario)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
