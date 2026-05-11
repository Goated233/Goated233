from dataclasses import dataclass
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.player import Profile, User
from infra.redis.cache import CacheStore


@dataclass(frozen=True)
class LeaderboardEntry:
    rank: int
    discord_id: int
    username: str
    value: int
    icon: str


class LeaderboardService:
    def __init__(self, session: AsyncSession, cache: CacheStore, ttl_seconds: int):
        self.session = session
        self.cache = cache
        self.ttl_seconds = ttl_seconds

    async def global_xp(self, limit: int = 10) -> list[LeaderboardEntry]:
        key = f"leaderboard:global_xp:{limit}"
        cached = await self.cache.get_json(key)
        if isinstance(cached, list):
            return [LeaderboardEntry(**entry) for entry in cached]
        rows = await self.session.execute(
            select(Profile, User).join(User, User.id == Profile.user_id).order_by(desc(Profile.xp)).limit(limit)
        )
        entries = [
            LeaderboardEntry(index + 1, user.discord_id, user.username_cache, profile.xp, self.rank_icon(index + 1))
            for index, (profile, user) in enumerate(rows.all())
        ]
        await self.cache.set_json(key, [entry.__dict__ for entry in entries], self.ttl_seconds)
        return entries

    def rank_icon(self, rank: int) -> str:
        return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "🔹")

    def reward_for_rank(self, rank: int) -> dict:
        if rank == 1:
            return {"coins": 5000, "gems": 150, "title": "Leaderboard Monarch"}
        if rank <= 3:
            return {"coins": 2500, "gems": 75, "title": "Podium Legend"}
        if rank <= 10:
            return {"coins": 1000, "gems": 25}
        return {"coins": 250}
