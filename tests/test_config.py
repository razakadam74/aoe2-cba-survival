"""Config schema validation (issue #6)."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from cba_survival.config import load_config, parse_config
from cba_survival.datasets import ConfigError

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"


def _raw():
    balance = yaml.safe_load((CONFIG_DIR / "balance.yaml").read_text(encoding="utf-8"))
    waves = yaml.safe_load((CONFIG_DIR / "waves.yaml").read_text(encoding="utf-8"))
    return balance, waves


def test_real_config_loads():
    cfg = load_config(CONFIG_DIR)
    assert cfg.balance.defenders >= 1
    assert cfg.balance.map_size >= 60
    assert cfg.waves.waves, "expected at least one scripted wave"
    assert cfg.waves.peak.units, "expected the endless peak to spawn units"
    assert cfg.balance.army_size == sum(s.count for s in cfg.balance.starting_army)


def test_names_resolve_to_ids():
    cfg = load_config(CONFIG_DIR)
    for stack in cfg.balance.starting_army:
        assert stack.unit_id > 0
    for wave in cfg.waves.waves:
        for stack in wave.units:
            assert stack.unit_id > 0


@pytest.mark.parametrize("defenders", [0, 8, -1])
def test_defender_count_bounds(defenders):
    balance, waves = _raw()
    balance["defenders"] = defenders
    with pytest.raises(ConfigError):
        parse_config(balance, waves)


def test_unknown_unit_rejected():
    balance, waves = _raw()
    balance["starting_army"] = [{"unit": "NOT_A_REAL_UNIT", "count": 2}]
    with pytest.raises(ConfigError):
        parse_config(balance, waves)


def test_unknown_building_rejected():
    balance, waves = _raw()
    balance["production_buildings"] = ["BARRACKS", "NOPE_HALL"]
    with pytest.raises(ConfigError):
        parse_config(balance, waves)


def test_unknown_age_rejected():
    balance, waves = _raw()
    balance["starting_age"] = "STONE_AGE"
    with pytest.raises(ConfigError):
        parse_config(balance, waves)


def test_negative_stipend_rejected():
    balance, waves = _raw()
    balance["stipend"]["gold"] = -50
    with pytest.raises(ConfigError):
        parse_config(balance, waves)


def test_zero_count_rejected():
    balance, waves = _raw()
    waves["waves"][0]["units"][0]["count"] = 0
    with pytest.raises(ConfigError):
        parse_config(balance, waves)


def test_missing_peak_rejected():
    balance, waves = _raw()
    waves = copy.deepcopy(waves)
    del waves["peak"]
    with pytest.raises(ConfigError):
        parse_config(balance, waves)
