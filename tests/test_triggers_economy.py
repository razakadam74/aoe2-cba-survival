"""M2 economy tests: kill income + periodic reinforcements."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml
from conftest import trigger_named

from AoE2ScenarioParser.datasets.effects import EffectId

from cba_survival.builder import build_scenario
from cba_survival.config import parse_config
from cba_survival.datasets import ConfigError

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"


def _raw():
    balance = yaml.safe_load((CONFIG_DIR / "balance.yaml").read_text(encoding="utf-8"))
    waves = yaml.safe_load((CONFIG_DIR / "waves.yaml").read_text(encoding="utf-8"))
    return balance, waves


def test_kill_income_trigger_present_and_shaped(built, config):
    assert config.balance.kill_income.enabled
    trigger = trigger_named(built, "Kill income - Player 1")
    assert trigger.looping
    assert len(trigger.conditions) == 1  # poll timer
    # delta-poll: read total, subtract paid, scale by gold_per_kill, pay, remember.
    assert len(trigger.effects) == 5


def test_reinforcements_trigger_creates_squad(built, config):
    assert config.balance.reinforcements.enabled
    trigger = trigger_named(built, "Reinforcements - Player 1")
    assert trigger.looping
    total = sum(stack.count for stack in config.balance.reinforcements.units)
    creates = [e for e in trigger.effects if e.effect_type == EffectId.CREATE_OBJECT]
    assert len(creates) == total  # one per unit; players command them, no attack_move
    assert all(e.source_player == 1 for e in creates)


def test_kill_income_disabled_produces_no_triggers():
    balance, waves = _raw()
    balance = copy.deepcopy(balance)
    balance["kill_income"]["gold_per_kill"] = 0
    scenario = build_scenario(parse_config(balance, waves))
    assert not any(t.name.startswith("Kill income") for t in scenario.trigger_manager.triggers)


def test_reinforcements_disabled_produces_no_triggers():
    balance, waves = _raw()
    balance = copy.deepcopy(balance)
    balance["reinforcements"]["units"] = []
    scenario = build_scenario(parse_config(balance, waves))
    assert not any(t.name.startswith("Reinforcements") for t in scenario.trigger_manager.triggers)


def test_kill_income_poll_seconds_must_be_positive():
    balance, waves = _raw()
    balance = copy.deepcopy(balance)
    balance["kill_income"]["poll_seconds"] = 0
    with pytest.raises(ConfigError):
        parse_config(balance, waves)
