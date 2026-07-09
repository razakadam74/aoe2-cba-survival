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
- **unit_manager** — for **each active defender (Players 1–7)** place their **4 Castles**, a starting army,
  **villagers**, and a base of core military buildings (Barracks, Archery Range, Stable, Siege Workshop,
  Monastery, Castle + Blacksmith/University + Houses); place the **enemy fortress** castles for **Player 8**
  (`add_unit(player, unit_const, x, y)`). Defenders build *more* buildings forward themselves — the CBA push.
- **player_manager** — enable the **defender count** (1–7, from config) + the **enemy (Player 8)**; set each
  defender to the **Imperial Age** with a starting stipend. Defender count is a config knob, so solo (1) and
  7v1 use the same generator.
- **trigger_manager** — the game logic (below), generated from config.
- **xs_manager** — reserved for advanced logic later.

## Trigger design (the heart of it)
Generated from the YAML config:
- **Setup** (`execute_on_load`): set the **defender team (P1–P7) at war with the enemy (P8)** and allied
  with each other; grant each defender the starting stipend; **`add_train_location`**(Villager → Castle) +
  **`change_object_cost`**(Villager → expensive) per defender (no Town Center); init the **wave counter**;
  show intro; start the **Spawn loop**.
- **Spawn wave** (looping, fires every *interval* seconds — endless): increment the wave counter,
  `create_object` the wave's units (composition scales with `min(counter, cap)`) at the enemy (P8) spawn
  area, then `attack_move` those P8 units toward the defenders' Castles. Never deactivates — relentless.
  *(When a human occupies P8 they command the army instead of the spawner.)*
- **Income** (looping): **periodic gold** every X seconds (`modify_resource`), plus **kill income** — an
  `accumulate_attribute` loop on the *Kills* attribute (confirm the attribute id) that grants gold as your
  kill count climbs. Classic-CBA, so little/no gathering.
- **Team Victory** (the only win): `own_fewer_objects(1, object_list=Castle, source_player=EIGHT)` — no
  enemy castles left → `declare_victory` for every surviving defender. Active from the start.
- **Elimination / Defeat**: per defender, `own_fewer_objects(1, object_list=Castle, source_player=<Pn>)` —
  that player's castles gone → they're **eliminated**. When **all** defenders are out → enemy (P8)
  `declare_victory` (team loss).

> There is **no finale / no survive-to-win trigger** — the spawn loop never stops, so the game ends only
> when one side's castles are gone.

## Validated datasets (IDs we'll use)
**Units:** Villager 83, Militia 74, Man-at-Arms 75, Spearman 93, Archer 4, Skirmisher 7, Crossbowman 24,
Long Swordsman 77, Knight 38, Scout Cavalry 448, Champion 567, Monk 125, Mangonel 280,
Battering Ram 1258.
**Player siege / raze tools:** Capped Ram 422, Siege Ram 548, Onager 550, Trebuchet 42 (packed 331),
Bombard Cannon 36, Petard 440.
**Buildings:** Castle 82 (yours ×4 **and** the enemy fortress), Barracks 12, Archery Range 87,
Stable 101, **Siege Workshop 49**, **Monastery 104**, Blacksmith 103, University 209, Market 84,
Town Center 109, Watch Tower 79, Stone Wall 117, Gate 487, House 70.
**Player IDs:** GAIA 0, ONE–SEVEN 1–7 (co-op defenders, count from config), EIGHT 8 (enemy fortress — AI now, human later).

## Risks to validate in M1 (being honest about unknowns)
- **create → attack_move in the same trigger**: created units must be selectable by the following
  `attack_move`. Common pattern, but if enemies stand still we split "spawn" and "command" into two
  triggers ~1s apart.
- **`own_fewer_objects` counts the right things**: for the win/lose checks, filter by
  `object_list = Castle` so "fewer than 1" cleanly means "that side's castles are gone".
- **Endless spawn hygiene**: the looping spawner must not pile up so many units it tanks performance —
  cap concurrent units / spawn size in config, and confirm the loop's timer re-arms cleanly.
- **`declare_victory` win-vs-lose flag** — confirm in-game; fallback for the loss case is "enemy
  declares victory".
- **Kill income**: confirm the exact *Kills* attribute id for `accumulate_attribute`; the periodic-gold
  loop is a safe fallback if per-kill proves fiddly.
- **Round-trip** — build → write → read back → assert triggers/units. This is M1's first test.

## Testing
`tests/` will hold a round-trip test (generate → `write_to_file` → `from_file` → assert expected
triggers/units) and YAML-schema validation (config parses and stays within sane bounds). We can
validate the *file*, not the *gameplay* — playtesting is human, reported via issues.
