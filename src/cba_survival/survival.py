"""Build a 7v1 survival scenario on top of an existing CBA base.

We reuse the base scenario's map and fortresses (its layout), strip its
PvP triggers, and apply authentic-CBA-plus-survival logic:

  * Each player gets a fixed civilization and their castles auto-produce that
    civ's unique unit (so you play Celts and pump Woad Raiders, etc.).
  * Players 1..N are allied defenders (Player 1 is you); AI allies actively
    push to the fight instead of idling.
  * Player 8 is a buffed AI boss whose castles pour out a horde that marches
    on your base. Raze all boss castles to win; lose when every defender's
    castles have fallen.
  * The whole map is revealed.

The base file is third-party and kept local (git-ignored); this module only
adds our own, diffable logic on top of it.
"""
from __future__ import annotations

import json
from pathlib import Path

from AoE2ScenarioParser.datasets.object_support import Civilization
from AoE2ScenarioParser.datasets.trigger_lists import VisibilityState
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from .datasets import CASTLE_ID, DiplomacyState, PanelLocation, resolve_object_id

ENEMY = 8

# Fixed civ + unique unit per player position. Player 1 is Celts (Woad Raiders);
# Player 8 is the boss. Tunable later via config.
CIV_TABLE: dict[int, tuple[str, str]] = {
    1: ("CELTS", "WOAD_RAIDER"),
    2: ("BRITONS", "LONGBOWMAN"),
    3: ("FRANKS", "THROWING_AXEMAN"),
    4: ("MONGOLS", "MANGUDAI"),
    5: ("JAPANESE", "SAMURAI"),
    6: ("VIKINGS", "BERSERK"),
    7: ("BYZANTINES", "CATAPHRACT"),
    8: ("TEUTONS", "TEUTONIC_KNIGHT"),
}

DEFAULTS: dict = {
    "defenders": 7,
    "human_defenders": (1,),   # which defender seats are human (rest are AI allies)
    "defender_cap": 80,        # per-player unit cap (classic CBA ~80)
    "defender_interval": 6,    # seconds between a castle's spawns
    "defender_per_castle": 1,
    "boss_cap": 300,           # the boss overwhelms 7 defenders
    "boss_interval": 4,
    "boss_per_castle": 2,
    "march_interval": 3,       # re-command AI units so new spawns keep moving
    "spawn_offset": 6,         # spawn this many tiles off the castle (into the open)
    "reveal_map": True,
    "title": "CBA Survival 7v1",
    "author": "razakadam74",
}

INTRO_MESSAGE = (
    "CBA SURVIVAL - 7v1\n\n"
    "You (Celts) and your allies hold your castles against an endless horde "
    "pouring from the enemy fortress (Player 8). Your castles auto-produce your "
    "unique unit. Survive, push out, and raze every enemy castle to win. Lose "
    "your castles and you are out."
)


def build_survival(base_path: str | Path, **opts) -> AoE2DEScenario:
    """Load the CBA base and transform it into a 7v1 survival scenario."""
    cfg = {**DEFAULTS, **opts}
    scenario = AoE2DEScenario.from_file(str(base_path))
    castles = _castles_by_player(scenario)
    _strip_logic(scenario)
    _configure_players(scenario, cfg)
    _build_triggers(scenario, cfg, castles)
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
        "Description": "7v1 survival built on a CBA base: hold your castles, raze the enemy fortress.",
        "CacheStatus": 0,
    }
    (mod_folder / "info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return mod_folder


# --------------------------------------------------------------------------- #
def _castles_by_player(scenario: AoE2DEScenario) -> dict[int, list[tuple[int, int]]]:
    out: dict[int, list[tuple[int, int]]] = {}
    for pid in range(1, 9):
        out[pid] = [
            (round(u.x), round(u.y))
            for u in scenario.unit_manager.get_player_units(pid)
            if u.unit_const == CASTLE_ID
        ]
    return out


def _strip_logic(scenario: AoE2DEScenario) -> None:
    """Remove all of the base's triggers and variables (keep the map + units)."""
    manager = scenario.trigger_manager
    manager.triggers = []
    manager.variables = []
    try:
        manager.trigger_display_order = []
    except Exception:
        pass


def _configure_players(scenario: AoE2DEScenario, cfg: dict) -> None:
    manager = scenario.player_manager
    defenders = list(range(1, cfg["defenders"] + 1))
    humans = set(cfg["human_defenders"])

    for pid, (civ_name, _) in CIV_TABLE.items():
        manager.players[pid].civilization = Civilization[civ_name]

    for pid in defenders:
        player = manager.players[pid]
        player.human = pid in humans
        player.allied_victory = True
    manager.players[ENEMY].human = False

    if len(defenders) > 1:
        manager.set_diplomacy_teams(defenders, diplomacy=DiplomacyState.ALLY)
    for pid in defenders:
        manager.players[pid].set_player_diplomacy(ENEMY, DiplomacyState.ENEMY)
    manager.players[ENEMY].set_player_diplomacy(defenders, DiplomacyState.ENEMY)


def _build_triggers(scenario: AoE2DEScenario, cfg: dict, castles: dict[int, list[tuple[int, int]]]) -> None:
    manager = scenario.trigger_manager
    size = scenario.map_manager.map_width
    defenders = list(range(1, cfg["defenders"] + 1))
    humans = set(cfg["human_defenders"])
    offset = cfg["spawn_offset"]

    center = (size // 2, size // 2)
    p1_center = _centroid(castles[1]) if castles[1] else center

    setup = manager.add_trigger("Survival setup")
    setup.enabled = True
    setup.execute_on_load = True
    setup.new_effect.display_instructions(
        source_player=1, message=INTRO_MESSAGE, display_time=25,
        instruction_panel_position=PanelLocation.MIDDLE.value, string_id=-1, play_sound=0,
    )
    if cfg["reveal_map"]:
        for pid in defenders:
            for target in range(0, 9):
                setup.new_effect.set_player_visibility(
                    source_player=pid, target_player=target, visibility_state=VisibilityState.VISIBLE.value
                )

    # Each defender's castles auto-produce that civ's unique unit (capped, free).
    for pid in defenders:
        unit_id = resolve_object_id(CIV_TABLE[pid][1])
        _production_trigger(
            manager, f"Produce - Player {pid}", pid, unit_id, castles[pid], size, offset,
            cap=cfg["defender_cap"], interval=cfg["defender_interval"], per_castle=cfg["defender_per_castle"],
        )

    # The boss fortress pumps a bigger, tougher horde.
    _production_trigger(
        manager, "Boss production", ENEMY, resolve_object_id(CIV_TABLE[ENEMY][1]), castles[ENEMY], size, offset,
        cap=cfg["boss_cap"], interval=cfg["boss_interval"], per_castle=cfg["boss_per_castle"],
    )

    # The boss horde marches on your base; AI allies push to the centre to fight.
    _march_trigger(manager, "Boss march", ENEMY, p1_center, size, cfg["march_interval"])
    for pid in defenders:
        if pid not in humans:
            _march_trigger(manager, f"Advance - Player {pid}", pid, center, size, cfg["march_interval"])

    # Win: no boss castles left. Lose: no defender castles left anywhere.
    win = manager.add_trigger("Victory - boss fortress razed")
    win.enabled = True
    win.new_condition.own_fewer_objects(quantity=1, object_list=CASTLE_ID, source_player=ENEMY)
    for pid in defenders:
        win.new_effect.declare_victory(source_player=pid, enabled=1)

    defeat = manager.add_trigger("Defeat - all defenders fallen")
    defeat.enabled = True
    for pid in defenders:
        defeat.new_condition.own_fewer_objects(quantity=1, object_list=CASTLE_ID, source_player=pid)
    defeat.new_effect.declare_victory(source_player=ENEMY, enabled=1)


def _production_trigger(manager, name, player, unit_id, player_castles, size, offset, *, cap, interval, per_castle):
    trigger = manager.add_trigger(name)
    trigger.enabled = True
    trigger.looping = True
    trigger.new_condition.timer(timer=interval)
    trigger.new_condition.own_fewer_objects(quantity=cap, object_list=unit_id, source_player=player)
    for castle in player_castles:
        for sx, sy in _spawn_points(castle, size, per_castle, offset):
            trigger.new_effect.create_object(object_list_unit_id=unit_id, source_player=player, location_x=sx, location_y=sy)


def _march_trigger(manager, name, player, target, size, interval):
    trigger = manager.add_trigger(name)
    trigger.enabled = True
    trigger.looping = True
    trigger.new_condition.timer(timer=interval)
    trigger.new_effect.attack_move(
        source_player=player, location_x=target[0], location_y=target[1],
        area_x1=0, area_y1=0, area_x2=size - 1, area_y2=size - 1, max_units_affected=-1,
    )


def _centroid(points: list[tuple[int, int]]) -> tuple[int, int]:
    return (sum(x for x, _ in points) // len(points), sum(y for _, y in points) // len(points))


def _spawn_points(castle: tuple[int, int], size: int, count: int, offset: int) -> list[tuple[int, int]]:
    """Spawn tiles for one castle: a small cluster *offset* tiles toward the map
    centre (open ground in front of the castle), never on the castle itself."""
    cx, cy = castle
    mid = size // 2
    dx, dy = mid - cx, mid - cy
    mag = max(1.0, (dx * dx + dy * dy) ** 0.5)
    base_x = cx + round(offset * dx / mag)
    base_y = cy + round(offset * dy / mag)
    points: list[tuple[int, int]] = []
    for i in range(max(1, count)):
        points.append((_clamp(base_x + (i % 3) - 1, size), _clamp(base_y + i // 3, size)))
    return points


def _clamp(value: int, size: int) -> int:
    return max(1, min(size - 2, value))


__all__ = ["build_survival", "build_survival_mod", "DEFAULTS", "CIV_TABLE"]
