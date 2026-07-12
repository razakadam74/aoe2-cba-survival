"""Shared pytest fixtures."""
from __future__ import annotations

from pathlib import Path

import pytest

from cba_survival.builder import build_scenario
from cba_survival.config import load_config
from cba_survival.players import enemy_player_id

# Belt and suspenders: importing cba_survival already disables the library's
# status prints, but make it explicit so pytest never hits the Windows emoji crash.
from AoE2ScenarioParser import settings as _settings

_settings.PRINT_STATUS_UPDATES = False

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"


@pytest.fixture(scope="session")
def config():
    return load_config(CONFIG_DIR)


@pytest.fixture(scope="session")
def built(config):
    """A fully assembled in-memory scenario (read-only in tests)."""
    return build_scenario(config)


@pytest.fixture(scope="session")
def enemy_id(config):
    return enemy_player_id(config.balance)


def trigger_named(scenario, name: str):
    for trigger in scenario.trigger_manager.triggers:
        if trigger.name == name:
            return trigger
    raise AssertionError(f"No trigger named {name!r}")


def units_of(scenario, player: int, unit_const: int):
    return [u for u in scenario.unit_manager.get_player_units(player) if u.unit_const == unit_const]
