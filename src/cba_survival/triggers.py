"""Generate all game logic as triggers, driven by config.

Trigger set:
  * Setup (execute-on-load): villager-from-Castle + expensive cost, intro,
    and it kicks off the wave chain.
  * Wave 1..N (scripted, escalating) then an endless looping Peak wave.
  * Income (looping periodic gold) per defender.
  * Victory (raze all enemy Castles) - the only win.
  * Elimination notice per defender + Defeat (all defenders' Castles gone).

The spawner creates units at the fortress spawn box, then issues one
area-based attack-move so the freshly created units march on the defenders.
"""
from __future__ import annotations

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from .config import ModConfig, PeakWave, UnitStack, Wave
from .datasets import (
    Attribute,
    ButtonLocation,
    CASTLE_ID,
    Operation,
    PanelLocation,
    RESOURCE_IDS,
    VILLAGER_ID,
)
from .layout import Layout, spawn_positions
from .players import enemy_player_id

_MAX_UNITS_AFFECTED = 255

INTRO_MESSAGE = (
    "CBA SURVIVAL\n\n"
    "Hold your four Castles against endless escalating waves from the enemy "
    "fortress. The onslaught never stops, so the only way to win is to build "
    "an army, break out, and raze every enemy Castle. Defend and push at the "
    "same time. Good luck!"
)


def build_triggers(scenario: AoE2DEScenario, config: ModConfig, layout: Layout) -> None:
    balance = config.balance
    waves = config.waves
    manager = scenario.trigger_manager
    defender_ids = list(range(1, balance.defenders + 1))
    enemy_id = enemy_player_id(balance)

    setup = _build_setup(manager, config, defender_ids)
    _build_spawner(manager, waves, layout, setup, enemy_id)
    _build_income(manager, balance, defender_ids)
    _build_win(manager, defender_ids, enemy_id)
    _build_defeat(manager, defender_ids, enemy_id)


# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #
def _build_setup(manager, config: ModConfig, defender_ids: list[int]):
    balance = config.balance
    setup = manager.add_trigger("Setup")
    setup.enabled = True
    setup.execute_on_load = True

    for pid in defender_ids:
        # Train villagers from the Castle (no Town Center)...
        setup.new_effect.add_train_location(
            object_list_unit_id=VILLAGER_ID,
            source_player=pid,
            object_list_unit_id_2=CASTLE_ID,
            button_location=ButtonLocation.r1c1.value,
            train_time=balance.villager_train_time,
        )
        # ...and make them deliberately expensive.
        setup.new_effect.change_object_cost(
            object_list_unit_id=VILLAGER_ID,
            source_player=pid,
            resource_1=RESOURCE_IDS["food"],
            resource_1_quantity=balance.villager_cost.get("food", 0),
            resource_2=RESOURCE_IDS["gold"],
            resource_2_quantity=balance.villager_cost.get("gold", 0),
        )

    setup.new_effect.display_instructions(
        source_player=1,
        message=INTRO_MESSAGE,
        display_time=25,
        instruction_panel_position=PanelLocation.MIDDLE.value,
        string_id=-1,
        play_sound=0,
    )
    return setup


# --------------------------------------------------------------------------- #
# Endless wave spawner
# --------------------------------------------------------------------------- #
def _build_spawner(manager, waves, layout: Layout, setup, enemy_id: int) -> None:
    chain = []

    for index, wave in enumerate(waves.waves, start=1):
        trigger = manager.add_trigger(f"Wave {index}: {wave.name}")
        trigger.enabled = False  # activated by the previous link in the chain
        trigger.new_condition.timer(timer=wave.delay_seconds)
        _add_spawn(trigger, wave.units, layout, enemy_id)
        chain.append(trigger)

    peak = manager.add_trigger(f"Peak: {waves.peak.name}")
    peak.enabled = False
    peak.looping = True  # never deactivates - relentless, forever
    peak.new_condition.timer(timer=waves.peak.interval_seconds)
    _add_spawn(peak, waves.peak.units, layout, enemy_id)
    chain.append(peak)

    # Setup starts the chain; each wave activates the next; last -> endless peak.
    setup.new_effect.activate_trigger(trigger_id=chain[0].trigger_id)
    for current, following in zip(chain, chain[1:]):
        current.new_effect.activate_trigger(trigger_id=following.trigger_id)


def _add_spawn(trigger, unit_stacks: tuple[UnitStack, ...], layout: Layout, enemy_id: int) -> None:
    total = sum(stack.count for stack in unit_stacks)
    positions = spawn_positions(layout.enemy.spawn, total, layout.map_size)

    index = 0
    for stack in unit_stacks:
        for _ in range(stack.count):
            x, y = positions[index]
            index += 1
            trigger.new_effect.create_object(
                object_list_unit_id=stack.unit_id,
                source_player=enemy_id,
                location_x=x,
                location_y=y,
            )

    target_x, target_y = layout.defender_centroid
    x1, y1, x2, y2 = layout.enemy.spawn_area
    trigger.new_effect.attack_move(
        source_player=enemy_id,
        location_x=target_x,
        location_y=target_y,
        area_x1=x1,
        area_y1=y1,
        area_x2=x2,
        area_y2=y2,
        max_units_affected=_MAX_UNITS_AFFECTED,
    )


# --------------------------------------------------------------------------- #
# Economy (M1: periodic gold; kill income lands in M2)
# --------------------------------------------------------------------------- #
def _build_income(manager, balance, defender_ids: list[int]) -> None:
    amount = balance.periodic_gold["amount"]
    interval = balance.periodic_gold["interval_seconds"]
    for pid in defender_ids:
        income = manager.add_trigger(f"Income - Player {pid}")
        income.enabled = True
        income.looping = True
        income.new_condition.timer(timer=interval)
        income.new_effect.modify_resource(
            quantity=amount,
            tribute_list=RESOURCE_IDS["gold"],
            source_player=pid,
            operation=Operation.ADD.value,
        )


# --------------------------------------------------------------------------- #
# Win / lose
# --------------------------------------------------------------------------- #
def _build_win(manager, defender_ids: list[int], enemy_id: int) -> None:
    win = manager.add_trigger("Victory - enemy fortress razed")
    win.enabled = True
    win.new_condition.own_fewer_objects(quantity=1, object_list=CASTLE_ID, source_player=enemy_id)
    for pid in defender_ids:
        win.new_effect.declare_victory(source_player=pid, enabled=1)


def _build_defeat(manager, defender_ids: list[int], enemy_id: int) -> None:
    # Per-defender elimination notice (fires once when that player's Castles fall).
    for pid in defender_ids:
        notice = manager.add_trigger(f"Player {pid} eliminated")
        notice.enabled = True
        notice.new_condition.own_fewer_objects(quantity=1, object_list=CASTLE_ID, source_player=pid)
        notice.new_effect.display_instructions(
            source_player=pid,
            message=f"Player {pid} has been eliminated - their Castles have fallen.",
            display_time=12,
            instruction_panel_position=PanelLocation.MIDDLE.value,
            string_id=-1,
            play_sound=0,
        )

    # Team defeat: every defender has lost all Castles (all conditions ANDed).
    defeat = manager.add_trigger("Defeat - all defenders eliminated")
    defeat.enabled = True
    for pid in defender_ids:
        defeat.new_condition.own_fewer_objects(quantity=1, object_list=CASTLE_ID, source_player=pid)
    defeat.new_effect.declare_victory(source_player=enemy_id, enabled=1)


__all__ = ["build_triggers", "INTRO_MESSAGE"]
