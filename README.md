# CBA Survival — an Age of Empires II: DE mod

> A co-op-capable **PvE survival** scenario for Age of Empires II: Definitive Edition.
> Hold your **4 Castles** against endless escalating waves from an enemy fortress — then break out and
> raze their castles to win.

**Status:** 🟡 Planning (Milestone 0). No playable build yet — see the [Roadmap](docs/ROADMAP.md).

## What makes this different
Most AoE2 scenarios are hand-clicked in the in-game editor and shipped as an opaque binary
`.aoe2scenario` file — impossible to diff, review, or collaborate on. **CBA Survival is generated
from code** (via [AoE2ScenarioParser]), so:

- Waves and balance live in readable `config/` files anyone can tweak.
- Every change is reviewable in a pull request.
- The whole scenario rebuilds reproducibly with one command.

## How it works (high level)
`config/` (wave & balance data) → `src/` (Python generator) → `scripts/build` →
`mod/…/CBA Survival.aoe2scenario` → drop into your local AoE2 mods folder → play.
Details in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## The game (v1)
You (Player 1) defend a base of **4 Castles**. An **enemy fortress** (Player 2) pours out an **endless**
stream of escalating waves that march on them. You start in the **Imperial Age** with a base and
**villagers**, and earn resources from **kills + periodic income** — spend it to train any army, research
upgrades, and **build army buildings forward** to push (classic CBA). The onslaught **never stops**, so
the **only way to win is to raze the enemy fortress's castles** — you must defend *and* break out. Play
**solo or up-to-7-player co-op** (each defends their own castles; a human can even take the enemy's seat
later). You lose when your castles fall. Full design: [docs/DESIGN.md](docs/DESIGN.md).

## Contributing
New contributors welcome — especially **wave designs and balance tuning**, which need *no coding*
(just edit a config file). Start with [CONTRIBUTING.md](CONTRIBUTING.md).

## License
[MIT](LICENSE) — use, fork, and remix freely. We ship **no** copyrighted game assets; the mod only
references built-in unit IDs by number.

[AoE2ScenarioParser]: https://github.com/KSneijders/AoE2ScenarioParser
