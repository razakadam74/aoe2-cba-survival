# tests/ — validation

**Status:** starts in M1. Planned:
- **Round-trip**: generate → `write_to_file` → `from_file` → assert expected triggers/units exist.
- **Config validation**: wave/balance files parse and stay within sane bounds.

> Note: we can validate the *file*, not the *gameplay*. Playtesting is human — report via issues.

Run: `python -m pytest`
