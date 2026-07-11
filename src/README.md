# src/ - scenario generator

Python that turns `config/` data into an `.aoe2scenario` file using [AoE2ScenarioParser].

**Status:** implemented in M1 (`cba_survival` package). Build with `python scripts/build.py`.

Modules (`src/cba_survival/`):
- `config.py` - load + validate `config/*.yaml` into typed dataclasses.
- `datasets.py` - resolve unit/building/age names to game ids.
- `layout.py` - deterministic arena geometry (bases, fortress, spawn).
- `players.py` - activate players, Imperial age, stipend, diplomacy.
- `placement.py` - place castles, production, army, villagers, fortress; flat grass map.
- `triggers.py` - setup, endless spawner, income, win/lose.
- `builder.py` - assemble the scenario and write the deployable mod folder.

See [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for the design.

[AoE2ScenarioParser]: https://github.com/KSneijders/AoE2ScenarioParser
