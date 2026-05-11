from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from core.limits import LimitReason, LimitResult, LimitViolation, format_duration


@dataclass
class InteractionGuardState:
    processed_interactions: set[str] = field(default_factory=set)
    locks: dict[str, datetime] = field(default_factory=dict)
    cooldowns: dict[tuple[int, str], datetime] = field(default_factory=dict)
    spam_counts: dict[tuple[int, str], list[datetime]] = field(default_factory=dict)


class InteractionGuard:
    DEFAULT_COOLDOWN_SECONDS = 2
    LOCK_TTL_SECONDS = 8
    MAX_PER_WINDOW = 8
    WINDOW_SECONDS = 10

    def __init__(self, state: InteractionGuardState | None = None):
        self.state = state or InteractionGuardState()

    def validate(self, *, interaction_id: str, user_id: int, component_id: str, expires_at: datetime | None = None) -> None:
        now = datetime.now(UTC)
        if expires_at and expires_at <= now:
            raise LimitViolation(LimitResult.block(LimitReason.EXPIRED, "This button expired. Open a fresh panel to continue."))
        if interaction_id in self.state.processed_interactions:
            raise LimitViolation(LimitResult.block(LimitReason.DUPLICATE, "That interaction was already processed."))
        lock_until = self.state.locks.get(component_id)
        if lock_until and lock_until > now:
            raise LimitViolation(LimitResult.block(LimitReason.LOCKED, "That action is already being processed."))
        cooldown_key = (user_id, component_id)
        cooldown_until = self.state.cooldowns.get(cooldown_key)
        if cooldown_until and cooldown_until > now:
            raise LimitViolation(LimitResult.block(LimitReason.COOLDOWN, f"Slow down — try again in {format_duration(cooldown_until - now)}.", retry_after_seconds=round((cooldown_until - now).total_seconds())))
        events = [stamp for stamp in self.state.spam_counts.get(cooldown_key, []) if now - stamp < timedelta(seconds=self.WINDOW_SECONDS)]
        if len(events) >= self.MAX_PER_WINDOW:
            raise LimitViolation(LimitResult.block(LimitReason.RATE_LIMITED, "Too many button presses. Your actions are being silently throttled."))
        events.append(now)
        self.state.spam_counts[cooldown_key] = events
        self.state.locks[component_id] = now + timedelta(seconds=self.LOCK_TTL_SECONDS)
        self.state.cooldowns[cooldown_key] = now + timedelta(seconds=self.DEFAULT_COOLDOWN_SECONDS)
        self.state.processed_interactions.add(interaction_id)

    def release(self, component_id: str) -> None:
        self.state.locks.pop(component_id, None)

    def cleanup(self, now: datetime | None = None) -> int:
        moment = now or datetime.now(UTC)
        before = len(self.state.locks) + len(self.state.cooldowns)
        self.state.locks = {key: value for key, value in self.state.locks.items() if value > moment}
        self.state.cooldowns = {key: value for key, value in self.state.cooldowns.items() if value > moment}
        return before - len(self.state.locks) - len(self.state.cooldowns)
