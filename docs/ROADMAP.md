# CBA Survival - Roadmap

Milestones are **vertical slices**: each one is a shippable increment. All numbers/waves are tunable.

## M0 - Repo & Plan  ✅
- Design, architecture, and roadmap docs.
- Repo scaffolding, license, contributing guide.
- **Done when:** the repo is public and a newcomer can understand the project and how to help.

## M1 - Minimal playable slice  🟢 (code complete, pending in-game playtest)
- Generate a small two-base arena; place your **4 Castles**, a starting army, **villagers**, a base of
  military buildings (Imperial Age, starting stipend), and a minimal **enemy fortress** (a couple of castles).
- An **endless looping spawner** (a few escalating waves for the slice) that attack-moves your castles.
- Basic income: a **periodic gold** loop (+ stipend) so you can build/train; full kill-income lands in M2.
- Win/lose wired: **win** = raze all enemy castles (the only win); **lose** = all your castles fall.
  No finale - the spawner never stops.
- `scripts/build` + `scripts/deploy`; a round-trip test in `tests/`.
- **Done when:** it loads in AoE2 DE and you can build forward, win (raze the enemy), and lose.

## M2 - Full escalation & economy  🟢 (code complete, pending playtest + balance pass)
- **Endless** spawner with tiered archetypes (infantry -> ranged -> cavalry -> siege) from `config/*.yaml`,
  escalating over ~10 scripted waves toward a peak, then holding at full intensity via the looping peak.
- **Kill income** (per-kill gold via a variable delta-poll of Units Killed) + **periodic gold** + starting stipend; Houses for population.
- Periodic reinforcements (a squad arrives at each base on a timer); upgrades via the native tech tree.
- Tune the **enemy fortress** + escalation cap so the break-out is tempting but risky. *(balance = playtest)*
- First balance pass. *(needs in-game playtest)*
- **Done when:** the endless ramp feels relentless-but-fair and a well-timed raze is a viable gamble.

## M3 - Co-op (up to 7v1) & difficulty
- **Up to 7-player co-op** (each defends their own 4 castles; individual elimination; team win by raze).
- Difficulty tiers (config profiles).
- Scoring: time-to-raze and/or longest hold.
- **Done when:** 7 players can defend together vs the AI enemy and pick a difficulty.

## M4 - Polish & publish
- Map-design pass in the in-game editor (chokepoints, visuals).
- Playtest-driven tuning.
- Publish to **mod.io** via the in-game Mods menu.
- GitHub Release attaching the built `.aoe2scenario` for non-coders.
- **Done when:** it's live on mod.io and downloadable from Releases.

## M5 - Play-as-the-enemy (stretch)
- Let a human occupy the enemy slot (the last active player) and command the assault - asymmetric 1-vs-many PvP.
- Same map/triggers; the wave spawner yields to the human's army.
- **Done when:** a human can play the enemy and attack the defenders.

## From milestones to work
Each milestone breaks into GitHub issues labeled `M1`/`M2`/… and `good first issue` where possible.
See [CONTRIBUTING.md](../CONTRIBUTING.md).
