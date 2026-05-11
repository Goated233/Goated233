from engines.base.types import EngineType, GameDefinition, RewardRule

BLACKJACK = GameDefinition(
    id="blackjack",
    name="Blackjack",
    description="Multiplayer betting table with streaks, audited economy transactions, and abuse limits.",
    engine_type=EngineType.CARD,
    category="Card Economy",
    min_players=1,
    max_players=4,
    estimated_minutes=3,
    reward_rule=RewardRule(base_xp=40, base_coins=30, win_multiplier=2.0),
    config={"min_bet": 10, "max_bet": 500, "dealer_stands_at": 17, "streak_bonus": True},
)
