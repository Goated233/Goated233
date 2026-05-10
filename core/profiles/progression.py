from dataclasses import dataclass
from datetime import UTC, date, datetime


@dataclass(frozen=True)
class LevelProgress:
    level: int
    current_level_xp: int
    next_level_xp: int
    total_xp: int
    leveled_up: bool
    unlocked_titles: list[str]


class ProgressionService:
    """Addictive XP, streak, daily reward, quest, and milestone calculations."""

    def xp_required_for_level(self, level: int) -> int:
        return int(125 * (level**1.72) + 400 * level)

    def level_for_xp(self, xp: int) -> int:
        level = 1
        while xp >= self.total_xp_for_level(level + 1):
            level += 1
        return level

    def total_xp_for_level(self, level: int) -> int:
        return sum(self.xp_required_for_level(step) for step in range(1, max(level, 1)))

    def apply_xp(self, current_xp: int, gained_xp: int, current_level: int) -> LevelProgress:
        total = max(0, current_xp + gained_xp)
        new_level = self.level_for_xp(total)
        floor = self.total_xp_for_level(new_level)
        next_floor = self.total_xp_for_level(new_level + 1)
        return LevelProgress(
            level=new_level,
            current_level_xp=total - floor,
            next_level_xp=next_floor - floor,
            total_xp=total,
            leveled_up=new_level > current_level,
            unlocked_titles=self.milestone_titles(new_level, current_level),
        )

    def daily_reward(self, streak: int, claimed_on: date | None) -> dict:
        today = datetime.now(UTC).date()
        if claimed_on == today:
            return {"claimable": False, "reason": "already_claimed"}
        new_streak = streak + 1 if claimed_on and (today - claimed_on).days == 1 else 1
        multiplier = min(3.0, 1 + (new_streak - 1) * 0.08)
        return {
            "claimable": True,
            "streak": new_streak,
            "xp": round(150 * multiplier),
            "coins": round(125 * multiplier),
            "gems": 5 if new_streak % 7 == 0 else 0,
        }

    def milestone_titles(self, new_level: int, previous_level: int) -> list[str]:
        milestones = {5: "Dungeon Delver", 10: "Arcade Regular", 25: "Raid Captain", 50: "Omega Champion", 100: "Eternal Legend"}
        return [title for level, title in milestones.items() if previous_level < level <= new_level]

    def scaled_reward(self, base: int, level: int, streak: int = 0, event_multiplier: float = 1.0) -> int:
        return round(base * (1 + min(level, 100) * 0.018) * (1 + min(streak, 30) * 0.015) * event_multiplier)
