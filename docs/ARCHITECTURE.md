# CBA Survival — Architecture

How the mod is built, and the technical facts we've **validated** so far.

## Toolchain (validated)
| Piece | Value |
|---|---|
| Language | Python (verified on 3.14; target 3.10+) |
| Library | [AoE2ScenarioParser](https://github.com/KSneijders/AoE2ScenarioParser) **0.8.3** |
| Config parsing | **PyYAML** (wave/balance data is YAML) |
| Game | Age of Empires II: DE, scenario version **1.58** |
| Output | `.aoe2scenario` binary |

> **Windows note:** force UTF-8 (`set PYTHONUTF8=1`) or the parser's status emoji crashes the
> cp1252 console. We also set `settings.PRINT_STATUS_UPDATES = False` to keep output clean.

## Pipeline
```
config/*.yaml (wave & balance data)    # WHAT to build — editable by anyone, YAML + comments
   |
   v
src/ (Python generator)                # turns config into a scenario
   |   AoE2DEScenario.from_default()   # fresh v1.58 scenario, no template file needed
   |   map / unit / trigger managers
   v
scripts/build                          # runs the generator
   |
   v
mod/<id>_CBA Survival/                  # deployable mod folder (git-ignored output)
   |-- info.json                        # {Author, Title, Description, CacheStatus}
   `-- resources/_common/scenario/CBA Survival.aoe2scenario
   |
   v
scripts/deploy -> local mods folder -> play -> (later) publish to mod.io / GitHub Release
```

Local mods folder (this machine):
`C:\Users\<you>\Games\Age of Empires 2 DE\<SteamID>\mods\local\`

## Generation model
The scenario is assembled with AoE2ScenarioParser "managers":
- **map_manager** — map size & terrain (v1: small two-base grass arena).
- **unit_manager** — place your **4 Castles**, starting army, production buildings, and the
  **enemy fortress** castles (`add_unit(player, unit_const, x, y)`).
- **player_manager** — enable Player 2, set starting resources.
- **trigger_manager** — the game logic (below), generated in loops from config.
- **xs_manager** — reserved for advanced logic later.

## Trigger design (the heart of it)
Generated from the YAML config:
- **Setup** (`execute_on_load`): set P1↔P2 diplomacy to **enemy**, grant starting stipend, show
  intro, activate Wave 1.
- **Wave N — Start** (activated by the previous wave): `display_instructions` ("Wave N"),
  `create_object` × the wave's units at the enemy-fortress spawn area, `attack_move` those P2 units
  toward your Castles, then `activate_trigger` → Wave N — Cleared.
- **Wave N — Cleared**: conditions `timer(breather)` **and** `own_fewer_objects(1, source_player=TWO,
  <military only>)` → effects: bounty via `modify_resource`, "Wave cleared", then activate Wave N+1
  (or **Defensive Victory** on the last wave).
- **Trickle** (looping): every X seconds, `modify_resource` a small amount.
- **Defensive Victory**: after wave 12 cleared → `declare_victory(source_player=ONE)`.
- **Offensive Victory**: `own_fewer_objects(1, object_list=Castle, source_player=TWO)` (no enemy
  castles left) → `declare_victory(source_player=ONE)`.
- **Defeat**: `own_fewer_objects(1, object_list=Castle, source_player=ONE)` (all 4 of your castles
  gone) → enemy `declare_victory` (you lose).

## Validated datasets (IDs we'll use)
**Units:** Militia 74, Man-at-Arms 75, Spearman 93, Archer 4, Skirmisher 7, Crossbowman 24,
Long Swordsman 77, Knight 38, Scout Cavalry 448, Champion 567, Mangonel 280, Battering Ram 1258,
Villager 83.
**Buildings:** Castle 82 (yours ×4 **and** the enemy fortress), Town Center 109, Barracks 12,
Archery Range 87, Stable 101, Blacksmith 103, University 209, Watch Tower 79, Stone Wall 117,
Gate 487, House 70.
**Player IDs:** GAIA 0, ONE 1 (you), TWO 2 (enemy fortress).

## Risks to validate in M1 (being honest about unknowns)
- **create → attack_move in the same trigger**: created units must be selectable by the following
  `attack_move`. Common pattern, but if enemies stand still we split "spawn" and "command" into two
  triggers ~1s apart.
- **`own_fewer_objects` counts the right things**: for "wave dead" we must count only P2 *military*
  (not the enemy castles), and for the win/lose castle checks we filter by `object_list = Castle`.
  The breather timer also guards against firing before units spawn.
- **`declare_victory` win-vs-lose flag** — confirm in-game; fallback for the loss case is "enemy
  declares victory".
- **Round-trip** — build → write → read back → assert triggers/units. This is M1's first test.

## Testing
`tests/` will hold a round-trip test (generate → `write_to_file` → `from_file` → assert expected
triggers/units) and YAML-schema validation (config parses and stays within sane bounds). We can
validate the *file*, not the *gameplay* — playtesting is human, reported via issues.
