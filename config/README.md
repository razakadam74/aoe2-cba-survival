# config/ — wave & balance data

**The easiest place to contribute — no coding required.** Editing these files changes the game;
the generator reads them at build time.

**Status:** schema is defined in M1/M2. Planned files (**YAML**):
- `waves.yaml` — per-wave unit composition, counts, and spawn timing.
- `balance.yaml` — starting stipend, wave-clear bounty, trickle rate, reinforcements, enemy-fortress toughness.
- `difficulty.yaml` — (post-v1) alternate profiles.

Keep values readable and commented. After editing, rebuild + playtest (see
[../CONTRIBUTING.md](../CONTRIBUTING.md)).
