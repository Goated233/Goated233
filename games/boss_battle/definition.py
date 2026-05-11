from engines.base.types import EngineType, GameDefinition, RewardRule

BOSS_BATTLE = GameDefinition(
    id="boss_battle",
    name="Boss Battle",
    description="Global timed raids with server-wide boss spawns, damage leaderboards, and reward tiers.",
    engine_type=EngineType.BATTLE,
    category="Global Raid",
    min_players=1,
    max_players=100,
    estimated_minutes=15,
    reward_rule=RewardRule(base_xp=220, base_coins=150, win_multiplier=1.5),
    config={"global": True, "damage_leaderboard": True, "timed_seconds": 900},
)
