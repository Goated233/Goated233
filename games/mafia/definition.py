from engines.base.types import EngineType, GameDefinition, RewardRule

MAFIA = GameDefinition(
    id="mafia",
    name="Mafia",
    description="Social deduction with roles, private prompts, voting, reconnect handling, and day/night phases.",
    engine_type=EngineType.SOCIAL_DEDUCTION,
    category="Social Deduction",
    min_players=5,
    max_players=16,
    estimated_minutes=20,
    reward_rule=RewardRule(base_xp=180, base_coins=120, win_multiplier=1.35),
    config={"roles": ["Mafia", "Detective", "Doctor", "Villager"], "phases": ["night", "day", "vote"]},
)
