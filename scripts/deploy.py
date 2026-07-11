#!/usr/bin/env python
"""Copy the built mod into your local AoE2 DE mods folder.

    python scripts/deploy.py                 # auto-detect the game profile(s)
    python scripts/deploy.py --dest "<path>" # deploy to a specific mods/local dir
    python scripts/deploy.py --dry-run       # show what would happen
    set AOE2_MODS_DIR=<path>                  # override auto-detection

Local mods folder looks like:
    C:\\Users\\<you>\\Games\\Age of Empires 2 DE\\<SteamID>\\mods\\local\\
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cba_survival.config import load_config  # noqa: E402


def find_local_mods_dirs() -> list[Path]:
    """Discover ``.../Age of Empires 2 DE/<id>/mods/local`` directories."""
    override = os.environ.get("AOE2_MODS_DIR")
    if override:
        return [Path(override)]

    base = Path.home() / "Games" / "Age of Empires 2 DE"
    if not base.exists():
        return []
    found: list[Path] = []
    for profile in sorted(base.iterdir()):
        if profile.is_dir() and (profile / "mods").exists():
            found.append(profile / "mods" / "local")
    return found


def deploy(source: Path, dest_local: Path, dry_run: bool) -> None:
    target = dest_local / source.name
    print(f"  {source}  ->  {target}")
    if dry_run:
        return
    dest_local.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy the CBA Survival mod locally.")
    parser.add_argument("--dest", help="Explicit .../mods/local directory to deploy into.")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without copying.")
    args = parser.parse_args()

    title = load_config(ROOT / "config").balance.mod.title
    source = ROOT / "mod" / title
    if not source.exists():
        print(f"Mod not built yet: {source}\nRun: python scripts/build.py", file=sys.stderr)
        return 1

    if args.dest:
        destinations = [Path(args.dest)]
    else:
        destinations = find_local_mods_dirs()

    if not destinations:
        print(
            "Could not find a local AoE2 DE mods folder.\n"
            "Pass one with --dest or set AOE2_MODS_DIR.",
            file=sys.stderr,
        )
        return 1

    print("Deploying:" if not args.dry_run else "Dry run (no files copied):")
    for dest_local in destinations:
        deploy(source, dest_local, args.dry_run)
    print("Enable it in-game under Mods > Local, then load the scenario.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
