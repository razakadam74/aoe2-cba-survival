# CBA Survival — Game Design

> Status: **v1 spec locked** for the first playable milestone. Stretch ideas are marked *post-v1*.

## Vision
A **PvE survival** scenario for Age of Empires II: Definitive Edition, inspired by the community's
beloved **CBA (Castle Blood Automatic)** scenarios — *Castle* (you defend a cluster of castles),
*Blood* (constant, never-ending combat), *Automatic* (the enemy army spawns on its own).

You defend a base of **4 Castles** against an **endless** stream of escalating waves from an **enemy
fortress**. The onslaught *never stops* — the only way out is to **raze the enemy's castles**. So you
must **defend and push at the same time**: hold the line while carving out enough of an army to break
their fortress. Imperial-Age start, full army freedom, classic-CBA economy. Solo-testable first,
co-op later.

## Core loop
1. **Hold** — waves pour out of the enemy fortress and march on your Castles. Keep them off.
2. **Earn** — every kill pays gold; a periodic drip tops you up.
3. **Reinforce, upgrade & push** — train any army, research upgrades, and **build army buildings
   forward** (production nearer the enemy) to stage your assault.
4. **Break out** — you can't outlast the waves (they never stop), so at some point you *must* march on
   the enemy fortress and **raze its castles** — the only win. Every soldier attacking is one not
   defending: that's the gamble.

## v1 spec (locked)
| Aspect | Decision |
|---|---|
| Players | 1 human (Player 1) vs a hostile **enemy fortress** (Player 2). P2 is *not* a mirror army — it's castles + an endless wave spawner, so the mode stays solo-testable. |
| Objective | **Raze all enemy Castles.** |
| Waves | **Endless.** Difficulty escalates to a peak around **wave 12**, then keeps coming at full intensity. They never stop. |
| Win | Destroy **all enemy Castles** — the only win. |
| Lose | All 4 of your Castles destroyed. |
| Fight-back | **Hybrid**: starting army + small auto-reinforcements + train/upgrade with earned resources; **build your own siege** to crack castles. |
| Economy | Income from **kills + periodic gold** (little/no gathering) + a starting stipend. Spend on army *and* forward buildings. |
| Map | Small flat **two-base arena** (your castles ↔ battlefield ↔ enemy fortress). Polished later in the in-game editor. |
| Config | Wave & balance data in **YAML** (`config/`), tunable without touching code. |

## Enemy fortress & the only win
Player 2 is deliberately **asymmetric**: no micro-managed enemy army — just a fortress of castles that
**spawns endless escalating waves** and **defends itself** (its castles fire arrows at attackers). This
keeps the mode solo-testable while giving you a target to break.

**There is no "survive to win."** The waves never stop, so survival is the *pressure*, not a victory
condition. The **only win is razing every enemy Castle** — and the tension is that you must do it while
your own 4 castles are still under attack. Turtle too long and the escalation grinds you down; over-commit
to the attack and your base falls behind you. Timing your break-out is the whole game.

You crack castles with **siege you build yourself** (Rams / Trebuchets / Bombards from your Siege
Workshop and Castle) — that's why you get full army freedom and a generous-enough economy.

## Wave escalation model
- Waves spawn **continuously** from the enemy fortress on a timer — relentless, classic-CBA style.
- **Composition** escalates as waves climb, tier by tier:
  - Early: light infantry (Militia / Spearman).
  - Then ranged (Archers / Skirmishers).
  - Then cavalry (Scouts / Knights) + heavier infantry.
  - Then **siege** (Rams / Mangonels) — dangerous to your castles.
- Difficulty **ramps to a peak around wave 12**, then continues **at peak intensity indefinitely**
  (it plateaus so a break-out stays possible, but it never eases off).
- All sizes, timing, and the escalation cap live in **`config/`** so they can be tuned without code.

## Your forces & economy
- **Full army freedom** — Imperial-Age start, train any composition, including the **siege** you need
  to raze castles.
- **Villagers to build forward and push.** A classic CBA skill: throw down a Barracks/Range/Stable (or a
  forward **Castle**) closer to the enemy, wall a chokepoint, or expand.
- **Where villagers come from:** no Town Center — you **train villagers from your Castle**, but they're
  **expensive** (a deliberate gold investment), so you buy a builder to push, not to boom. Enabled in DE
  with the `add_train_location` + `change_object_cost` trigger effects (a scenario trick, no data mod).
- **Income from kills + periodic gold** (classic-CBA, little/no gathering) + a **starting stipend**.
  Villagers **build**, they do not need to gather. Spend income on both **army** and **forward buildings**.
- **Population** headroom via Houses; small **auto-reinforcements** arrive periodically on top of what
  you train.

## Win / lose
- **Win**: destroy **all enemy Castles** → victory. (Active from the start — break out whenever you can.)
- **Lose**: all 4 of your Castles destroyed → defeat.
- **No survive-to-win**: the waves never stop; razing the enemy is the only way out.

## Difficulty (post-v1)
Difficulty tiers scale wave size/composition, spawn rate, the escalation cap, and enemy-fortress
toughness — implemented as alternate `config/` profiles rather than code branches.

## Stretch goals (post-v1)
- **Co-op** for 2–4 players (shared or individual castle bases).
- **Scoring / leaderboards** — fastest raze, or longest hold.
- **Boss waves** (unique tanky units) at intervals.
- **Map variants** (chokepoints, multiple spawn lanes).
- **Mutators** (e.g., "no ranged", "double siege").

## Open design questions (let's debate these in issues)
- How tanky should the enemy fortress be — how *tempting* vs *punishing* is the break-out?
- Where should the escalation plateau (wave ~12?) so a raze stays possible but the heat never drops?
- How much gold per kill + periodic drip (and starting stipend)?
- How expensive should Castle-trained villagers be, and how many do you start with?
- Any resource nodes on the map for optional gathering, or pure kill + periodic income?
- One shared castle base vs one per player in co-op?
