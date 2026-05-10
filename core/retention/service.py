from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum


class QuestCadence(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    SEASONAL = "seasonal"


@dataclass(frozen=True)
class RetentionReward:
    claimable: bool
    streak_day: int
    weekly_streak: int
    monthly_streak: int
    xp: int
    coins: int
    gems: int
    booster_minutes: int
    visual: str
    reason: str | None = None


@dataclass(frozen=True)
class QuestDefinition:
    id: str
    cadence: QuestCadence
    name: str
    description: str
    target: int
    metric: str
    reward: dict
    icon: str


@dataclass(frozen=True)
class QuestProgress:
    quest: QuestDefinition
    current: int
    completed: bool
    percent: int


class RetentionService:
    DAILY_QUESTS = [
        QuestDefinition("daily_clear", QuestCadence.DAILY, "Daily Dungeon", "Clear one Dungeon Raid.", 1, "dungeon_clears", {"xp": 250, "coins": 150}, "🗡️"),
        QuestDefinition("daily_buttons", QuestCadence.DAILY, "Button Burst", "Use 12 arcade buttons.", 12, "button_clicks", {"xp": 120, "coins": 80}, "🔘"),
        QuestDefinition("daily_loot", QuestCadence.DAILY, "Loot Hunter", "Find 3 loot drops.", 3, "loot_drops", {"xp": 180, "coins": 100}, "🎁"),
    ]
    WEEKLY_QUESTS = [
        QuestDefinition("weekly_raider", QuestCadence.WEEKLY, "Raid Regular", "Complete 10 game sessions.", 10, "sessions_completed", {"xp": 1500, "gems": 25}, "🔥"),
        QuestDefinition("weekly_social", QuestCadence.WEEKLY, "Party Up", "Join or create 3 parties.", 3, "party_actions", {"xp": 900, "coins": 600}, "🤝"),
    ]
    SEASONAL_MISSIONS = [
        QuestDefinition("season_mythic", QuestCadence.SEASONAL, "Mythic Chase", "Earn 10 legendary+ drops this season.", 10, "legendary_drops", {"xp": 5000, "cosmetic": "mythic_banner"}, "🌈"),
    ]

    def login_reward(self, last_claim: date | None, streak_day: int, now: datetime | None = None) -> RetentionReward:
        today = (now or datetime.now(UTC)).date()
        if last_claim == today:
            return RetentionReward(False, streak_day, streak_day // 7, streak_day // 30, 0, 0, 0, 0, "✅", "already_claimed")
        consecutive = last_claim is not None and today - last_claim == timedelta(days=1)
        new_streak = streak_day + 1 if consecutive else 1
        weekly = new_streak // 7
        monthly = new_streak // 30
        multiplier = min(3.5, 1 + (new_streak - 1) * 0.06)
        gems = 10 if new_streak % 7 == 0 else 0
        booster = 30 if new_streak % 5 == 0 else 0
        return RetentionReward(True, new_streak, weekly, monthly, round(180 * multiplier), round(140 * multiplier), gems, booster, self.streak_visual(new_streak))

    def streak_visual(self, streak_day: int) -> str:
        filled = min(7, ((streak_day - 1) % 7) + 1)
        return "🔥" * filled + "▫️" * (7 - filled)

    def quest_rotation(self, user_id: int, today: date | None = None) -> list[QuestDefinition]:
        day = today or datetime.now(UTC).date()
        offset = (day.toordinal() + user_id) % len(self.DAILY_QUESTS)
        daily = [self.DAILY_QUESTS[offset], self.DAILY_QUESTS[(offset + 1) % len(self.DAILY_QUESTS)]]
        return [*daily, *self.WEEKLY_QUESTS, *self.SEASONAL_MISSIONS]

    def progress(self, quest: QuestDefinition, metrics: dict[str, int]) -> QuestProgress:
        current = min(metrics.get(quest.metric, 0), quest.target)
        percent = round(current / quest.target * 100)
        return QuestProgress(quest, current, current >= quest.target, percent)

    def battle_pass_xp(self, base_xp: int, booster_active: bool, premium: bool, event_multiplier: float = 1.0) -> int:
        premium_multiplier = 1.2 if premium else 1.0
        booster_multiplier = 1.5 if booster_active else 1.0
        return round(base_xp * premium_multiplier * booster_multiplier * event_multiplier)
