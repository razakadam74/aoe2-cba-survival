"""In-memory generator asserts (issues #2, #3, #4)."""
from __future__ import annotations

from conftest import trigger_named, units_of

from AoE2ScenarioParser.datasets.effects import EffectId

from cba_survival.datasets import CASTLE_ID, VILLAGER_ID, StartingAge


def test_defenders_and_enemy_active(built, config, enemy_id):
    manager = built.player_manager
    for pid in range(1, config.balance.defenders + 1):
        assert manager.players[pid].active
    assert manager.players[enemy_id].active


def test_imperial_age_and_stipend(built, config):
    p1 = built.player_manager.players[1]
    assert int(p1.starting_age) == StartingAge.IMPERIAL_AGE.value
    assert p1.gold == config.balance.stipend["gold"]
    assert p1.food == config.balance.stipend["food"]


def test_castles_placed(built, config, enemy_id):
    assert len(units_of(built, 1, CASTLE_ID)) == 4
    assert len(units_of(built, enemy_id, CASTLE_ID)) == config.balance.enemy_castles


def test_villagers_and_army_placed(built, config):
    assert len(units_of(built, 1, VILLAGER_ID)) == config.balance.starting_villagers
    for stack in config.balance.starting_army:
        assert len(units_of(built, 1, stack.unit_id)) >= stack.count


def test_expected_triggers_present(built, config):
    names = [t.name for t in built.trigger_manager.triggers]
    assert "Setup" in names
    assert any(n.startswith("Wave 1") for n in names)
    assert any(n.startswith("Peak") for n in names)
    assert "Victory - enemy fortress razed" in names
    assert "Defeat - all defenders eliminated" in names
    assert sum(n.startswith("Income") for n in names) == config.balance.defenders


def test_trigger_count(built, config):
    # setup + waves + peak + income(N) + win + elimination(N) + defeat
    expected = 1 + len(config.waves.waves) + 1 + config.balance.defenders + 1 + config.balance.defenders + 1
    assert len(built.trigger_manager.triggers) == expected


def test_setup_flags_and_effects(built):
    setup = trigger_named(built, "Setup")
    assert setup.enabled
    assert setup.execute_on_load
    # train-location + cost (x defenders) + intro + activate-first-wave.
    assert len(setup.effects) >= 4


def test_peak_is_endless_loop(built):
    peak = next(t for t in built.trigger_manager.triggers if t.name.startswith("Peak"))
    assert peak.looping
    assert peak.enabled is False  # activated by the wave chain, not at start
    assert len(peak.conditions) == 1  # the interval timer


def test_scripted_waves_start_disabled(built):
    for trigger in built.trigger_manager.triggers:
        if trigger.name.startswith("Wave "):
            assert trigger.enabled is False


def test_win_and_defeat_shape(built, config, enemy_id):
    win = trigger_named(built, "Victory - enemy fortress razed")
    assert len(win.conditions) == 1
    assert win.conditions[0].object_list == CASTLE_ID
    assert win.conditions[0].source_player == enemy_id
    assert len(win.effects) == config.balance.defenders  # declare_victory per defender

    defeat = trigger_named(built, "Defeat - all defenders eliminated")
    assert len(defeat.conditions) == config.balance.defenders
    assert all(cond.object_list == CASTLE_ID for cond in defeat.conditions)
    assert len(defeat.effects) == 1


def test_activation_chain_reaches_looping_peak(built):
    # The activation chain (Setup -> Wave 1 -> ... -> Peak) is the core mechanic;
    # assert it is actually wired via activate_trigger and terminates at the loop.
    triggers = built.trigger_manager.triggers
    by_id = {t.trigger_id: t for t in triggers}

    def activated_ids(trigger):
        return [
            effect.trigger_id
            for effect in trigger.effects
            if effect.effect_type == EffectId.ACTIVATE_TRIGGER and effect.trigger_id in by_id
        ]

    setup = trigger_named(built, "Setup")
    links = activated_ids(setup)
    assert len(links) == 1, "Setup should activate exactly one trigger (Wave 1)"

    current = by_id[links[0]]
    visited = [current.name]
    guard = 0
    while True:
        guard += 1
        assert guard < 100, "activation chain did not terminate"
        nxt = activated_ids(current)
        if not nxt:
            break
        assert len(nxt) == 1
        current = by_id[nxt[0]]
        visited.append(current.name)

    assert visited[0].startswith("Wave 1")
    assert current.name.startswith("Peak")
    assert current.looping
    wave_names = [n for n in visited if n.startswith("Wave ")]
    assert wave_names == sorted(wave_names)
