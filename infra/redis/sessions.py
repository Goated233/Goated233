import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

Redis = Any


@dataclass(frozen=True)
class SessionLock:
    key: str
    token: str
    acquired: bool


class SessionStore:
    """Redis-backed active session store with indexes and distributed interaction locks."""

    def __init__(self, redis: Redis, ttl_seconds: int):
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    async def save(self, session_id: str, state: dict) -> None:
        now = datetime.now(UTC).isoformat()
        serialized = {**state, "updated_at": now}
        await self.redis.set(f"session:{session_id}", json.dumps(serialized), ex=self.ttl_seconds)
        await self.redis.zadd("sessions:active", {session_id: datetime.now(UTC).timestamp()})
        for player_id in serialized.get("player_discord_ids", []):
            await self.redis.set(f"session:user:{player_id}", session_id, ex=self.ttl_seconds)

    async def load(self, session_id: str) -> dict | None:
        raw = await self.redis.get(f"session:{session_id}")
        return json.loads(raw) if raw else None

    async def delete(self, session_id: str) -> None:
        state = await self.load(session_id)
        pipe = self.redis.pipeline()
        pipe.delete(f"session:{session_id}")
        pipe.zrem("sessions:active", session_id)
        if state:
            for player_id in state.get("player_discord_ids", []):
                pipe.delete(f"session:user:{player_id}")
        await pipe.execute()

    async def active_for_user(self, discord_id: int) -> str | None:
        session_id = await self.redis.get(f"session:user:{discord_id}")
        return str(session_id) if session_id else None

    async def list_active_ids(self, limit: int = 100) -> list[str]:
        ids = await self.redis.zrevrange("sessions:active", 0, limit - 1)
        return [str(session_id) for session_id in ids]

    async def active_count(self) -> int:
        return int(await self.redis.zcard("sessions:active"))

    async def mark_reconnect_token(self, session_id: str, discord_id: int, token: str) -> None:
        await self.redis.set(
            f"session:reconnect:{discord_id}:{token}", session_id, ex=min(self.ttl_seconds, 900)
        )

    async def consume_reconnect_token(self, discord_id: int, token: str) -> str | None:
        key = f"session:reconnect:{discord_id}:{token}"
        session_id = await self.redis.get(key)
        if session_id:
            await self.redis.delete(key)
        return str(session_id) if session_id else None

    async def acquire_lock(self, session_id: str, actor_id: int, ttl_seconds: int = 8) -> SessionLock:
        token = f"{actor_id}:{datetime.now(UTC).timestamp()}"
        key = f"session:lock:{session_id}"
        acquired = bool(await self.redis.set(key, token, ex=ttl_seconds, nx=True))
        return SessionLock(key=key, token=token, acquired=acquired)

    async def release_lock(self, lock: SessionLock) -> None:
        current = await self.redis.get(lock.key)
        if current == lock.token:
            await self.redis.delete(lock.key)

    @asynccontextmanager
    async def interaction_lock(self, session_id: str, actor_id: int) -> AsyncIterator[bool]:
        lock = await self.acquire_lock(session_id, actor_id)
        try:
            yield lock.acquired
        finally:
            if lock.acquired:
                await self.release_lock(lock)

    async def cleanup_stale(self, stale_before_timestamp: float) -> int:
        stale_ids = await self.redis.zrangebyscore("sessions:active", 0, stale_before_timestamp)
        removed = 0
        for session_id in stale_ids:
            if not await self.redis.exists(f"session:{session_id}"):
                await self.redis.zrem("sessions:active", session_id)
                removed += 1
        return removed
