import asyncio
from database.models import Base
from app.config import get_settings
from database.session import create_engine


async def main() -> None:
    settings = get_settings()
    if settings.environment == "production":
        raise RuntimeError("Refusing to reset database in production.")
    engine = create_engine(settings.database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Development database reset complete. Run seed_database.py and bootstrap_owner.py next.")


if __name__ == "__main__":
    asyncio.run(main())
