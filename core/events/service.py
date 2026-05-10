from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class WorldEventDefinition:
    id: str
    name: str
    description: str
    modifiers: dict[str, float | int | str]
    duration_hours: int
    broadcast: str


class WorldEventService:
    ROTATION = [
        WorldEventDefinition("double_xp", "Double XP Weekend", "All games grant bonus XP.", {"xp_multiplier": 2.0}, 48, "🔥 Double XP is live!"),
        WorldEventDefinition("loot_frenzy", "Loot Frenzy", "Rare drops are easier to find.", {"drop_rate_multiplier": 1.75}, 24, "🎁 Loot Frenzy has begun!"),
        WorldEventDefinition("corruption_invasion", "Corruption Invasion", "Dungeon enemies are stronger but richer.", {"enemy_power": 1.25, "coin_multiplier": 1.5}, 36, "🌑 Corruption spreads across the arcade!"),
        WorldEventDefinition("meteor_shower", "Meteor Shower", "Mining, fishing, and raids find cosmic items.", {"cosmic_drop_rate": 2.0}, 12, "☄️ Meteor Shower event is active!"),
    ]

    def current_rotation(self, now: datetime | None = None) -> WorldEventDefinition:
        moment = now or datetime.now(UTC)
        index = moment.toordinal() % len(self.ROTATION)
        return self.ROTATION[index]

    def schedule_window(self, event: WorldEventDefinition, now: datetime | None = None) -> dict:
        starts = now or datetime.now(UTC)
        ends = starts + timedelta(hours=event.duration_hours)
        return {"event_id": event.id, "starts_at": starts.isoformat(), "ends_at": ends.isoformat(), "modifiers": event.modifiers}
