from engines.base.types import EngineType, GameDefinition, RewardRule

DUNGEON_RAID = GameDefinition(
    id="dungeon_raid",
    name="Dungeon Raid",
    description="Co-op procedural PvE rooms, enemies, loot, bosses, rarity drops, abilities, and progression.",
    engine_type=EngineType.BATTLE,
    category="PvE Battle",
    min_players=1,
    max_players=5,
    estimated_minutes=8,
    reward_rule=RewardRule(
        base_xp=140,
        base_coins=85,
        win_multiplier=1.6,
        drops=[{"item_id": "ancient_relic", "rarity": "legendary", "weight": 6}],
    ),
    config={
        "rooms": ["Crypt Gate", "Crystal Cavern", "Abyss Vault"],
        "enemies": ["Goblin Scout", "Crystal Slime", "Abyss Knight"],
        "bosses": ["Omega Lich", "Vault Dragon"],
        "abilities": ["Slash", "Guard", "Ultimate"],
    },
)
