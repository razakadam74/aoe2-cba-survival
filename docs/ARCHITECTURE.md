# CBA Survival - Architecture

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
config/*.yaml (wave & balance data)    # WHAT to build - editable by anyone, YAML + comments
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
- **map_manager** - map size & terrain (v1: small two-base grass arena).
- **unit_manager** - for **each active defender (Players 1-7)** place their **4 Castles**, a starting army,
  **villagers**, and a base of core military buildings (Barracks, Archery Range, Stable, Siege Workshop,
  Monastery, Castle + Blacksmith/University + Houses); place the **enemy fortress** castles for the
  **enemy slot (Player N+1)** (`add_unit(player, unit_const, x, y)`). Defenders build *more* buildings forward themselves - the CBA push.
- **player_manager** - enable the **defender count** (1-7, from config) + the **enemy**; set each
  defender to the **Imperial Age** with a starting stipend. Defender count is a config knob, so solo (1) and
  7v1 use the same generator. The engine needs active players contiguous from Player 1, so the enemy is the
  next slot after the defenders: **solo = Player 2, full 7v1 = Player 8** (`active_players = defenders + 1`).
- **trigger_manager** - the game logic (below), generated from config.
- **xs_manager** - reserved for advanced logic later.

## Trigger design (the heart of it)
Generated from the YAML config. *As built in M1:* the spawner is a chain of scripted, escalating wave
triggers that hands off to a single endless looping **Peak** trigger (a runtime wave counter with
`min(counter, cap)` scaling is deferred to M2).
- **Setup** (`execute_on_load`): diplomacy sets the **defender team at war with the enemy slot** and allied
  with each other; grant each defender the starting stipend; **`add_train_location`**(Villager to Castle) +
  **`change_object_cost`**(Villager to expensive) per defender (no Town Center); show intro; **activate the
  first wave** (which starts the chain).
- **Spawn wave** (scripted chain, then an endless looping Peak fires every *interval* seconds):
  `create_object` the wave's units at the enemy spawn area, then `attack_move` those enemy units toward the
  defenders' Castles; each wave activates the next, and the last activates the looping Peak that never
  deactivates - relentless. *(When a human occupies the enemy slot they command the army instead of the spawner.)*
- **Income** (looping): **periodic gold** every X seconds (`modify_resource`) + **kill income** - an
  `accumulate_attribute` loop on *Units Killed* (attribute 20) that pays gold per block of kills - plus
  periodic **reinforcements** (a squad `create_object`ed at each base on a timer, for the player to
  command). Classic-CBA, so little/no gathering.
- **Team Victory** (the only win): `own_fewer_objects(1, object_list=Castle, source_player=<enemy slot>)` - no
  enemy castles left, so `declare_victory` for every surviving defender. Active from the start.
- **Elimination / Defeat**: per defender, `own_fewer_objects(1, object_list=Castle, source_player=<Pn>)` -
  that player's castles gone, so they're **eliminated**. When **all** defenders are out, the enemy slot
  `declare_victory` (team loss).

> There is **no finale / no survive-to-win trigger** - the spawn loop never stops, so the game ends only
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
**Player IDs:** GAIA 0, ONE-SEVEN 1-7 (co-op defenders, count from config), the **enemy fortress** is the
next slot after the defenders (Player N+1: **Player 2** solo, up to **Player 8** at full 7v1 - AI now, human later).

## Risks to validate in M1 (being honest about unknowns)
- **create → attack_move in the same trigger**: created units must be selectable by the following
  `attack_move`. Common pattern, but if enemies stand still we split "spawn" and "command" into two
  triggers ~1s apart.
- **`own_fewer_objects` counts the right things**: for the win/lose checks, filter by
  `object_list = Castle` so "fewer than 1" cleanly means "that side's castles are gone".
- **Endless spawn hygiene**: the looping spawner must not pile up so many units it tanks performance -
  cap concurrent units / spawn size in config, and confirm the loop's timer re-arms cleanly.
- **`declare_victory` win-vs-lose flag** - confirm in-game; fallback for the loss case is "enemy
  declares victory".
- **Kill income**: confirm the exact *Kills* attribute id for `accumulate_attribute`; the periodic-gold
  loop is a safe fallback if per-kill proves fiddly.
- **Round-trip** - build → write → read back → assert triggers/units. This is M1's first test.

## Testing
`tests/` will hold a round-trip test (generate → `write_to_file` → `from_file` → assert expected
triggers/units) and YAML-schema validation (config parses and stays within sane bounds). We can
validate the *file*, not the *gameplay* - playtesting is human, reported via issues.
