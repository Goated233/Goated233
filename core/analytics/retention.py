from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class InteractionSignal:
    custom_id: str
    user_id: int
    surface: str
    latency_ms: int
    completed: bool


class AnalyticsSignalBuilder:
    def button_usage(self, signal: InteractionSignal) -> dict:
        return {
            "event_type": "button_usage",
            "subject": signal.custom_id,
            "metadata": {
                "surface": signal.surface,
                "latency_ms": signal.latency_ms,
                "completed": signal.completed,
                "recorded_at": datetime.now(UTC).isoformat(),
            },
            "actor_discord_id": signal.user_id,
        }

    def rage_quit(self, session_id: str, game_id: str, elapsed_seconds: int, actor_id: int) -> dict:
        return {
            "event_type": "rage_quit_detected" if elapsed_seconds > 90 else "early_abandon",
            "subject": game_id,
            "metadata": {"session_id": session_id, "elapsed_seconds": elapsed_seconds},
            "actor_discord_id": actor_id,
        }

    def reward_generation(self, game_id: str, rewards: list[dict]) -> dict:
        return {
            "event_type": "reward_generation",
            "subject": game_id,
            "metadata": {"rewards": rewards, "total_coins": sum(int(r.get("coins", 0)) for r in rewards)},
            "actor_discord_id": None,
        }
