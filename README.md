# CBA Survival — an Age of Empires II: DE mod

> A co-op-capable **PvE survival** scenario for Age of Empires II: Definitive Edition.
> Defend your **4 Castles** against escalating waves from an enemy fortress. Reinforce, upgrade,
> outlast — or break out and raze their castles.

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
You (Player 1) defend a base of **4 Castles**. An **enemy fortress** (Player 2) launches **12
escalating waves** that march on them. You start with an army + production buildings, get small
reinforcements each wave, and earn resources (wave-clear bounties + a trickle) to **train and
upgrade through the native tech tree**. **Two ways to win:** survive all 12 waves, *or* break out
and destroy the enemy's castles. You lose only when all 4 of your castles fall.
Full design: [docs/DESIGN.md](docs/DESIGN.md).

## Contributing
New contributors welcome — especially **wave designs and balance tuning**, which need *no coding*
(just edit a config file). Start with [CONTRIBUTING.md](CONTRIBUTING.md).

## License
[MIT](LICENSE) — use, fork, and remix freely. We ship **no** copyrighted game assets; the mod only
references built-in unit IDs by number.

[AoE2ScenarioParser]: https://github.com/KSneijders/AoE2ScenarioParser
