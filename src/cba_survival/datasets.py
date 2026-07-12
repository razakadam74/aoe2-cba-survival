"""Dataset lookups: resolve human-readable config names to game object ids.

All ids come straight from AoE2ScenarioParser's datasets, so we never hardcode
raw numbers in config. Names are the dataset enum member names, e.g.
``MAN_AT_ARMS``, ``CROSSBOWMAN``, ``SIEGE_WORKSHOP``.
"""
from __future__ import annotations

from AoE2ScenarioParser.datasets.buildings import BuildingInfo
from AoE2ScenarioParser.datasets.object_support import StartingAge
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.trigger_lists import (
    Attribute,
    ButtonLocation,
    DiplomacyState,
    Operation,
    PanelLocation,
    VictoryCondition,
)
from AoE2ScenarioParser.datasets.units import UnitInfo


class ConfigError(ValueError):
    """Raised when config data is missing, malformed, or references unknown ids."""


# Frequently used object ids, resolved once.
CASTLE_ID: int = BuildingInfo.CASTLE.ID
HOUSE_ID: int = BuildingInfo.HOUSE.ID
VILLAGER_ID: int = UnitInfo.VILLAGER_MALE.ID

# Global victory: CUSTOM means only our triggers decide winners (raze to win),
# not standard/conquest/wonder/score routes.
VICTORY_CUSTOM = VictoryCondition.CUSTOM

# Resource ids used by change_object_cost / modify_resource (0=food..3=gold).
RESOURCE_IDS: dict[str, int] = {
    "food": Attribute.FOOD_STORAGE.value,
    "wood": Attribute.WOOD_STORAGE.value,
    "stone": Attribute.STONE_STORAGE.value,
    "gold": Attribute.GOLD_STORAGE.value,
}


def resolve_object_id(name: str) -> int:
    """Resolve a unit OR building name to its game id (units win ties)."""
    key = _norm(name)
    if key in UnitInfo.__members__:
        return UnitInfo[key].ID
    if key in BuildingInfo.__members__:
        return BuildingInfo[key].ID
    raise ConfigError(f"Unknown unit/building name: {name!r}")


def resolve_building_id(name: str) -> int:
    """Resolve a building name to its game id (rejects non-buildings)."""
    key = _norm(name)
    if key in BuildingInfo.__members__:
        return BuildingInfo[key].ID
    raise ConfigError(f"Unknown building name: {name!r}")


def resolve_starting_age(name: str) -> StartingAge:
    """Resolve a starting-age name (e.g. IMPERIAL_AGE) to its enum member."""
    key = _norm(name)
    if key in StartingAge.__members__:
        return StartingAge[key]
    valid = ", ".join(StartingAge.__members__)
    raise ConfigError(f"Unknown starting_age {name!r}; expected one of: {valid}")


def _norm(name: str) -> str:
    if not isinstance(name, str):
        raise ConfigError(f"Expected a name string, got {name!r}")
    return name.strip().upper()


__all__ = [
    "Attribute",
    "ButtonLocation",
    "CASTLE_ID",
    "ConfigError",
    "DiplomacyState",
    "HOUSE_ID",
    "Operation",
    "PanelLocation",
    "PlayerId",
    "RESOURCE_IDS",
    "StartingAge",
    "VICTORY_CUSTOM",
    "VictoryCondition",
    "VILLAGER_ID",
    "resolve_building_id",
    "resolve_object_id",
    "resolve_starting_age",
]
