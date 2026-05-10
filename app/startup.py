from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from redis.asyncio import Redis
from app.config import Settings


@dataclass(frozen=True)
class StartupCheck:
    name: str
    ok: bool
    detail: str


class StartupValidator:
    def __init__(self, settings: Settings, engine: AsyncEngine, redis: Redis):
        self.settings = settings
        self.engine = engine
        self.redis = redis

    def validate_static(self) -> list[StartupCheck]:
        checks = [
            StartupCheck("discord_token", bool(self.settings.discord_token and len(self.settings.discord_token) > 20), "configured" if self.settings.discord_token else "missing DISCORD_TOKEN"),
            StartupCheck("owner_user_id", self.settings.owner_user_id > 10**16, str(self.settings.owner_user_id)),
            StartupCheck("owner_display", bool(self.settings.owner_display), self.settings.owner_display or "missing"),
            StartupCheck("database_url", self.settings.database_url.startswith("postgresql+asyncpg://"), "must use postgresql+asyncpg://"),
            StartupCheck("redis_url", self.settings.redis_url.startswith("redis://"), "must use redis://"),
        ]
        return checks

    async def validate_database(self) -> StartupCheck:
        try:
            async with self.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return StartupCheck("database", True, "PostgreSQL connection ready")
        except Exception as exc:
            return StartupCheck("database", False, f"PostgreSQL check failed: {exc}")

    async def validate_redis(self) -> StartupCheck:
        try:
            pong = await self.redis.ping()
            return StartupCheck("redis", bool(pong), "Redis connection ready")
        except Exception as exc:
            return StartupCheck("redis", False, f"Redis check failed: {exc}")

    async def validate_all(self) -> list[StartupCheck]:
        return [*self.validate_static(), await self.validate_database(), await self.validate_redis()]

    async def assert_ready(self) -> None:
        checks = await self.validate_all()
        failed = [check for check in checks if not check.ok]
        if failed:
            details = "\n".join(f"- {check.name}: {check.detail}" for check in failed)
            raise RuntimeError(f"Alpha Omega Arcade startup validation failed:\n{details}")
