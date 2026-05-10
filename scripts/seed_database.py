import asyncio
from sqlalchemy.dialects.postgresql import insert
from app.config import get_settings
from database.models.game import GameDefinition
from database.models.inventory import Item
from database.models.platform import Achievement, Quest
from database.session import create_engine, create_session_factory
from games.registry import ALL_GAMES

STARTER_ITEMS = [
    {"id": "iron_coin_cache", "name": "Iron Coin Cache", "description": "A pouch of dungeon coins.", "rarity": "common", "item_type": "currency", "stackable": True, "metadata_json": {}},
    {"id": "crystal_blade", "name": "Crystal Blade", "description": "A rare blade from the Crystal Cavern.", "rarity": "rare", "item_type": "weapon", "stackable": False, "metadata_json": {"slot": "weapon", "power": 18}},
    {"id": "omega_relic", "name": "Omega Relic", "description": "A legendary relic pulsing with raid energy.", "rarity": "legendary", "item_type": "trinket", "stackable": False, "metadata_json": {"slot": "trinket", "power": 35}},
]

STARTER_ACHIEVEMENTS = [
    {"id": "first_dungeon_clear", "name": "First Clear", "description": "Complete Dungeon Raid once.", "criteria": {"game": "dungeon_raid", "clears": 1}, "points": 10},
    {"id": "boss_slayer", "name": "Boss Slayer", "description": "Defeat a dungeon boss.", "criteria": {"boss_defeats": 1}, "points": 25},
]

STARTER_QUESTS = [
    {"id": "daily_dungeon", "name": "Daily Dungeon", "description": "Clear one Dungeon Raid today.", "reward": {"xp": 250, "coins": 200}, "criteria": {"dungeon_clears": 1}},
]


async def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)
    async with factory() as session:
        for game in ALL_GAMES:
            stmt = insert(GameDefinition).values(
                id=game.id,
                name=game.name,
                description=game.description,
                engine_type=game.engine_type.value,
                category=game.category,
                min_players=game.min_players,
                max_players=game.max_players,
                config=game.config,
            ).on_conflict_do_update(
                index_elements=[GameDefinition.id],
                set_={"name": game.name, "description": game.description, "config": game.config, "enabled": True},
            )
            await session.execute(stmt)
        for row in STARTER_ITEMS:
            await session.execute(insert(Item).values(**row).on_conflict_do_nothing(index_elements=[Item.id]))
        for row in STARTER_ACHIEVEMENTS:
            await session.execute(insert(Achievement).values(**row).on_conflict_do_nothing(index_elements=[Achievement.id]))
        for row in STARTER_QUESTS:
            await session.execute(insert(Quest).values(**row).on_conflict_do_nothing(index_elements=[Quest.id]))
        await session.commit()
    await engine.dispose()
    print("Seeded Alpha Omega Arcade starter games, items, achievements, and quests.")


if __name__ == "__main__":
    asyncio.run(main())
