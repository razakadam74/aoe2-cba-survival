# CBA Survival — Game Design

> Status: **v1 spec locked** for the first playable milestone. Stretch ideas are marked *post-v1*.

## Vision
A **PvE survival** scenario for Age of Empires II: Definitive Edition, inspired by the community's
beloved **CBA (Castle Blood Automatic)** scenarios — *Castle* (you defend a cluster of castles),
*Blood* (constant combat, no economy-building), *Automatic* (your army spawns on its own).

You defend a base of **4 Castles** against escalating waves launched from an **enemy fortress**.
No villager economy to babysit — you start in the **Imperial Age** with every military building and a
generous treasury, so you can field **any army you like** off the spoils of war. **Your goal:** raze
the enemy's castles. Surviving all 12 waves halts the onslaught and arms you for a final assault — or,
if you're strong enough, break out and level them early. Designed to be **solo-testable** first,
**co-op** later.

## Core loop
1. **Prepare** — a brief calm before wave 1 (position your army, queue upgrades).
2. **Survive a wave** — enemies pour out of the enemy fortress and march on your Castles. Fight them off.
3. **Reap** — clearing a wave pays a resource **bounty**; a slow **trickle** also drips in.
4. **Reinforce & upgrade** — spend resources at your buildings via the **native tech tree**
   (Forging, Fletching, unit-line upgrades…); small auto-reinforcements arrive each wave.
5. **Escalate** — each wave is bigger and nastier. Hold your 4 Castles through all 12.
6. **Finale** — clearing wave 12 **stops the enemy spawns** and grants you a **siege battalion**. March
   out and **raze the enemy fortress's castles to win**.

**Go early if you dare.** You don't have to wait for the finale — at any point you can march on the
**enemy fortress** and raze its castles for an instant win. But every soldier attacking is one not
defending, its castles shoot back, and razing needs **siege** — a deliberate risk/reward race.

## v1 spec (locked)
| Aspect | Decision |
|---|---|
| Players | 1 human (Player 1) vs a hostile **enemy fortress** (Player 2). P2 is *not* a mirror army — it's castles + a wave spawner, so the mode stays solo-testable. |
| Objective | Defend your **4 Castles**. |
| Enemy | An **enemy fortress** (its own castles) that launches the waves and can itself be attacked. |
| Waves | **12**, finite, escalating. |
| Your forces | **Full army freedom, no villagers.** Start in the **Imperial Age** with every military building pre-placed; train any composition. Plus a starting army + small auto-reinforcements each wave. |
| Economy | **Generous**: starting stipend + wave-clear **bounty** + steady **trickle**. Upgrades via the **native tech tree** (no custom shop). |
| Win | **Raze all enemy Castles** (any time). Clearing all 12 waves stops the spawns + grants a siege battalion to guarantee the final assault. |
| Lose | All 4 of your Castles destroyed. |
| Map | Small flat **two-base arena** (your castles ↔ battlefield ↔ enemy fortress). Chokepoints & looks polished later in the in-game editor. |
| Config | Wave & balance data in **YAML** (`config/`), so anyone can tune it without touching code. |

## Enemy fortress & the two-phase finale
Player 2 is deliberately **asymmetric**: no micro-managed enemy army, just a fortress of castles that
**spawns the timed waves** and **defends itself** (its castles fire arrows at attackers). This keeps
the mode solo-testable while still giving you a target to break.

**Winning always means razing the enemy's castles.** There are two ways to get there:
- **Two-phase finale (the intended arc):** hold your castles through all 12 waves → clearing wave 12
  **stops the spawns** and grants you a **siege battalion** → march out and level the fortress.
- **Early breakout (the gamble):** rush the fortress before wave 12 and raze it for an instant win —
  but attackers aren't home defending, and you'll need **siege** to crack the castles.

The tension is real: every soldier you send to attack is one not defending your own 4 castles.

## Wave escalation model
- **Size** grows with the wave number (e.g., `base + growth × N` units).
- **Composition** shifts from weak to strong as tiers unlock:
  - Waves 1–3: light infantry (Militia / Spearman).
  - Waves 4–6: add ranged (Archers / Skirmishers).
  - Waves 7–9: add cavalry (Scouts / Knights) + heavier infantry.
  - Waves 10–12: add **siege** (Rams / Mangonels) — the natural castle-killer, so the late game
    becomes "kill the siege before it levels your castles."
- **Pacing**: the next wave begins shortly after the previous is cleared (with a minimum breather).
- All composition/size numbers live in **`config/`** so they can be tuned without touching code.

## Your forces & economy
- **No villagers, no base-building** — this is *Blood*-style. You get **full army freedom** instead.
- **Imperial Age start** with every military building pre-placed (Barracks, Archery Range, Stable,
  **Siege Workshop**, Monastery, Castle + Blacksmith & University), so *any* unit is trainable — including
  the **siege** you need to raze castles.
- **Generous economy**: a healthy **starting stipend**, a **wave-clear bounty** (scales with wave N),
  and a small **trickle**, so you can always afford to rebuild and re-arm.
- **Population** headroom via Houses; small **auto-reinforcements** arrive each wave on top of what you train.

## Win / lose
- **Win**: destroy **all enemy Castles** (at any time) → victory.
- **Finale assist**: clearing wave 12 stops enemy spawns and grants a **siege battalion**, guaranteeing
  a shot at the final assault even if you turtled.
- **Lose**: all 4 of your Castles destroyed → defeat.

## Difficulty (post-v1)
Difficulty tiers scale wave size/composition, bounty size, reinforcement count, and enemy-fortress
toughness — implemented as alternate `config/` profiles rather than code branches.

## Stretch goals (post-v1)
- **Co-op** for 2–4 players (shared or individual castle bases).
- **Endless mode** with score = waves survived.
- **Boss waves** (unique tanky units) every few rounds.
- **Map variants** (chokepoints, multiple spawn lanes).
- **Mutators** (e.g., "no ranged", "double siege").

## Open design questions (let's debate these in issues)
- How tanky should the enemy fortress be — how *tempting* vs *punishing* is the rush?
- Per-kill income vs bounty-only — do we want kill-based rewards later?
- Should reinforcements stay free, or should the finale siege grant scale with how fast you cleared?
- How generous should the economy + starting stipend be, and how big is the finale siege battalion?
- One shared castle base vs one per player in co-op?
- Finite 12 waves, or "12 then endless"?
