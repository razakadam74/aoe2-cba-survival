"""Regression tests for review fixes: co-op build, victory, villager cost."""
from __future__ import annotations

from pathlib import Path

import yaml

from cba_survival.builder import build_scenario
from cba_survival.config import parse_config
from cba_survival.datasets import CASTLE_ID, RESOURCE_IDS, VICTORY_CUSTOM
from cba_survival.players import enemy_player_id
from cba_survival.triggers import _cost_kwargs

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"


def _raw():
    balance = yaml.safe_load((CONFIG_DIR / "balance.yaml").read_text(encoding="utf-8"))
    waves = yaml.safe_load((CONFIG_DIR / "waves.yaml").read_text(encoding="utf-8"))
    return balance, waves


def test_two_defender_build_does_not_crash():
    # Regression guard for the co-op diplomacy bug (set_diplomacy_teams).
    balance, waves = _raw()
    balance["defenders"] = 2
    config = parse_config(balance, waves)

    scenario = build_scenario(config)  # must not raise

    assert scenario.player_manager.active_players == 3
    enemy_id = enemy_player_id(config.balance)
    assert enemy_id == 3
    for pid in (1, 2):
        castles = [u for u in scenario.unit_manager.get_player_units(pid) if u.unit_const == CASTLE_ID]
        assert len(castles) == 4
    enemy_castles = [u for u in scenario.unit_manager.get_player_units(enemy_id) if u.unit_const == CASTLE_ID]
    assert len(enemy_castles) == config.balance.enemy_castles


def test_victory_condition_is_custom(built):
    # Raze-to-win only: standard/conquest/wonder routes must be disabled.
    assert built.option_manager.victory_condition == VICTORY_CUSTOM


def test_cost_kwargs_maps_every_configured_resource():
    kwargs = _cost_kwargs({"wood": 40, "gold": 100})
    assert kwargs["resource_1"] == RESOURCE_IDS["wood"]
    assert kwargs["resource_1_quantity"] == 40
    assert kwargs["resource_2"] == RESOURCE_IDS["gold"]
    assert kwargs["resource_2_quantity"] == 100
    # canonical order (food, wood, stone, gold) regardless of dict insertion order
    reordered = _cost_kwargs({"gold": 100, "food": 5})
    assert reordered["resource_1"] == RESOURCE_IDS["food"]
    assert reordered["resource_2"] == RESOURCE_IDS["gold"]
