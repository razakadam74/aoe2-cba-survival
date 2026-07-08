# src/ — scenario generator

Python that turns `config/` data into an `.aoe2scenario` file using [AoE2ScenarioParser].

**Status:** not yet implemented — see [../docs/ROADMAP.md](../docs/ROADMAP.md) (M1).

Planned modules:
- scenario assembly (map, players, starting units/buildings)
- wave generator (config → spawn / attack-move / cleared triggers, in loops)
- trigger helpers (win/lose, economy, diplomacy)

See [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for the design.

[AoE2ScenarioParser]: https://github.com/KSneijders/AoE2ScenarioParser
