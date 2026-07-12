"""Player configuration: activate players, set age, stipend, and diplomacy.

Defenders are Players 1..N (allied, allied-victory, human seats). The enemy
fortress is the next slot, Player N+1 (AI now, human-swappable later). The
engine requires active players to be contiguous from Player 1, so the enemy
sits directly after the defenders: solo -> Player 2, full 7v1 -> Player 8.
"""
from __future__ import annotations

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from .config import BalanceConfig, ModConfig
from .datasets import DiplomacyState, resolve_starting_age


def enemy_player_id(balance: BalanceConfig) -> int:
    """The enemy fortress slot: the player right after the last defender."""
    return balance.defenders + 1


def configure_players(scenario: AoE2DEScenario, config: ModConfig) -> None:
    balance = config.balance
    manager = scenario.player_manager
    age = resolve_starting_age(balance.starting_age)
    defender_ids = list(range(1, balance.defenders + 1))
    enemy_id = enemy_player_id(balance)

    # Activate Players 1..enemy_id (contiguous, as the engine requires).
    manager.active_players = enemy_id

    for pid in defender_ids:
        player = manager.players[pid]
        player.human = True  # defenders are player-controlled seats
        player.starting_age = age
        player.food = balance.stipend.get("food", 0)
        player.wood = balance.stipend.get("wood", 0)
        player.gold = balance.stipend.get("gold", 0)
        player.stone = balance.stipend.get("stone", 0)
        player.population_cap = balance.population_cap
        player.allied_victory = True

    enemy = manager.players[enemy_id]
    enemy.human = False
    enemy.starting_age = age
    enemy.population_cap = balance.population_cap

    _set_diplomacy(manager, defender_ids, enemy_id)


def _set_diplomacy(manager, defender_ids: list[int], enemy_id: int) -> None:
    # Defenders allied with each other (one team). set_diplomacy_teams takes a
    # list PER team, so pass the list itself - do not unpack it.
    if len(defender_ids) > 1:
        manager.set_diplomacy_teams(defender_ids, diplomacy=DiplomacyState.ALLY)
    # Everyone at war with the enemy fortress, both directions.
    for pid in defender_ids:
        manager.players[pid].set_player_diplomacy(enemy_id, DiplomacyState.ENEMY)
    manager.players[enemy_id].set_player_diplomacy(defender_ids, DiplomacyState.ENEMY)


__all__ = ["configure_players", "enemy_player_id"]
