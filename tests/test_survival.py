"""Survival layer asserts: keep CBA's triggers, add 7v1 + boss assault + win/lose.

Runs on a synthetic scenario that mimics CBA (8 forts, a couple of stand-in CBA
triggers) so it never touches the git-ignored base file.
"""
from __future__ import annotations

import pytest

from AoE2ScenarioParser.datasets.effects import EffectId
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from cba_survival.datasets import CASTLE_ID
from cba_survival.survival import BOSS, DEFENDERS, transform_to_survival

MAP = 120
CENTER = (MAP // 2, MAP // 2)
FORTS = {
    1: (42, 8), 2: (78, 8), 3: (8, 42), 4: (112, 42),
    5: (8, 78), 6: (112, 78), 7: (42, 112), 8: (78, 112),
}


def _expected_centroid(pid):
    cx, cy = FORTS[pid]
    xs = [cx + i for i in range(4)]
    return (sum(xs) // 4, cy)


def _synthetic_cba() -> AoE2DEScenario:
    scenario = AoE2DEScenario.from_default()
    scenario.map_manager.map_size = MAP
    scenario.player_manager.active_players = 8
    um = scenario.unit_manager
    for pid, (cx, cy) in FORTS.items():
        for i in range(4):
            um.add_unit(player=pid, unit_const=CASTLE_ID, x=cx + i, y=cy)
    tm = scenario.trigger_manager
    # Stand-in for CBA's own machinery: a production trigger (must be kept) and a
    # victory trigger (must be disabled by our layer).
    keep = tm.add_trigger("cba-keep")
    keep.enabled = True
    keep.looping = True
    keep.new_effect.create_object(object_list_unit_id=CASTLE_ID, source_player=1, location_x=10, location_y=10)
    vic = tm.add_trigger("cba-victory")
    vic.enabled = True
    vic.new_effect.declare_victory(source_player=1, enabled=1)
    return scenario


@pytest.fixture
def built():
    return transform_to_survival(_synthetic_cba())


def _named(scenario, name):
    return next((t for t in scenario.trigger_manager.triggers if t.name == name), None)


def _attack_target(trigger):
    e = trigger.effects[0]
    return (e.location_x, e.location_y)


def test_keeps_cba_triggers(built):
    keep = _named(built, "cba-keep")
    assert keep is not None and keep.enabled  # CBA production untouched
    # original 2 CBA triggers + 10 survival triggers.
    assert len(built.trigger_manager.triggers) == 2 + 10


def test_disables_cba_victory(built):
    assert _named(built, "cba-victory").enabled is False
    stray = [
        t for t in built.trigger_manager.triggers
        if not t.name.startswith("Survival")
        and any(e.effect_type == EffectId.DECLARE_VICTORY.value for e in t.effects)
    ]
    assert all(not t.enabled for t in stray)


def test_human_and_ai_seats(built):
    pm = built.player_manager
    assert pm.players[1].human is True
    for pid in range(2, 9):
        assert pm.players[pid].human is False


def test_players_get_concrete_civs(built):
    # CBA needs real civs (not RANDOM) or it never produces unique units.
    from cba_survival.survival import STANDARD_CIVS
    for pid in range(1, 9):
        civ = str(built.player_manager.players[pid].civilization).split(".")[-1]
        assert civ != "RANDOM"
        assert civ in STANDARD_CIVS


def _stance(value):
    """Diplomacy cells are DiplomacyState in-memory, plain ints once written."""
    return value.value if hasattr(value, "value") else value


def test_7v1_diplomacy(built):
    pm = built.player_manager
    # diplomacy is 0-indexed by player: slot i is the stance toward player i+1.
    d1 = pm.players[1].diplomacy
    for ally in range(2, 8):
        assert _stance(d1[ally - 1]) == 0   # allied with fellow defenders
    assert _stance(d1[BOSS - 1]) == 3       # enemy with the boss
    dboss = pm.players[BOSS].diplomacy
    for pid in range(1, 8):
        assert _stance(dboss[pid - 1]) == 3  # boss hostile to all defenders
    for pid in DEFENDERS:
        assert pm.players[pid].allied_victory is True


def test_boss_assaults_human_base(built):
    boss = _named(built, "Survival - boss assault")
    assert boss.looping and boss.enabled
    assert boss.effects[0].source_player == BOSS
    assert _attack_target(boss) == _expected_centroid(1)  # marches on YOUR base, not centre


def test_allies_advance_to_center_human_excluded(built):
    for pid in range(2, 8):
        adv = _named(built, f"Survival - ally advance P{pid}")
        assert adv is not None and adv.looping
        assert _attack_target(adv) == CENTER
    assert _named(built, "Survival - ally advance P1") is None


def test_win_and_lose_shape(built):
    win = _named(built, "Survival - defenders win")
    assert len(win.conditions) == 1
    assert win.conditions[0].object_list == CASTLE_ID
    assert win.conditions[0].source_player == BOSS
    assert len(win.effects) == 7  # declare_victory per defender

    lose = _named(built, "Survival - defenders lose")
    assert len(lose.conditions) == 7
    assert all(c.object_list == CASTLE_ID for c in lose.conditions)
    assert len(lose.effects) == 1


def test_reveal_map(built):
    reveal = _named(built, "Survival - reveal map")
    assert reveal is not None
    assert len(reveal.effects) == 9  # visibility toward players 0..8
