"""Guard: no em-dashes, en-dashes, or Unicode minus anywhere in the source.

Project hard rule: use plain ASCII hyphens only. This test fails loudly if a
fancy dash sneaks into config, code, docs, or scripts.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BANNED = {"\u2014": "em-dash", "\u2013": "en-dash", "\u2212": "unicode-minus"}
TEXT_SUFFIXES = {".py", ".yaml", ".yml", ".md", ".json", ".toml", ".txt", ".cfg", ".ini"}
SKIP_DIRS = {".git", "mod", ".pytest_cache", "__pycache__", ".mypy_cache", ".venv"}


def _text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        yield path


def test_no_fancy_dashes():
    offenders = []
    for path in _text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for char, label in BANNED.items():
            if char in text:
                line = next(i for i, ln in enumerate(text.splitlines(), 1) if char in ln)
                offenders.append(f"{path.relative_to(ROOT)}:{line} contains {label}")
    assert not offenders, "Fancy dashes found (use ASCII hyphens):\n" + "\n".join(offenders)
