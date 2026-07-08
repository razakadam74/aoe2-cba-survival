# CBA Survival — Roadmap

Milestones are **vertical slices**: each one is a shippable increment. All numbers/waves are tunable.

## M0 — Repo & Plan  ✅ (current)
- Design, architecture, and roadmap docs.
- Repo scaffolding, license, contributing guide.
- **Done when:** the repo is public and a newcomer can understand the project and how to help.

## M1 — Minimal playable slice
- Generate a small two-base arena; place your **4 Castles** + a starting army + one production
  building, and a minimal **enemy fortress** (a couple of castles).
- Spawn **3** escalating waves that attack-move your castles.
- All three end-states wired: **defensive win** (survive 3), **offensive win** (raze enemy castles),
  **lose** (all your castles fall).
- `scripts/build` + `scripts/deploy`; a round-trip test in `tests/`.
- **Done when:** it loads in AoE2 DE and you can win *both* ways and lose.

## M2 — Full escalation & economy
- All **12** waves with tiered archetypes (infantry → ranged → cavalry → siege) from `config/*.yaml`.
- Wave-clear bounties + trickle; starting stipend; Houses for population.
- Reinforcements each wave; upgrades via the native tech tree.
- Tune the **enemy fortress** so the offensive rush is tempting but risky.
- First balance pass.
- **Done when:** a full 12-wave run feels escalating and fair, and the rush is a viable gamble.

## M3 — Co-op, difficulty, endless
- 2–4 player co-op.
- Difficulty tiers (config profiles).
- Endless mode with score = waves survived.
- **Done when:** a group can play co-op and pick a difficulty.

## M4 — Polish & publish
- Map-design pass in the in-game editor (chokepoints, visuals).
- Playtest-driven tuning.
- Publish to **mod.io** via the in-game Mods menu.
- GitHub Release attaching the built `.aoe2scenario` for non-coders.
- **Done when:** it's live on mod.io and downloadable from Releases.

## From milestones to work
Each milestone breaks into GitHub issues labeled `M1`/`M2`/… and `good first issue` where possible.
See [CONTRIBUTING.md](../CONTRIBUTING.md).
