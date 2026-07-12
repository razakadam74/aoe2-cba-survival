"""Place castles, production, army, villagers, and the enemy fortress.

Returns the per-player Castle reference ids so callers (and future co-op work)
can reason about elimination/win checks. The win/lose triggers themselves
count Castles by object type, so building forward Castles never breaks them.
"""
from __future__ import annotations

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from .config import ModConfig
from .datasets import CASTLE_ID, HOUSE_ID, VILLAGER_ID, resolve_building_id
from .layout import Layout
from .players import enemy_player_id

_GRASS_TERRAIN_ID = 0


def configure_map(scenario: AoE2DEScenario, map_size: int) -> None:
    """Resize to a flat square grass arena."""
    manager = scenario.map_manager
    manager.map_size = map_size
    for tile in manager.terrain:
        tile.terrain_id = _GRASS_TERRAIN_ID


def place_all(scenario: AoE2DEScenario, config: ModConfig, layout: Layout) -> dict[int, list[int]]:
    """Place every starting object. Returns ``{player_id: [castle_ref_ids]}``."""
    units = scenario.unit_manager
    balance = config.balance
    castle_refs: dict[int, list[int]] = {}
    enemy_id = enemy_player_id(balance)

    for base in layout.defenders:
        refs: list[int] = []
        for x, y in base.castles:
            castle = units.add_unit(player=base.player_id, unit_const=CASTLE_ID, x=x, y=y)
            refs.append(castle.reference_id)
        castle_refs[base.player_id] = refs

        for name, (x, y) in zip(balance.production_buildings, base.production):
            units.add_unit(player=base.player_id, unit_const=resolve_building_id(name), x=x, y=y)

        for x, y in base.houses:
            units.add_unit(player=base.player_id, unit_const=HOUSE_ID, x=x, y=y)

        for x, y in base.villagers:
            units.add_unit(player=base.player_id, unit_const=VILLAGER_ID, x=x + 0.5, y=y + 0.5)

        _place_army(units, base.player_id, balance, base.army)

    enemy_refs: list[int] = []
    for x, y in layout.enemy.castles:
        castle = units.add_unit(player=enemy_id, unit_const=CASTLE_ID, x=x, y=y)
        enemy_refs.append(castle.reference_id)
    castle_refs[enemy_id] = enemy_refs

    return castle_refs


def _place_army(units, player_id: int, balance, positions: tuple[tuple[int, int], ...]) -> None:
    index = 0
    for stack in balance.starting_army:
        for _ in range(stack.count):
            x, y = positions[index]
            index += 1
            units.add_unit(player=player_id, unit_const=stack.unit_id, x=x + 0.5, y=y + 0.5)


__all__ = ["configure_map", "place_all"]
