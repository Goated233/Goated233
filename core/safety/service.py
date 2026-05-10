from dataclasses import dataclass
from enum import StrEnum


class SafetySeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class SafetyFlag:
    severity: SafetySeverity
    reason: str
    evidence: dict


class RewardSafetyService:
    def validate_reward(self, user_id: int, game_id: str, rewards: dict, idempotency_key: str) -> list[SafetyFlag]:
        flags: list[SafetyFlag] = []
        if not idempotency_key or len(idempotency_key) < 32:
            flags.append(SafetyFlag(SafetySeverity.HIGH, "missing_or_short_idempotency_key", {"user_id": user_id, "game_id": game_id}))
        if int(rewards.get("coins", 0)) > 25_000:
            flags.append(SafetyFlag(SafetySeverity.CRITICAL, "coin_reward_exceeds_cap", {"coins": rewards.get("coins")}))
        if int(rewards.get("xp", 0)) > 50_000:
            flags.append(SafetyFlag(SafetySeverity.HIGH, "xp_reward_exceeds_expected_range", {"xp": rewards.get("xp")}))
        return flags

    def session_desync(self, redis_state: dict | None, db_status: str | None) -> SafetyFlag | None:
        if redis_state is None and db_status in {"lobby", "active"}:
            return SafetyFlag(SafetySeverity.MEDIUM, "redis_session_missing_but_db_active", {"db_status": db_status})
        if redis_state and db_status in {"completed", "abandoned"}:
            return SafetyFlag(SafetySeverity.MEDIUM, "redis_session_active_but_db_closed", {"session": redis_state.get("session_id")})
        return None
