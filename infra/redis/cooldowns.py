from dataclasses import dataclass
from redis.asyncio import Redis


@dataclass(frozen=True)
class CooldownResult:
    allowed: bool
    retry_after_seconds: int
    bypassed: bool = False


class CooldownStore:
    def __init__(self, redis: Redis, owner_user_id: int):
        self.redis = redis
        self.owner_user_id = owner_user_id

    async def consume(self, scope: str, actor_discord_id: int, ttl_seconds: int) -> CooldownResult:
        if actor_discord_id == self.owner_user_id:
            return CooldownResult(allowed=True, retry_after_seconds=0, bypassed=True)
        key = f"cooldown:{scope}:{actor_discord_id}"
        created = await self.redis.set(key, "1", ex=ttl_seconds, nx=True)
        if created:
            return CooldownResult(allowed=True, retry_after_seconds=0)
        ttl = await self.redis.ttl(key)
        return CooldownResult(allowed=False, retry_after_seconds=max(0, int(ttl)))

    async def clear_user(self, actor_discord_id: int) -> int:
        keys = await self.redis.keys(f"cooldown:*:{actor_discord_id}")
        if not keys:
            return 0
        return int(await self.redis.delete(*keys))
