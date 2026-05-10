import json
from typing import TypeVar
from redis.asyncio import Redis

T = TypeVar("T")


class CacheStore:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_json(self, key: str) -> dict | list | None:
        raw = await self.redis.get(key)
        return json.loads(raw) if raw else None

    async def set_json(self, key: str, value: dict | list, ttl_seconds: int) -> None:
        await self.redis.set(key, json.dumps(value), ex=ttl_seconds)
