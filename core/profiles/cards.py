from dataclasses import dataclass, field
from ui.branding.identity import BADGE_EMOJIS, THEMES, Badge, ThemeToken, compact_stat


@dataclass(frozen=True)
class PremiumProfile:
    username: str
    title: str
    level: int
    xp: int
    next_level_xp: int
    prestige: int
    coins: int
    gems: int
    ranked_rating: int
    clan: str | None
    seasonal_rank: str
    favorite_game: str
    theme_id: str = "omega"
    badges: list[Badge] = field(default_factory=list)
    cosmetics: dict[str, str] = field(default_factory=dict)
    achievements: list[str] = field(default_factory=list)
    recent_activity: list[str] = field(default_factory=list)


class ProfilePresentationService:
    def theme_for(self, profile: PremiumProfile) -> ThemeToken:
        return THEMES.get(profile.theme_id, THEMES["omega"])

    def badge_line(self, profile: PremiumProfile) -> str:
        if not profile.badges:
            return "▫️ No badges equipped yet"
        return " ".join(f"{BADGE_EMOJIS[badge]} `{badge.value.replace('_', ' ').title()}`" for badge in profile.badges[:5])

    def activity_lines(self, profile: PremiumProfile) -> str:
        if not profile.recent_activity:
            return "No recent activity yet — start a Dungeon Raid!"
        return "\n".join(f"• {activity}" for activity in profile.recent_activity[:4])

    def stat_line(self, profile: PremiumProfile) -> str:
        return "\n".join(
            [
                compact_stat("Level", profile.level, "⭐"),
                compact_stat("Prestige", profile.prestige, "🌟"),
                compact_stat("Rating", profile.ranked_rating, "⚔️"),
                compact_stat("Coins", f"{profile.coins:,}", "🪙"),
                compact_stat("Gems", f"{profile.gems:,}", "💎"),
            ]
        )

    def completion_percent(self, profile: PremiumProfile) -> int:
        return round(min(profile.xp / max(profile.next_level_xp, 1), 1) * 100)
