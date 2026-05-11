from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any


class LimitScope(StrEnum):
    PARTY = "party"
    CLAN = "clan"
    MATCHMAKING = "matchmaking"
    ECONOMY = "economy"
    SESSION = "session"
    INTERACTION = "interaction"
    WORLD = "world"
    TOURNAMENT = "tournament"


class LimitReason(StrEnum):
    COOLDOWN = "cooldown"
    DUPLICATE = "duplicate"
    CAPACITY = "capacity"
    REQUIREMENT = "requirement"
    OWNERSHIP = "ownership"
    EXPIRED = "expired"
    LOCKED = "locked"
    STALE = "stale"
    RATE_LIMITED = "rate_limited"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    OVERFLOW = "overflow"


@dataclass(frozen=True)
class LimitResult:
    allowed: bool
    reason: LimitReason | None = None
    message: str = "Allowed"
    retry_after_seconds: int = 0
    active_reference: str | None = None
    recovery_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def allow(cls) -> "LimitResult":
        return cls(True)

    @classmethod
    def block(
        cls,
        reason: LimitReason,
        message: str,
        *,
        retry_after_seconds: int = 0,
        active_reference: str | None = None,
        recovery_action: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "LimitResult":
        return cls(False, reason, message, max(0, retry_after_seconds), active_reference, recovery_action, metadata or {})


class LimitViolation(ValueError):
    def __init__(self, result: LimitResult):
        super().__init__(result.message)
        self.result = result


@dataclass(frozen=True)
class AuditEvent:
    scope: LimitScope
    actor_id: int
    action: str
    allowed: bool
    reason: str | None
    created_at: datetime
    metadata: dict[str, Any]


@dataclass
class LimitLedger:
    cooldowns: dict[str, datetime] = field(default_factory=dict)
    idempotency_keys: set[str] = field(default_factory=set)
    locks: dict[str, datetime] = field(default_factory=dict)
    counters: dict[str, list[datetime]] = field(default_factory=dict)
    audit_events: list[AuditEvent] = field(default_factory=list)


class LimitEnforcer:
    """Server-side MMO limit checks usable with Redis-backed or in-memory state.

    Service methods pass durable state dictionaries/dataclasses into this enforcer so tests and local
    workers use the same validation semantics as production Redis/DB-backed paths.
    """

    def __init__(self, ledger: LimitLedger | None = None):
        self.ledger = ledger or LimitLedger()

    def require(self, result: LimitResult) -> None:
        if not result.allowed:
            raise LimitViolation(result)

    def check_cooldown(self, key: str, ttl_seconds: int, now: datetime | None = None) -> LimitResult:
        moment = now or datetime.now(UTC)
        expires_at = self.ledger.cooldowns.get(key)
        if expires_at and expires_at > moment:
            return LimitResult.block(
                LimitReason.COOLDOWN,
                f"This action is cooling down. Try again in {format_duration(expires_at - moment)}.",
                retry_after_seconds=round((expires_at - moment).total_seconds()),
            )
        self.ledger.cooldowns[key] = moment + timedelta(seconds=ttl_seconds)
        return LimitResult.allow()

    def peek_cooldown(self, key: str, now: datetime | None = None) -> LimitResult:
        moment = now or datetime.now(UTC)
        expires_at = self.ledger.cooldowns.get(key)
        if expires_at and expires_at > moment:
            return LimitResult.block(
                LimitReason.COOLDOWN,
                f"This action is cooling down. Try again in {format_duration(expires_at - moment)}.",
                retry_after_seconds=round((expires_at - moment).total_seconds()),
            )
        return LimitResult.allow()

    def remember_once(self, key: str, message: str = "Duplicate action blocked.") -> LimitResult:
        if key in self.ledger.idempotency_keys:
            return LimitResult.block(LimitReason.DUPLICATE, message, active_reference=key)
        self.ledger.idempotency_keys.add(key)
        return LimitResult.allow()

    def rate_limit(self, key: str, max_events: int, window_seconds: int, now: datetime | None = None) -> LimitResult:
        moment = now or datetime.now(UTC)
        cutoff = moment - timedelta(seconds=window_seconds)
        events = [event_at for event_at in self.ledger.counters.get(key, []) if event_at > cutoff]
        if len(events) >= max_events:
            retry = round((events[0] + timedelta(seconds=window_seconds) - moment).total_seconds())
            self.ledger.counters[key] = events
            return LimitResult.block(
                LimitReason.RATE_LIMITED,
                f"Too many attempts. Try again in {format_duration(timedelta(seconds=retry))}.",
                retry_after_seconds=retry,
            )
        events.append(moment)
        self.ledger.counters[key] = events
        return LimitResult.allow()

    def acquire_lock(self, key: str, ttl_seconds: int, now: datetime | None = None) -> LimitResult:
        moment = now or datetime.now(UTC)
        expires_at = self.ledger.locks.get(key)
        if expires_at and expires_at > moment:
            return LimitResult.block(LimitReason.LOCKED, "This action is already being processed.", retry_after_seconds=round((expires_at - moment).total_seconds()))
        self.ledger.locks[key] = moment + timedelta(seconds=ttl_seconds)
        return LimitResult.allow()

    def release_lock(self, key: str) -> None:
        self.ledger.locks.pop(key, None)

    def audit(self, scope: LimitScope, actor_id: int, action: str, result: LimitResult, metadata: dict[str, Any] | None = None) -> None:
        self.ledger.audit_events.append(
            AuditEvent(scope, actor_id, action, result.allowed, result.reason.value if result.reason else None, datetime.now(UTC), metadata or {})
        )
        del self.ledger.audit_events[500:]

    def cleanup(self, now: datetime | None = None) -> int:
        moment = now or datetime.now(UTC)
        before = len(self.ledger.cooldowns) + len(self.ledger.locks)
        self.ledger.cooldowns = {key: expires for key, expires in self.ledger.cooldowns.items() if expires > moment}
        self.ledger.locks = {key: expires for key, expires in self.ledger.locks.items() if expires > moment}
        return before - len(self.ledger.cooldowns) - len(self.ledger.locks)


def format_duration(delta: timedelta) -> str:
    seconds = max(0, round(delta.total_seconds()))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def limit_error_payload(result: LimitResult, title: str = "Action blocked") -> dict[str, Any]:
    fields = []
    if result.retry_after_seconds:
        fields.append({"name": "Retry In", "value": format_duration(timedelta(seconds=result.retry_after_seconds))})
    if result.active_reference:
        fields.append({"name": "Active Reference", "value": result.active_reference})
    if result.recovery_action:
        fields.append({"name": "Recovery", "value": result.recovery_action})
    return {
        "title": f"🛡️ {title}",
        "description": result.message,
        "color": 0xF59E0B,
        "fields": fields,
    }
