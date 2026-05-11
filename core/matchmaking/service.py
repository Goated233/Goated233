from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from core.limits import LimitReason, LimitResult, LimitViolation, format_duration

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


@dataclass
class MatchmakingGuardState:
    active_ticket_by_user: dict[int, str] = field(default_factory=dict)
    cooldowns: dict[int, datetime] = field(default_factory=dict)
    ranked_cooldowns: dict[int, datetime] = field(default_factory=dict)
    penalties: dict[int, datetime] = field(default_factory=dict)
    enqueued_at: dict[str, datetime] = field(default_factory=dict)
    attempts: dict[int, list[datetime]] = field(default_factory=dict)


class MatchmakingService:
    QUEUE_COOLDOWN_SECONDS = 20
    RANKED_COOLDOWN_SECONDS = 60
    QUEUE_TIMEOUT_SECONDS = 300
    MAX_ATTEMPTS_PER_MINUTE = 4
    ABANDON_PENALTY_SECONDS = 300
    AFK_PENALTY_SECONDS = 180

    def __init__(self, queues: QueueStore, guard: MatchmakingGuardState | None = None):
        self.queues = queues
        self.guard = guard or MatchmakingGuardState()

    async def enqueue(self, ticket: MatchmakingTicket) -> int:
        self.cleanup_timeouts()
        self._validate_enqueue(ticket)
        queue_name = self._queue(ticket.game_id, ticket.mode, ticket.region if ticket.global_pool else str(ticket.guild_id or ticket.region))
        payload = {**ticket.__dict__, "queued_at": datetime.now(UTC).isoformat(), "queue_name": queue_name}
        await self.queues.enqueue(queue_name, payload)
        self.guard.active_ticket_by_user[ticket.user_id] = queue_name
        self.guard.enqueued_at[f"{queue_name}:{ticket.user_id}"] = datetime.now(UTC)
        cooldowns = self.guard.ranked_cooldowns if ticket.mode == "ranked" else self.guard.cooldowns
        cooldowns[ticket.user_id] = datetime.now(UTC) + timedelta(seconds=self.RANKED_COOLDOWN_SECONDS if ticket.mode == "ranked" else self.QUEUE_COOLDOWN_SECONDS)
        return self.estimate_wait(ticket.mode, ticket.rating)

    async def try_match(self, game_id: str, mode: str, needed_players: int, rating: int, region: str = "global") -> MatchResult:
        self.cleanup_timeouts()
        tickets: list[MatchmakingTicket] = []
        attempts = needed_players * 3
        queue_name = self._queue(game_id, mode, region)
        for _ in range(attempts):
            payload = await self.queues.dequeue(queue_name)
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
            self.guard.active_ticket_by_user.pop(candidate.user_id, None)
            self.guard.enqueued_at.pop(f"{queue_name}:{candidate.user_id}", None)
            if mode != "ranked" or abs(candidate.rating - rating) <= self.rating_window(len(tickets)):
                tickets.append(candidate)
            else:
                await self.queues.enqueue(queue_name, payload)
                self.guard.active_ticket_by_user[candidate.user_id] = queue_name
                self.guard.enqueued_at[f"{queue_name}:{candidate.user_id}"] = datetime.now(UTC)
            if len(tickets) >= needed_players:
                return MatchResult(True, tickets, 0)
        return MatchResult(False, tickets, self.estimate_wait(mode, rating), "not_enough_balanced_players")

    def cancel_queue(self, user_id: int) -> None:
        self.guard.active_ticket_by_user.pop(user_id, None)

    def record_abandonment(self, user_id: int, afk: bool = False) -> None:
        self.guard.active_ticket_by_user.pop(user_id, None)
        self.guard.penalties[user_id] = datetime.now(UTC) + timedelta(seconds=self.AFK_PENALTY_SECONDS if afk else self.ABANDON_PENALTY_SECONDS)

    def cleanup_timeouts(self, now: datetime | None = None) -> int:
        moment = now or datetime.now(UTC)
        expired_keys = [key for key, queued_at in self.guard.enqueued_at.items() if moment - queued_at > timedelta(seconds=self.QUEUE_TIMEOUT_SECONDS)]
        for key in expired_keys:
            _, user_id = key.rsplit(":", 1)
            self.guard.enqueued_at.pop(key, None)
            self.guard.active_ticket_by_user.pop(int(user_id), None)
        return len(expired_keys)

    def estimate_wait(self, mode: str, rating: int) -> int:
        base = 20 if mode == "casual" else 45
        rating_penalty = max(0, abs(rating - 1000) // 250) * 10
        return base + rating_penalty

    def rating_window(self, attempts: int) -> int:
        return 120 + attempts * 45

    def _validate_enqueue(self, ticket: MatchmakingTicket) -> None:
        now = datetime.now(UTC)
        if ticket.user_id in self.guard.active_ticket_by_user:
            raise LimitViolation(LimitResult.block(LimitReason.DUPLICATE, "You are already queued for matchmaking.", active_reference=self.guard.active_ticket_by_user[ticket.user_id], recovery_action="Cancel or reconnect to the existing queue."))
        penalty_until = self.guard.penalties.get(ticket.user_id)
        if penalty_until and penalty_until > now:
            raise LimitViolation(LimitResult.block(LimitReason.COOLDOWN, f"Matchmaking penalty active. Try again in {format_duration(penalty_until - now)}.", retry_after_seconds=round((penalty_until - now).total_seconds())))
        cooldowns = self.guard.ranked_cooldowns if ticket.mode == "ranked" else self.guard.cooldowns
        cooldown_until = cooldowns.get(ticket.user_id)
        if cooldown_until and cooldown_until > now:
            raise LimitViolation(LimitResult.block(LimitReason.COOLDOWN, f"Queue cooldown active. Try again in {format_duration(cooldown_until - now)}.", retry_after_seconds=round((cooldown_until - now).total_seconds())))
        attempts = [stamp for stamp in self.guard.attempts.get(ticket.user_id, []) if now - stamp < timedelta(minutes=1)]
        if len(attempts) >= self.MAX_ATTEMPTS_PER_MINUTE:
            raise LimitViolation(LimitResult.block(LimitReason.RATE_LIMITED, "You are joining matchmaking too quickly."))
        attempts.append(now)
        self.guard.attempts[ticket.user_id] = attempts
        if ticket.party_size < 1 or ticket.party_size > 5:
            raise LimitViolation(LimitResult.block(LimitReason.CAPACITY, "Invalid party size for matchmaking."))

    def _queue(self, game_id: str, mode: str, region: str = "global") -> str:
        return f"matchmaking:{region}:{game_id}:{mode}"
