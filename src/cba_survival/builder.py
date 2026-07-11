"""Top-level assembly: config -> scenario -> deployable mod folder."""
from __future__ import annotations

import json
from pathlib import Path

from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from .config import ModConfig, load_config
from .layout import compute_layout
from .placement import configure_map, place_all
from .players import configure_players
from .triggers import build_triggers


def build_scenario(config: ModConfig) -> AoE2DEScenario:
    """Assemble a complete in-memory scenario from *config* (deterministic)."""
    scenario = AoE2DEScenario.from_default()
    scenario.name = config.balance.mod.title

    layout = compute_layout(config.balance)
    configure_map(scenario, config.balance.map_size)
    place_all(scenario, config, layout)
    configure_players(scenario, config)
    build_triggers(scenario, config, layout)
    return scenario


def build_mod(config: ModConfig, output_dir: str | Path) -> Path:
    """Write the deployable mod folder and return its path."""
    scenario = build_scenario(config)
    title = config.balance.mod.title

    mod_folder = Path(output_dir) / title
    scenario_dir = mod_folder / "resources" / "_common" / "scenario"
    scenario_dir.mkdir(parents=True, exist_ok=True)

    scenario_path = scenario_dir / f"{title}.aoe2scenario"
    scenario.write_to_file(str(scenario_path))

    info = {
        "Author": config.balance.mod.author,
        "Title": title,
        "Description": config.balance.mod.description,
        "CacheStatus": 0,
    }
    (mod_folder / "info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return mod_folder


def build_from_config_dir(config_dir: str | Path, output_dir: str | Path) -> Path:
    """Convenience: load config from *config_dir* and build into *output_dir*."""
    return build_mod(load_config(config_dir), output_dir)


__all__ = ["build_scenario", "build_mod", "build_from_config_dir"]
