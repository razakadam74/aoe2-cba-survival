# mod/ — build output (generated)

This folder holds the **deployable mod**, produced by `scripts/build.py`. It's **git-ignored**
(the source of truth is `config/` + `src/`), so don't hand-edit it.

After a build it contains:
```
mod/<id>_CBA Survival/
├─ info.json          # {Author, Title, Description, CacheStatus}
└─ resources/_common/scenario/CBA Survival.aoe2scenario
```
Copy that folder into your local AoE2 mods folder (or run `scripts/deploy.py`), then enable it
in-game under **Mods → Local**.
