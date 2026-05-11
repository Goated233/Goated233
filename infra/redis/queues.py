import json
from redis.asyncio import Redis


class QueueStore:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def enqueue(self, queue_name: str, payload: dict) -> None:
        await self.redis.rpush(f"queue:{queue_name}", json.dumps(payload))

    async def dequeue(self, queue_name: str) -> dict | None:
        raw = await self.redis.lpop(f"queue:{queue_name}")
        return json.loads(raw) if raw else None
