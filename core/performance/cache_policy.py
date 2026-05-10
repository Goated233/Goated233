from dataclasses import dataclass


@dataclass(frozen=True)
class CachePolicy:
    key: str
    ttl_seconds: int
    jitter_seconds: int


class CachePolicyService:
    def leaderboard(self, scope: str, metric: str) -> CachePolicy:
        return CachePolicy(f"leaderboard:{scope}:{metric}", 120, 15)

    def profile(self, discord_id: int) -> CachePolicy:
        return CachePolicy(f"profile:{discord_id}", 90, 10)

    def shop(self, day_number: int) -> CachePolicy:
        return CachePolicy(f"shop:rotation:{day_number}", 3600, 120)

    def feed(self, guild_id: int | None = None) -> CachePolicy:
        suffix = guild_id if guild_id is not None else "global"
        return CachePolicy(f"feed:{suffix}", 45, 5)
