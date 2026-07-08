# CBA Survival — Game Design

> Status: **v1 spec locked** for the first playable milestone. Stretch ideas are marked *post-v1*.

## Vision
A **PvE survival** scenario for Age of Empires II: Definitive Edition, inspired by the community's
beloved **CBA (Castle Blood Automatic)** scenarios — *Castle* (you defend a cluster of castles),
*Blood* (constant combat, no economy-building), *Automatic* (your army spawns on its own).

You defend a base of **4 Castles** against escalating waves launched from an **enemy fortress**.
You don't gather an economy from scratch — you fight, reinforce, and upgrade off the spoils of war.
**Two ways to win:** outlast every wave, *or* break out and raze the enemy's castles. Designed to be
**solo-testable** first, **co-op** later.

## Core loop
1. **Prepare** — a brief calm before wave 1 (position your army, queue upgrades).
2. **Survive a wave** — enemies pour out of the enemy fortress and march on your Castles. Fight them off.
3. **Reap** — clearing a wave pays a resource **bounty**; a slow **trickle** also drips in.
4. **Reinforce & upgrade** — spend resources at your buildings via the **native tech tree**
   (Forging, Fletching, unit-line upgrades…); small auto-reinforcements arrive each wave.
5. **Escalate** — each wave is bigger and nastier. Repeat until you win or your last Castle falls.

**Alternate path — go on the offense.** At any time you can march on the **enemy fortress** and try
to destroy its castles for an instant win. But every soldier attacking is one not defending, and the
enemy castles shoot back — a deliberate risk/reward race.

## v1 spec (locked)
| Aspect | Decision |
|---|---|
| Players | 1 human (Player 1) vs a hostile **enemy fortress** (Player 2). P2 is *not* a mirror army — it's castles + a wave spawner, so the mode stays solo-testable. |
| Objective | Defend your **4 Castles**. |
| Enemy | An **enemy fortress** (its own castles) that launches the waves and can itself be attacked. |
| Waves | **12**, finite, escalating. |
| Fight-back | **Hybrid**: starting army + small auto-reinforcements each wave + train/upgrade with earned resources. |
| Economy | Wave-clear **bounty** + steady **trickle**. Upgrades via the **native tech tree** (no custom shop). |
| Win | Survive all 12 waves **or** destroy all enemy Castles. |
| Lose | All 4 of your Castles destroyed. |
| Map | Small flat **two-base arena** (your castles ↔ battlefield ↔ enemy fortress). Chokepoints & looks polished later in the in-game editor. |
| Config | Wave & balance data in **YAML** (`config/`), so anyone can tune it without touching code. |

## Enemy fortress & win paths
Player 2 is deliberately **asymmetric**: no micro-managed enemy army, just a fortress of castles that
**spawns the timed waves** and **defends itself** (its castles fire arrows at attackers). This keeps
the mode solo-testable while still giving you a target to break.

- **Defensive win** — clear all 12 waves.
- **Offensive win** — raze every enemy Castle, at any point.
- The two paths create real strategy: **turtle**, **all-in rush**, or a **hybrid** timing push — while
  remembering that attackers aren't home defending your own castles.

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

## Economy model
- **Starting stipend** so you can act immediately.
- **Wave-clear bounty**: clearing wave N grants a resource lump (scales with N).
- **Trickle**: small passive income so training feels continuous.
- **Population** headroom via Houses so you can actually train reinforcements.

## Win / lose
- **Win (defensive)**: clear wave 12 → victory.
- **Win (offensive)**: destroy all enemy Castles → victory.
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
- Should reinforcements be free or purchasable?
- One shared castle base vs one per player in co-op?
- Finite 12 waves, or "12 then endless"?
