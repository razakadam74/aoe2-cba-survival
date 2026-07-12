"""Arena geometry: where every castle, building, unit, and spawn lives.

All coordinates are tile positions on a square map. Defenders occupy the
south edge (one base each, spread along x); the enemy fortress sits on the
north edge. Waves spawn just south of the fortress and attack-move toward the
defenders. Everything here is deterministic (same config -> same coordinates).
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from .config import BalanceConfig

# Spacing between object centres (tiles). Generous enough to avoid overlap.
_CASTLE_STEP = 8
_PRODUCTION_STEP = 6
_HOUSE_STEP = 3
_ARMY_STEP = 2
_VILLAGER_STEP = 2
_SPAWN_STEP = 2

# Vertical bands within a defender base, measured north (toward the enemy)
# from the base's back row of castles.
_BAND_PRODUCTION = 18
_BAND_HOUSES = 30
_BAND_ARMY = 36

_EDGE_MARGIN = 12
_BASE_BACK_Y = 12  # south row of a defender base


@dataclass(frozen=True)
class DefenderBase:
    player_id: int
    castles: tuple[tuple[int, int], ...]
    production: tuple[tuple[int, int], ...]
    houses: tuple[tuple[int, int], ...]
    army: tuple[tuple[int, int], ...]
    villagers: tuple[tuple[int, int], ...]
    rally: tuple[int, int]
    reinforce: tuple[int, int]


@dataclass(frozen=True)
class EnemyLayout:
    castles: tuple[tuple[int, int], ...]
    spawn: tuple[int, int]
    spawn_area: tuple[int, int, int, int]  # x1, y1, x2, y2


@dataclass(frozen=True)
class Layout:
    map_size: int
    defenders: tuple[DefenderBase, ...]
    enemy: EnemyLayout
    defender_centroid: tuple[int, int]


def compute_layout(balance: BalanceConfig) -> Layout:
    """Build the full coordinate plan from *balance*."""
    size = balance.map_size
    enemy = _enemy_layout(size, balance.enemy_castles)

    bases: list[DefenderBase] = []
    n = balance.defenders
    usable = size - 2 * _EDGE_MARGIN
    step = usable // n
    for i in range(n):
        cx = _clamp(_EDGE_MARGIN + step * i + step // 2, size)
        bases.append(_defender_base(i + 1, cx, size, balance))

    cx = sum(b.rally[0] for b in bases) // len(bases)
    cy = sum(b.rally[1] for b in bases) // len(bases)
    return Layout(map_size=size, defenders=tuple(bases), enemy=enemy, defender_centroid=(cx, cy))


def _enemy_layout(size: int, castle_count: int) -> EnemyLayout:
    cx = size // 2
    cy = size - _EDGE_MARGIN
    castles = tuple(_centered_row(cx, cy, castle_count, _CASTLE_STEP, size))
    spawn = (cx, _clamp(cy - 10, size))
    half = 9
    area = (
        _clamp(spawn[0] - half, size),
        _clamp(spawn[1] - half, size),
        _clamp(spawn[0] + half, size),
        _clamp(spawn[1] + half, size),
    )
    return EnemyLayout(castles=castles, spawn=spawn, spawn_area=area)


def _defender_base(player_id: int, cx: int, size: int, balance: BalanceConfig) -> DefenderBase:
    back_y = _BASE_BACK_Y

    # Four castles in a 2x2 cluster at the back of the base.
    castles = (
        (_clamp(cx - 4, size), _clamp(back_y, size)),
        (_clamp(cx + 4, size), _clamp(back_y, size)),
        (_clamp(cx - 4, size), _clamp(back_y + _CASTLE_STEP, size)),
        (_clamp(cx + 4, size), _clamp(back_y + _CASTLE_STEP, size)),
    )
    rally = (_clamp(cx, size), _clamp(back_y + 4, size))

    production = _centered_grid(
        cx, back_y + _BAND_PRODUCTION, len(balance.production_buildings), cols=4, dx=_PRODUCTION_STEP, dy=_PRODUCTION_STEP, size=size
    )
    houses = _centered_grid(
        cx, back_y + _BAND_HOUSES, balance.houses, cols=6, dx=_HOUSE_STEP, dy=_HOUSE_STEP, size=size
    )
    army = _centered_grid(
        cx, back_y + _BAND_ARMY, balance.army_size, cols=8, dx=_ARMY_STEP, dy=_ARMY_STEP, size=size
    )
    villagers = _centered_grid(
        _clamp(cx - 12, size), back_y, balance.starting_villagers, cols=2, dx=_VILLAGER_STEP, dy=_VILLAGER_STEP, size=size
    )
    # Reinforcements arrive on open ground just in front of the army band.
    reinforce = (_clamp(cx, size), _clamp(back_y + _BAND_ARMY + 6, size))
    return DefenderBase(
        player_id=player_id,
        castles=castles,
        production=production,
        houses=houses,
        army=army,
        villagers=villagers,
        rally=rally,
        reinforce=reinforce,
    )


def spawn_positions(spawn: tuple[int, int], total: int, size: int) -> list[tuple[int, int]]:
    """Grid of spawn tiles around *spawn* for *total* units (kept inside the spawn area)."""
    return _centered_grid(spawn[0], spawn[1] - 6, total, cols=8, dx=_SPAWN_STEP, dy=_SPAWN_STEP, size=size)


def squad_positions(center: tuple[int, int], total: int, size: int) -> list[tuple[int, int]]:
    """Grid of tiles centred on *center* for a reinforcement squad of *total* units."""
    return list(_centered_grid(center[0], center[1], total, cols=6, dx=_ARMY_STEP, dy=_ARMY_STEP, size=size))


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #
def _centered_row(cx: int, y: int, n: int, dx: int, size: int) -> list[tuple[int, int]]:
    if n <= 0:
        return []
    start = cx - dx * (n - 1) // 2
    return [(_clamp(start + i * dx, size), _clamp(y, size)) for i in range(n)]


def _centered_grid(cx: int, y: int, n: int, cols: int, dx: int, dy: int, size: int) -> tuple[tuple[int, int], ...]:
    if n <= 0:
        return ()
    points: list[tuple[int, int]] = []
    rows = ceil(n / cols)
    for i in range(n):
        r, c = divmod(i, cols)
        in_row = min(cols, n - r * cols)
        start = cx - dx * (in_row - 1) // 2
        points.append((_clamp(start + c * dx, size), _clamp(y + r * dy, size)))
    del rows
    return tuple(points)


def _clamp(value: int, size: int) -> int:
    return max(2, min(size - 3, value))


__all__ = ["DefenderBase", "EnemyLayout", "Layout", "compute_layout", "spawn_positions", "squad_positions"]
