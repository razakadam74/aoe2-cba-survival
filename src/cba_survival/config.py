"""Load and validate CBA Survival config (balance.yaml + waves.yaml).

Splitting ``parse_config`` (pure dict -> dataclasses) from ``load_config``
(file IO) keeps validation unit-testable without touching disk.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from .datasets import (
    ConfigError,
    resolve_building_id,
    resolve_object_id,
    resolve_starting_age,
)

RESOURCE_KEYS = ("food", "wood", "gold", "stone")
MAX_DEFENDERS = 7
MIN_MAP_SIZE = 60
MAX_MAP_SIZE = 480


@dataclass(frozen=True)
class UnitStack:
    """A count of one unit type, e.g. 6 Man-at-Arms."""

    name: str
    count: int

    @property
    def unit_id(self) -> int:
        return resolve_object_id(self.name)


@dataclass(frozen=True)
class Wave:
    name: str
    delay_seconds: int
    units: tuple[UnitStack, ...]


@dataclass(frozen=True)
class PeakWave:
    name: str
    interval_seconds: int
    units: tuple[UnitStack, ...]


@dataclass(frozen=True)
class WaveConfig:
    max_concurrent: int
    escalation_cap_wave: int
    waves: tuple[Wave, ...]
    peak: PeakWave


@dataclass(frozen=True)
class ModMeta:
    title: str
    author: str
    description: str


@dataclass(frozen=True)
class KillIncome:
    """Gold earned per block of enemy kills (classic-CBA economy, M2)."""

    reward_gold: int
    per_kills: int

    @property
    def enabled(self) -> bool:
        return self.reward_gold > 0 and self.per_kills > 0


@dataclass(frozen=True)
class Reinforcements:
    """A small squad that arrives at each base on a timer (M2)."""

    interval_seconds: int
    units: tuple[UnitStack, ...]

    @property
    def enabled(self) -> bool:
        return bool(self.units)


@dataclass(frozen=True)
class BalanceConfig:
    mod: ModMeta
    defenders: int
    map_size: int
    starting_age: str
    stipend: Mapping[str, int]
    population_cap: int
    starting_villagers: int
    villager_cost: Mapping[str, int]
    villager_train_time: int
    starting_army: tuple[UnitStack, ...]
    production_buildings: tuple[str, ...]
    houses: int
    periodic_gold: Mapping[str, int]
    kill_income: KillIncome
    reinforcements: Reinforcements
    enemy_castles: int

    @property
    def army_size(self) -> int:
        return sum(s.count for s in self.starting_army)


@dataclass(frozen=True)
class ModConfig:
    balance: BalanceConfig
    waves: WaveConfig


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def load_config(config_dir: str | Path) -> ModConfig:
    """Read ``balance.yaml`` and ``waves.yaml`` from *config_dir*."""
    config_dir = Path(config_dir)
    balance = _read_yaml(config_dir / "balance.yaml")
    waves = _read_yaml(config_dir / "waves.yaml")
    return parse_config(balance, waves)


def parse_config(balance: Mapping[str, Any], waves: Mapping[str, Any]) -> ModConfig:
    """Validate raw dicts and build the typed :class:`ModConfig`."""
    return ModConfig(balance=_parse_balance(balance), waves=_parse_waves(waves))


# --------------------------------------------------------------------------- #
# Balance parsing
# --------------------------------------------------------------------------- #
def _parse_balance(data: Mapping[str, Any]) -> BalanceConfig:
    _require(isinstance(data, Mapping), "balance.yaml must be a mapping")

    defenders = _int(data, "defenders", minimum=1, maximum=MAX_DEFENDERS)
    map_size = _int(data, "map_size", minimum=MIN_MAP_SIZE, maximum=MAX_MAP_SIZE)

    starting_age = _str(data, "starting_age")
    resolve_starting_age(starting_age)  # raises ConfigError if unknown

    mod = _parse_mod(data.get("mod", {}))
    stipend = _resources(data.get("stipend", {}), "stipend")
    villager_cost = _resources(data.get("villager_cost", {}), "villager_cost")
    # A unit has only three cost slots (resource_1..3 on change_object_cost).
    _require(len(villager_cost) <= 3, "villager_cost may set at most 3 resources")
    _require("periodic_gold" in data, "balance.yaml is missing the 'periodic_gold' block")
    periodic_gold = _parse_periodic_gold(data["periodic_gold"])
    kill_income = _parse_kill_income(data.get("kill_income", {}))
    reinforcements = _parse_reinforcements(data.get("reinforcements", {}))

    army = _parse_stacks(data.get("starting_army", []), "starting_army", allow_empty=True)

    production = tuple(str(b) for b in data.get("production_buildings", []))
    for name in production:
        resolve_building_id(name)  # raises if not a building

    enemy = data.get("enemy", {})
    _require(isinstance(enemy, Mapping), "enemy must be a mapping")
    enemy_castles = _int(enemy, "castles", minimum=1, maximum=50)

    return BalanceConfig(
        mod=mod,
        defenders=defenders,
        map_size=map_size,
        starting_age=starting_age,
        stipend=stipend,
        population_cap=_int(data, "population_cap", minimum=1, maximum=1000),
        starting_villagers=_int(data, "starting_villagers", minimum=0, maximum=200),
        villager_cost=villager_cost,
        villager_train_time=_int(data, "villager_train_time", minimum=1, maximum=600),
        starting_army=army,
        production_buildings=production,
        houses=_int(data, "houses", minimum=0, maximum=200),
        periodic_gold=periodic_gold,
        kill_income=kill_income,
        reinforcements=reinforcements,
        enemy_castles=enemy_castles,
    )


def _parse_kill_income(data: Mapping[str, Any]) -> KillIncome:
    _require(isinstance(data, Mapping), "kill_income must be a mapping")
    return KillIncome(
        reward_gold=_int(data, "reward_gold", minimum=0, maximum=100000, default=0),
        per_kills=_int(data, "per_kills", minimum=1, maximum=100000, default=1),
    )


def _parse_reinforcements(data: Mapping[str, Any]) -> Reinforcements:
    _require(isinstance(data, Mapping), "reinforcements must be a mapping")
    return Reinforcements(
        interval_seconds=_int(data, "interval_seconds", minimum=1, maximum=3600, default=60),
        units=_parse_stacks(data.get("units", []), "reinforcements units", allow_empty=True),
    )


def _parse_mod(data: Mapping[str, Any]) -> ModMeta:
    _require(isinstance(data, Mapping), "mod must be a mapping")
    title = str(data.get("title", "CBA Survival")).strip() or "CBA Survival"
    # The title becomes a folder name in build_mod() and deploy.py (which rmtree's
    # the target), so it must be a single safe path component - no separators or "..".
    _require(
        title == Path(title).name and title not in ("..", ".") and not _has_path_chars(title),
        f"mod.title must be a safe folder name (no path separators or '..'), got {title!r}",
    )
    return ModMeta(
        title=title,
        author=str(data.get("author", "unknown")).strip() or "unknown",
        description=str(data.get("description", "")).strip(),
    )


def _has_path_chars(name: str) -> bool:
    return any(ch in name for ch in '/\\:*?"<>|')


def _parse_periodic_gold(data: Mapping[str, Any]) -> dict[str, int]:
    _require(isinstance(data, Mapping), "periodic_gold must be a mapping")
    return {
        "amount": _int(data, "amount", minimum=0, maximum=100000),
        "interval_seconds": _int(data, "interval_seconds", minimum=1, maximum=3600),
    }


# --------------------------------------------------------------------------- #
# Waves parsing
# --------------------------------------------------------------------------- #
def _parse_waves(data: Mapping[str, Any]) -> WaveConfig:
    _require(isinstance(data, Mapping), "waves.yaml must be a mapping")

    raw_waves = data.get("waves", [])
    _require(isinstance(raw_waves, Sequence), "waves must be a list")
    waves: list[Wave] = []
    for i, entry in enumerate(raw_waves, start=1):
        _require(isinstance(entry, Mapping), f"wave #{i} must be a mapping")
        waves.append(
            Wave(
                name=str(entry.get("name", f"Wave {i}")),
                delay_seconds=_int(entry, "delay_seconds", minimum=0, maximum=3600),
                units=_parse_stacks(entry.get("units", []), f"wave #{i} units"),
            )
        )

    peak_raw = data.get("peak")
    _require(isinstance(peak_raw, Mapping), "waves.yaml needs a 'peak' mapping (the endless loop)")
    peak = PeakWave(
        name=str(peak_raw.get("name", "Endless assault")),
        interval_seconds=_int(peak_raw, "interval_seconds", minimum=1, maximum=3600),
        units=_parse_stacks(peak_raw.get("units", []), "peak units"),
    )

    max_concurrent = _int(data, "max_concurrent", minimum=1, maximum=5000, default=200)
    # Enforce the performance guardrail: no single wave (or the peak) may spawn
    # more live units than max_concurrent.
    for wave in waves:
        total = sum(stack.count for stack in wave.units)
        _require(
            total <= max_concurrent,
            f"wave {wave.name!r} spawns {total} units, exceeding max_concurrent ({max_concurrent})",
        )
    peak_total = sum(stack.count for stack in peak.units)
    _require(
        peak_total <= max_concurrent,
        f"peak {peak.name!r} spawns {peak_total} units, exceeding max_concurrent ({max_concurrent})",
    )

    return WaveConfig(
        max_concurrent=max_concurrent,
        escalation_cap_wave=_int(data, "escalation_cap_wave", minimum=1, maximum=1000, default=12),
        waves=tuple(waves),
        peak=peak,
    )


# --------------------------------------------------------------------------- #
# Small validation helpers
# --------------------------------------------------------------------------- #
def _parse_stacks(raw: Any, label: str, allow_empty: bool = False) -> tuple[UnitStack, ...]:
    _require(isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)), f"{label} must be a list")
    stacks: list[UnitStack] = []
    for entry in raw:
        _require(isinstance(entry, Mapping), f"{label}: each entry must be a mapping with 'unit' and 'count'")
        name = _str(entry, "unit")
        resolve_object_id(name)  # raises ConfigError on unknown unit
        count = _int(entry, "count", minimum=1, maximum=1000)
        stacks.append(UnitStack(name=name, count=count))
    _require(allow_empty or stacks, f"{label} must not be empty")
    return tuple(stacks)


def _resources(data: Any, label: str) -> dict[str, int]:
    _require(isinstance(data, Mapping), f"{label} must be a mapping")
    out: dict[str, int] = {}
    for key, value in data.items():
        _require(key in RESOURCE_KEYS, f"{label}: unknown resource {key!r} (use {', '.join(RESOURCE_KEYS)})")
        _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0,
                 f"{label}.{key} must be a non-negative integer")
        out[key] = value
    return out


def _int(data: Mapping[str, Any], key: str, *, minimum: int, maximum: int, default: int | None = None) -> int:
    if key not in data:
        if default is not None:
            return default
        raise ConfigError(f"Missing required integer field: {key!r}")
    value = data[key]
    _require(isinstance(value, int) and not isinstance(value, bool), f"{key} must be an integer, got {value!r}")
    _require(minimum <= value <= maximum, f"{key} must be between {minimum} and {maximum}, got {value}")
    return value


def _str(data: Mapping[str, Any], key: str) -> str:
    _require(key in data, f"Missing required field: {key!r}")
    value = data[key]
    _require(isinstance(value, str) and value.strip(), f"{key} must be a non-empty string")
    return value.strip()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConfigError(message)


def _read_yaml(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    _require(isinstance(data, Mapping), f"{path.name} must contain a top-level mapping")
    return data


__all__ = [
    "BalanceConfig",
    "KillIncome",
    "ModConfig",
    "ModMeta",
    "PeakWave",
    "Reinforcements",
    "UnitStack",
    "Wave",
    "WaveConfig",
    "load_config",
    "parse_config",
]
