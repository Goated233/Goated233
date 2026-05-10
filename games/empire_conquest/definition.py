from engines.base.types import EngineType, GameDefinition, RewardRule

EMPIRE_CONQUEST = GameDefinition(
    id="empire_conquest",
    name="Empire Conquest",
    description="Territory strategy with alliances, resource generation, attacks, and seasonal map control.",
    engine_type=EngineType.STRATEGY,
    category="Strategy",
    min_players=2,
    max_players=50,
    estimated_minutes=30,
    reward_rule=RewardRule(base_xp=260, base_coins=200, win_multiplier=1.4),
    config={"resources": ["gold", "stone", "food"], "alliances": True, "territory_grid": "seasonal"},
)
