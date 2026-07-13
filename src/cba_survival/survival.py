"""Layer a 7v1 survival mode on top of a real CBA scenario.

We keep the entire CBA base intact - its thousands of triggers detect each
player's civ and auto-produce that civ's unique unit from the castles at the
right rate, plus handle resources, ages, and per-castle elimination. On top of
that we add only a thin survival layer:

  * A concrete civ per seat: CBA only produces a player's unique unit once that
    player has a real civ, and a scenario left on "Random" never resolves in
    single-player (so no uniques). We roll a random concrete civ per player.
  * 7v1 teams: Player 1 (you, human) plus AI allies 2-7, all versus Player 8.
  * A boss that actually attacks: Player 8's AI units are attack-moved onto your
    base every few seconds so the enemy swarms you. CBA leaves unit control to
    humans, so without this an AI enemy would just sit at home - and moving the
    units also keeps its spawn tiles clear so it keeps pumping out a horde.
  * Allied AI units are attack-moved to the centre so they join the fight too.
  * A clean raze-to-win / lose-your-castles victory for the 7v1 split (CBA's own
    end-game triggers are disabled so ours is authoritative).

We never touch CBA's production, resources, ages, or rates - only which civ each
seat plays, the diplomacy, and the AI's marching orders.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from AoE2ScenarioParser.datasets.effects import EffectId
from AoE2ScenarioParser.datasets.object_support import Civilization
from AoE2ScenarioParser.datasets.trigger_lists import VisibilityState
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from .datasets import CASTLE_ID, DiplomacyState

BOSS = 8
DEFENDERS = (1, 2, 3, 4, 5, 6, 7)

# CBA only produces a player's unique unit once that player has a concrete civ
# (its detection keys off civ techs). AoE2 has no "set civ" trigger, so CBA
# relies on the lobby to resolve "Random" - which never happens in a standalone
# single-player scenario. So we assign a concrete civ per seat at build time.
# These are the standard civs CBA Requiem supports (no Chronicles/RoR civs).
STANDARD_CIVS = (
    "AZTECS", "ARMENIANS", "BENGALIS", "BERBERS", "BOHEMIANS", "BRITONS",
    "BULGARIANS", "BURGUNDIANS", "BURMESE", "BYZANTINES", "CELTS", "CHINESE",
    "CUMANS", "DRAVIDIANS", "ETHIOPIANS", "FRANKS", "GEORGIANS", "GOTHS",
    "GURJARAS", "HINDUSTANIS", "HUNS", "INCAS", "ITALIANS", "JAPANESE",
    "KHMER", "KOREANS", "LITHUANIANS", "MAGYARS", "MALAY", "MALIANS",
    "MAYANS", "MONGOLS", "PERSIANS", "POLES", "PORTUGUESE", "ROMANS",
    "SARACENS", "SICILIANS", "SLAVS", "SPANISH", "TATARS", "TEUTONS",
    "TURKS", "VIETNAMESE", "VIKINGS",
)

DEFAULTS: dict = {
    "human": 1,                # your player seat; every other player is AI
    "reveal_map": True,        # reveal the whole map so you see the horde coming
    "attack_interval": 5,      # seconds between re-issuing the AI horde/ally orders
    "seed": None,              # set an int for a reproducible civ draw
    "title": "CBA Survival 7v1",
    "author": "razakadam74",
}


def build_survival(base_path: str | Path, **opts) -> AoE2DEScenario:
    """Load the CBA base and layer the 7v1 survival mode on top."""
    scenario = AoE2DEScenario.from_file(str(base_path))
    return transform_to_survival(scenario, **opts)


def transform_to_survival(scenario: AoE2DEScenario, **opts) -> AoE2DEScenario:
    """Apply the survival layer in place, keeping all of CBA's own triggers."""
    cfg = {**DEFAULTS, **opts}
    _configure_players(scenario, cfg)
    _add_survival_triggers(scenario, cfg)
    return scenario


def build_survival_mod(base_path: str | Path, output_dir: str | Path, **opts) -> Path:
    """Build and write the deployable mod folder; return its path."""
    cfg = {**DEFAULTS, **opts}
    scenario = build_survival(base_path, **opts)
    title = cfg["title"]
    mod_folder = Path(output_dir) / title
    scenario_dir = mod_folder / "resources" / "_common" / "scenario"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    scenario.write_to_file(str(scenario_dir / f"{title}.aoe2scenario"))
    info = {
        "Author": cfg["author"],
        "Title": title,
        "Description": (
            "7v1 survival on a CBA base: you and AI allies hold your castles while "
            "Player 8 swarms you. Raze the enemy fortress to win."
        ),
        "CacheStatus": 0,
    }
    (mod_folder / "info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return mod_folder


# --------------------------------------------------------------------------- #
def _configure_players(scenario: AoE2DEScenario, cfg: dict) -> None:
    pm = scenario.player_manager
    human = cfg["human"]
    defenders = list(DEFENDERS)

    # Concrete civ per seat so CBA's unique-unit production actually fires
    # (a scenario left on "Random" never resolves in single-player -> no uniques).
    rng = random.Random(cfg.get("seed"))
    civs = rng.sample(STANDARD_CIVS, 8)
    for pid in range(1, 9):
        pm.players[pid].civilization = Civilization[civs[pid - 1]]

    for pid in range(1, 9):
        pm.players[pid].human = pid == human
    for pid in defenders:
        pm.players[pid].allied_victory = True
    pm.players[BOSS].allied_victory = False

    # 7v1 diplomacy: all defenders allied, everyone against the boss.
    pm.set_diplomacy_teams(defenders, diplomacy=DiplomacyState.ALLY)
    for pid in defenders:
        pm.players[pid].set_player_diplomacy(BOSS, DiplomacyState.ENEMY)
    pm.players[BOSS].set_player_diplomacy(defenders, DiplomacyState.ENEMY)


def _add_survival_triggers(scenario: AoE2DEScenario, cfg: dict) -> None:
    tm = scenario.trigger_manager
    size = scenario.map_manager.map_width
    human = cfg["human"]
    interval = cfg["attack_interval"]
    center = (size // 2, size // 2)
    human_base = _base_centroid(scenario, human) or center

    # Make our 7v1 victory authoritative: silence CBA's own end-game triggers.
    for trigger in list(tm.triggers):
        if any(e.effect_type == EffectId.DECLARE_VICTORY.value for e in trigger.effects):
            trigger.enabled = False

    if cfg["reveal_map"]:
        reveal = tm.add_trigger("Survival - reveal map")
        reveal.enabled = True
        for target in range(0, 9):
            reveal.new_effect.set_player_visibility(
                source_player=human, target_player=target, visibility_state=VisibilityState.VISIBLE.value
            )

    # The boss horde marches on your base (and keeps its own spawn tiles clear).
    _assault_trigger(tm, "Survival - boss assault", BOSS, human_base, size, interval)
    # AI allies push to the centre so they actually fight instead of idling.
    for pid in DEFENDERS:
        if pid != human:
            _assault_trigger(tm, f"Survival - ally advance P{pid}", pid, center, size, interval)

    # Clean 7v1 win / lose (CBA already removes a player's units when razed).
    win = tm.add_trigger("Survival - defenders win")
    win.enabled = True
    win.new_condition.own_fewer_objects(quantity=1, object_list=CASTLE_ID, source_player=BOSS)
    for pid in DEFENDERS:
        win.new_effect.declare_victory(source_player=pid, enabled=1)

    lose = tm.add_trigger("Survival - defenders lose")
    lose.enabled = True
    for pid in DEFENDERS:
        lose.new_condition.own_fewer_objects(quantity=1, object_list=CASTLE_ID, source_player=pid)
    lose.new_effect.declare_victory(source_player=BOSS, enabled=1)


def _assault_trigger(tm, name, player, target, size, interval) -> None:
    trigger = tm.add_trigger(name)
    trigger.enabled = True
    trigger.looping = True
    trigger.new_condition.timer(timer=interval)
    trigger.new_effect.attack_move(
        source_player=player, location_x=target[0], location_y=target[1],
        area_x1=0, area_y1=0, area_x2=size - 1, area_y2=size - 1, max_units_affected=-1,
    )


def _base_centroid(scenario: AoE2DEScenario, player: int):
    pts = [
        (round(u.x), round(u.y))
        for u in scenario.unit_manager.get_player_units(player)
        if u.unit_const == CASTLE_ID
    ]
    if not pts:
        return None
    return (sum(x for x, _ in pts) // len(pts), sum(y for _, y in pts) // len(pts))


__all__ = ["build_survival", "transform_to_survival", "build_survival_mod", "DEFAULTS", "BOSS", "DEFENDERS"]
