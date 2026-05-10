from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from core.limits import LimitReason, LimitResult, LimitViolation, format_duration

MAX_CURRENCY_BALANCE = 9_000_000_000
MAX_TRADE_AMOUNT = 1_000_000
PURCHASE_RATE_LIMIT = 10
PURCHASE_WINDOW_SECONDS = 60


@dataclass
class EconomyGuardState:
    idempotency_keys: set[str] = field(default_factory=set)
    daily_claims: dict[int, datetime] = field(default_factory=dict)
    purchase_attempts: dict[int, list[datetime]] = field(default_factory=dict)
    exploit_logs: list[dict] = field(default_factory=list)


class EconomyGuard:
    def __init__(self, state: EconomyGuardState | None = None):
        self.state = state or EconomyGuardState()

    def validate_transaction(self, user_id: int, currency: str, amount: int, balance_before: int, idempotency_key: str) -> int:
        if currency not in {"coins", "gems", "xp"}:
            self._log(user_id, "invalid_currency", {"currency": currency})
            raise LimitViolation(LimitResult.block(LimitReason.REQUIREMENT, "Invalid currency transaction."))
        if amount <= 0:
            self._log(user_id, "non_positive_transaction", {"amount": amount})
            raise LimitViolation(LimitResult.block(LimitReason.REQUIREMENT, "Rewards must be positive and server generated."))
        if idempotency_key in self.state.idempotency_keys:
            self._log(user_id, "duplicate_idempotency_key", {"key": idempotency_key})
            raise LimitViolation(LimitResult.block(LimitReason.DUPLICATE, "This reward was already processed.", active_reference=idempotency_key))
        balance_after = balance_before + amount
        if balance_after > MAX_CURRENCY_BALANCE:
            self._log(user_id, "currency_overflow", {"balance_after": balance_after})
            raise LimitViolation(LimitResult.block(LimitReason.OVERFLOW, "Currency balance limit reached."))
        self.state.idempotency_keys.add(idempotency_key)
        return balance_after

    def claim_daily(self, user_id: int, now: datetime | None = None) -> None:
        moment = now or datetime.now(UTC)
        next_claim = self.state.daily_claims.get(user_id)
        if next_claim and next_claim > moment:
            raise LimitViolation(LimitResult.block(LimitReason.COOLDOWN, f"Daily reward available again in {format_duration(next_claim - moment)}.", retry_after_seconds=round((next_claim - moment).total_seconds())))
        self.state.daily_claims[user_id] = moment + timedelta(hours=24)

    def validate_trade(self, sender_id: int, receiver_id: int, amount: int, sender_balance: int) -> None:
        if sender_id == receiver_id:
            raise LimitViolation(LimitResult.block(LimitReason.DUPLICATE, "You cannot trade with yourself."))
        if amount <= 0 or amount > MAX_TRADE_AMOUNT or amount > sender_balance:
            self._log(sender_id, "invalid_trade", {"receiver_id": receiver_id, "amount": amount})
            raise LimitViolation(LimitResult.block(LimitReason.REQUIREMENT, "Trade failed validation."))

    def purchase_allowed(self, user_id: int, price: int, balance: int, now: datetime | None = None) -> None:
        moment = now or datetime.now(UTC)
        if price <= 0 or price > balance:
            raise LimitViolation(LimitResult.block(LimitReason.INSUFFICIENT_FUNDS, "Purchase failed validation."))
        attempts = [stamp for stamp in self.state.purchase_attempts.get(user_id, []) if moment - stamp < timedelta(seconds=PURCHASE_WINDOW_SECONDS)]
        if len(attempts) >= PURCHASE_RATE_LIMIT:
            raise LimitViolation(LimitResult.block(LimitReason.RATE_LIMITED, "Purchase rate limit reached."))
        attempts.append(moment)
        self.state.purchase_attempts[user_id] = attempts

    def rollback_key(self, idempotency_key: str) -> None:
        self.state.idempotency_keys.discard(idempotency_key)

    def _log(self, user_id: int, reason: str, evidence: dict) -> None:
        self.state.exploit_logs.append({"user_id": user_id, "reason": reason, "evidence": evidence, "created_at": datetime.now(UTC).isoformat()})
