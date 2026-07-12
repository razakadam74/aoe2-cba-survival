"""CBA Survival - code-generated AoE2 DE survival scenario.

Importing this package silences AoE2ScenarioParser's status prints (which
otherwise emit emoji that crash the Windows cp1252 console).
"""
from __future__ import annotations

from AoE2ScenarioParser import settings as _settings

# Keep generator output clean and Windows-safe.
_settings.PRINT_STATUS_UPDATES = False

__all__ = ["config", "builder", "layout", "players", "placement", "triggers", "datasets"]
