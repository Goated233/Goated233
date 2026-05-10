from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from infra.redis.queues import QueueStore
else:
    QueueStore = Any


@dataclass(frozen=True)
class MatchmakingTicket:
    discord_id: int
    user_id: int
    game_id: str
    mode: str
    rating: int
    party_size: int = 1
    guild_id: int | None = None
    global_pool: bool = True
    region: str = "global"


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    tickets: list[MatchmakingTicket]
    estimated_wait_seconds: int
    reason: str | None = None


class MatchmakingService:
    def __init__(self, queues: QueueStore):
        self.queues = queues

    async def enqueue(self, ticket: MatchmakingTicket) -> int:
        payload = {**ticket.__dict__, "queued_at": datetime.now(UTC).isoformat()}
        await self.queues.enqueue(self._queue(ticket.game_id, ticket.mode, ticket.region if ticket.global_pool else str(ticket.guild_id or ticket.region)), payload)
        return self.estimate_wait(ticket.mode, ticket.rating)

    async def try_match(self, game_id: str, mode: str, needed_players: int, rating: int, region: str = "global") -> MatchResult:
        tickets: list[MatchmakingTicket] = []
        attempts = needed_players * 3
        for _ in range(attempts):
            payload = await self.queues.dequeue(self._queue(game_id, mode, region))
            if not payload:
                break
            candidate = MatchmakingTicket(
                discord_id=int(payload["discord_id"]),
                user_id=int(payload["user_id"]),
                game_id=str(payload["game_id"]),
                mode=str(payload["mode"]),
                rating=int(payload["rating"]),
                party_size=int(payload.get("party_size", 1)),
                guild_id=payload.get("guild_id"),
                global_pool=bool(payload.get("global_pool", True)),
                region=str(payload.get("region", "global")),
            )
            if mode != "ranked" or abs(candidate.rating - rating) <= self.rating_window(len(tickets)):
                tickets.append(candidate)
            else:
                await self.queues.enqueue(self._queue(game_id, mode, region), payload)
            if len(tickets) >= needed_players:
                return MatchResult(True, tickets, 0)
        return MatchResult(False, tickets, self.estimate_wait(mode, rating), "not_enough_balanced_players")

    def estimate_wait(self, mode: str, rating: int) -> int:
        base = 20 if mode == "casual" else 45
        rating_penalty = max(0, abs(rating - 1000) // 250) * 10
        return base + rating_penalty

    def rating_window(self, attempts: int) -> int:
        return 120 + attempts * 45

    def _queue(self, game_id: str, mode: str, region: str = "global") -> str:
        return f"matchmaking:{region}:{game_id}:{mode}"
