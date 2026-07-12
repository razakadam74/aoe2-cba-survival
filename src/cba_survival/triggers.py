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
from .layout import Layout, castle_spawn_positions, squad_positions
from .players import enemy_player_id

_ALL_UNITS_AFFECTED = -1
_MARCH_INTERVAL = 2  # seconds; re-command enemy units so freshly spawned ones march
_ENEMY_FRONT_DY = -5  # spawn enemy units just south of their castles (toward you)
_PLAYER_FRONT_DY = 6  # spawn your castle units just in front of your castles
# Villager trains from an empty Castle button slot; r1c1 is the Unique Unit.
_VILLAGER_BUTTON = ButtonLocation.r3c5.value
_RESOURCE_ORDER = ("food", "wood", "stone", "gold")
# Per-player running total of enemy units killed (drives kill income).
_KILLS_ATTRIBUTE = Attribute.UNITS_KILLED.value

INTRO_MESSAGE = (
    "CBA SURVIVAL\n\n"
    "Hold your four Castles against endless escalating waves from the enemy "
    "fortress. The onslaught never stops, so the only way to win is to build "
    "an army, break out, and raze every enemy Castle. Defend and push at the "
    "same time. Good luck!"
)


def _cost_kwargs(cost: dict) -> dict:
    """Map a resource->quantity cost onto change_object_cost's resource_1..3 slots."""
    kwargs: dict = {}
    for slot, name in enumerate((r for r in _RESOURCE_ORDER if r in cost), start=1):
        kwargs[f"resource_{slot}"] = RESOURCE_IDS[name]
        kwargs[f"resource_{slot}_quantity"] = cost[name]
    return kwargs


def build_triggers(scenario: AoE2DEScenario, config: ModConfig, layout: Layout) -> None:
    balance = config.balance
    waves = config.waves
    manager = scenario.trigger_manager
    defender_ids = list(range(1, balance.defenders + 1))
    enemy_id = enemy_player_id(balance)

    setup = _build_setup(manager, config, defender_ids)
    _build_spawner(manager, waves, layout, setup, enemy_id)
    _build_march(manager, layout, enemy_id)
    _build_income(manager, balance, defender_ids)
    _build_kill_income(manager, balance, defender_ids)
    _build_reinforcements(manager, balance, layout, defender_ids)
    _build_player_production(manager, balance, layout, defender_ids)
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
        # Train villagers from the Castle (no Town Center), on an empty button...
        setup.new_effect.add_train_location(
            object_list_unit_id=VILLAGER_ID,
            source_player=pid,
            object_list_unit_id_2=CASTLE_ID,
            button_location=_VILLAGER_BUTTON,
            train_time=balance.villager_train_time,
        )
        # ...and make them deliberately expensive (whatever resources config sets).
        setup.new_effect.change_object_cost(
            object_list_unit_id=VILLAGER_ID,
            source_player=pid,
            **_cost_kwargs(balance.villager_cost),
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
    # Units pour out of the enemy fortress (spread across its castles). Movement is
    # handled by the separate looping March trigger - create + attack_move in one
    # trigger is unreliable (freshly created units aren't selectable yet).
    total = sum(stack.count for stack in unit_stacks)
    positions = castle_spawn_positions(layout.enemy.castles, total, layout.map_size, _ENEMY_FRONT_DY)
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


def _build_march(manager, layout: Layout, enemy_id: int) -> None:
    # Continuously send every enemy unit toward the defenders. Runs every couple of
    # seconds so units spawned from the fortress start marching within ~2s. Only
    # commands units north of the defender castles, so it never pulls attackers off
    # the base they have already reached.
    target_x, target_y = layout.defender_centroid
    size = layout.map_size
    march = manager.add_trigger("March - enemy assault")
    march.enabled = True
    march.looping = True
    march.new_condition.timer(timer=_MARCH_INTERVAL)
    march.new_effect.attack_move(
        source_player=enemy_id,
        location_x=target_x,
        location_y=target_y,
        area_x1=0,
        area_y1=min(target_y + 4, size - 1),
        area_x2=size - 1,
        area_y2=size - 1,
        max_units_affected=_ALL_UNITS_AFFECTED,
    )


def _build_player_production(manager, balance, layout: Layout, defender_ids: list[int]) -> None:
    # Classic CBA: each of your castles auto-produces units for you to command (no
    # resource cost). Set the composition (e.g. your unique unit) in config.
    prod = balance.player_production
    if not prod.enabled:
        return
    bases = {base.player_id: base for base in layout.defenders}
    per_castle = sum(stack.count for stack in prod.units)
    for pid in defender_ids:
        base = bases[pid]
        trigger = manager.add_trigger(f"Castle production - Player {pid}")
        trigger.enabled = True
        trigger.looping = True
        trigger.new_condition.timer(timer=prod.interval_seconds)
        for cx, cy in base.castles:
            spot = (cx, min(cy + _PLAYER_FRONT_DY, layout.map_size - 3))
            positions = squad_positions(spot, per_castle, layout.map_size)
            index = 0
            for stack in prod.units:
                for _ in range(stack.count):
                    x, y = positions[index]
                    index += 1
                    trigger.new_effect.create_object(
                        object_list_unit_id=stack.unit_id,
                        source_player=pid,
                        location_x=x,
                        location_y=y,
                    )


# --------------------------------------------------------------------------- #
# Economy: periodic gold (M1) + kill income + reinforcements (M2)
# --------------------------------------------------------------------------- #
def _build_income(manager, balance, defender_ids: list[int]) -> None:
    # Steady trickle of ALL configured resources so you can always build (units
    # and buildings cost food/wood/gold/stone, not just gold).
    income_cfg = balance.periodic_income
    if not income_cfg.enabled:
        return
    for pid in defender_ids:
        income = manager.add_trigger(f"Income - Player {pid}")
        income.enabled = True
        income.looping = True
        income.new_condition.timer(timer=income_cfg.interval_seconds)
        for name in _RESOURCE_ORDER:
            amount = income_cfg.resources.get(name, 0)
            if amount <= 0:
                continue
            income.new_effect.modify_resource(
                quantity=amount,
                tribute_list=RESOURCE_IDS[name],
                source_player=pid,
                operation=Operation.ADD.value,
            )


def _build_kill_income(manager, balance, defender_ids: list[int]) -> None:
    # Classic-CBA "every kill pays gold". The Accumulate Attribute condition never
    # resets, so instead we poll each defender's Units Killed stat on a timer and
    # pay for the kills gained since the previous poll (a delta), which cannot run
    # away and never touches the displayed Kills score.
    kill = balance.kill_income
    if not kill.enabled:
        return
    scratch = manager.add_variable("kill_income_scratch")
    for pid in defender_ids:
        paid = manager.add_variable(f"kills_paid_p{pid}")
        trigger = manager.add_trigger(f"Kill income - Player {pid}")
        trigger.enabled = True
        trigger.looping = True
        trigger.new_condition.timer(timer=kill.poll_seconds)
        # scratch = this player's total Units Killed so far
        trigger.new_effect.modify_variable_by_resource(
            tribute_list=_KILLS_ATTRIBUTE, source_player=pid,
            operation=Operation.SET.value, variable=scratch.variable_id,
        )
        # scratch = kills since we last paid (the new delta)
        trigger.new_effect.modify_variable_by_variable(
            variable=scratch.variable_id, operation=Operation.SUBTRACT.value, variable2=paid.variable_id,
        )
        # scratch = delta * gold_per_kill
        trigger.new_effect.change_variable(
            variable=scratch.variable_id, operation=Operation.MULTIPLY.value, quantity=kill.gold_per_kill,
        )
        # pay it out (delta of 0 adds 0 gold - a harmless no-op)
        trigger.new_effect.modify_resource_by_variable(
            tribute_list=RESOURCE_IDS["gold"], source_player=pid,
            operation=Operation.ADD.value, variable=scratch.variable_id,
        )
        # remember the new total so the next poll only pays for newer kills
        trigger.new_effect.modify_variable_by_resource(
            tribute_list=_KILLS_ATTRIBUTE, source_player=pid,
            operation=Operation.SET.value, variable=paid.variable_id,
        )


def _build_reinforcements(manager, balance, layout: Layout, defender_ids: list[int]) -> None:
    # A small squad arrives at each base on a timer, for the player to command.
    reinf = balance.reinforcements
    if not reinf.enabled:
        return
    bases = {base.player_id: base for base in layout.defenders}
    total = sum(stack.count for stack in reinf.units)
    for pid in defender_ids:
        positions = squad_positions(bases[pid].reinforce, total, layout.map_size)
        trigger = manager.add_trigger(f"Reinforcements - Player {pid}")
        trigger.enabled = True
        trigger.looping = True
        trigger.new_condition.timer(timer=reinf.interval_seconds)
        index = 0
        for stack in reinf.units:
            for _ in range(stack.count):
                x, y = positions[index]
                index += 1
                trigger.new_effect.create_object(
                    object_list_unit_id=stack.unit_id,
                    source_player=pid,
                    location_x=x,
                    location_y=y,
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
    # M1 ships solo, where losing all Castles is a loss via the team-defeat trigger
    # below. Mechanically removing a defeated player while co-op teammates fight on
    # is deferred to M3; for now this is an informational message.
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
