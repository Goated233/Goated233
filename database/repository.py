from datetime import datetime, timezone
from typing import Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class Repository:
    """Async MongoDB repository for relationship data and analytics queries."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def ensure_indexes(self) -> None:
        await self.db.users.create_index([('guild_id', 1), ('user_id', 1)], unique=True)
        await self.db.couples.create_index([('guild_id', 1), ('partner_a_id', 1), ('partner_b_id', 1)])
        for name in ['complaints','moods','journals','memories','quotes','goals','reminders','promises','achievements','visits','wishlists','gifts','ai_memories','conversation_summaries','checkins','weekly_reviews','bucket_items','trackers','complaint_reflections']:
            await self.db[name].create_index('couple_id')
        await self.db.reminders.create_index([('delivered', 1), ('remind_at', 1)])

    async def upsert_user(self, guild_id: int, user_id: int, display_name: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        await self.db.users.update_one({'guild_id': guild_id, 'user_id': user_id}, {'$set': {'display_name': display_name, 'updated_at': now}, '$setOnInsert': {'created_at': now, 'timezone': 'UTC', 'privacy_level': 'partner'}}, upsert=True)
        return await self.db.users.find_one({'guild_id': guild_id, 'user_id': user_id})

    async def create(self, collection: str, document: dict[str, Any]) -> str:
        now = datetime.now(timezone.utc)
        document.setdefault('created_at', now); document['updated_at'] = now
        result = await self.db[collection].insert_one(document)
        return str(result.inserted_id)

    async def get_couple_for_user(self, guild_id: int, user_id: int) -> dict[str, Any] | None:
        return await self.db.couples.find_one({'guild_id': guild_id, 'status': {'$in': ['pending','active']}, '$or': [{'partner_a_id': user_id}, {'partner_b_id': user_id}]})

    async def get_couple(self, couple_id: str) -> dict[str, Any] | None:
        return await self.db.couples.find_one({'_id': ObjectId(couple_id)})

    async def list_recent(self, collection: str, couple_id: str, limit: int = 10) -> list[dict[str, Any]]:
        cursor = self.db[collection].find({'couple_id': couple_id}).sort('created_at', -1).limit(limit)
        return [doc async for doc in cursor]

    async def stats(self, couple_id: str) -> dict[str, int]:
        keys = ['memories','journals','moods','goals','complaints','promises','gifts','achievements']
        return {key: await self.db[key].count_documents({'couple_id': couple_id}) for key in keys}
