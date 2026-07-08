# Contributing to CBA Survival

Thanks for helping! This project turns a data-driven config into an AoE2 DE survival scenario.
You **don't** need to be a programmer to contribute — *wave and balance tuning is just editing data.*

## Ways to contribute
| I want to… | Where | Coding? |
|---|---|---|
| Design / tune waves & balance | `config/` | ❌ No |
| Improve the generator | `src/` | ✅ Python |
| Fix build / deploy | `scripts/` | ✅ Python |
| Improve docs | `docs/`, `*.md` | ❌ No |
| Report bugs / playtest feedback | Issues | ❌ No |

## Dev setup
1. Install Python 3.10+.
2. `pip install AoE2ScenarioParser PyYAML`
3. Windows: run Python with UTF-8 enabled — `set PYTHONUTF8=1`
   (avoids a console emoji crash inside the library).

## Build & test (available from M1)
```
python scripts/build.py      # config + src  ->  mod/ output
python scripts/deploy.py     # copy mod/ into your local AoE2 mods folder
python -m pytest             # round-trip & config-validation tests
```

## Contributing a wave / balance change (no code)
1. Edit the relevant file in `config/`.
2. Rebuild and deploy (commands above).
3. Playtest in AoE2 DE.
4. Open a PR describing what you changed and how it played.

## Pull request process
1. Fork, then branch (e.g., `wave/harder-siege` or `feat/endless-mode`).
2. Keep generation **deterministic** (same config → same scenario).
3. Python: PEP 8 + type hints where practical.
4. Update docs if behavior changes.
5. Fill in the PR template checklist.

### Review gate (project convention)
Before a PR is opened/merged it goes through a **multi-model AI review (4 models)**, and the
feedback is synthesized into the PR. This catches bugs and design issues early. (Maintainer
workflow — noted here so contributors know what to expect.)

## Reporting bugs / playtests
Open an issue with: what you did, what happened, what you expected, and — for gameplay — which
wave and how it felt. Screenshots/clips welcome.

## Be kind
Assume good faith, keep it friendly, and remember most of us are here because we love AoE2.
