"""Round-trip harness (issue #1): build -> write -> read -> assert."""
from __future__ import annotations

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from cba_survival.builder import build_scenario
from cba_survival.datasets import CASTLE_ID


def test_write_then_read_preserves_triggers_and_units(tmp_path, config, enemy_id):
    scenario = build_scenario(config)
    path = tmp_path / f"{config.balance.mod.title}.aoe2scenario"
    scenario.write_to_file(str(path))
    assert path.exists() and path.stat().st_size > 0

    reloaded = AoE2DEScenario.from_file(str(path))

    names = [t.name for t in reloaded.trigger_manager.triggers]
    assert "Setup" in names
    assert any(n.startswith("Wave 1") for n in names)
    assert any(n.startswith("Peak") for n in names)
    assert "Victory - enemy fortress razed" in names
    assert "Defeat - all defenders eliminated" in names

    enemy_castles = [u for u in reloaded.unit_manager.get_player_units(enemy_id) if u.unit_const == CASTLE_ID]
    assert len(enemy_castles) == config.balance.enemy_castles

    defender_castles = [u for u in reloaded.unit_manager.get_player_units(1) if u.unit_const == CASTLE_ID]
    assert len(defender_castles) == 4


def test_generation_is_deterministic(config):
    # The scenario writer stamps a save time into the file, so raw bytes vary.
    # What must be stable is the generated content: triggers and unit placement.
    def structure(scenario):
        names = [t.name for t in scenario.trigger_manager.triggers]
        units = sorted(
            (int(u.player), u.unit_const, round(u.x, 3), round(u.y, 3))
            for u in scenario.unit_manager.get_all_units()
        )
        return names, units

    assert structure(build_scenario(config)) == structure(build_scenario(config))
