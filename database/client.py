from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import Settings


class Mongo:
    """Lifecycle wrapper around Motor client creation and shutdown."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client: AsyncIOMotorClient | None = None

    async def connect(self) -> AsyncIOMotorDatabase:
        if self.client is None:
            self.client = AsyncIOMotorClient(self.settings.mongo_uri, uuidRepresentation='standard')
            await self.client.admin.command('ping')
        return self.client[self.settings.mongo_database]

    async def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None


@asynccontextmanager
async def mongo_database(settings: Settings) -> AsyncIterator[AsyncIOMotorDatabase]:
    mongo = Mongo(settings)
    db = await mongo.connect()
    try:
        yield db
    finally:
        await mongo.close()
