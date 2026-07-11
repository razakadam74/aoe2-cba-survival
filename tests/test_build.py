"""Build output (mod folder + info.json) sanity (issue #5)."""
from __future__ import annotations

import json

from cba_survival.builder import build_mod


def test_build_mod_creates_folder_and_info(tmp_path, config):
    mod_folder = build_mod(config, tmp_path)
    assert mod_folder.is_dir()

    scenario = mod_folder / "resources" / "_common" / "scenario" / f"{config.balance.mod.title}.aoe2scenario"
    assert scenario.exists() and scenario.stat().st_size > 0

    info_path = mod_folder / "info.json"
    assert info_path.exists()
    info = json.loads(info_path.read_text(encoding="utf-8"))
    assert info["Title"] == config.balance.mod.title
    assert info["Author"] == config.balance.mod.author
    assert "CacheStatus" in info
