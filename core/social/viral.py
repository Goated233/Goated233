from dataclasses import dataclass
from enum import StrEnum


class SocialCardType(StrEnum):
    ACHIEVEMENT = "achievement"
    RARE_DROP = "rare_drop"
    LEADERBOARD = "leaderboard"
    RIVALRY = "rivalry"
    PROFILE = "profile"


@dataclass(frozen=True)
class ShareCard:
    card_type: SocialCardType
    title: str
    body: str
    accent: str
    call_to_action: str
    compare_lines: tuple[str, ...] = ()


class SocialViralService:
    def achievement_card(self, username: str, achievement: str, rarity: str = "legendary") -> ShareCard:
        return ShareCard(SocialCardType.ACHIEVEMENT, f"{username} unlocked {achievement}", f"A {rarity} achievement broadcast is ready to flex in chat.", "🏆", "Share Achievement", ("Profile prestige increased", "Clan feed notified"))

    def rare_drop_card(self, username: str, item_name: str, rarity: str) -> ShareCard:
        return ShareCard(SocialCardType.RARE_DROP, f"{rarity.title()} Drop: {item_name}", f"{username} pulled a showcase item that can be pinned to their profile.", "🌈" if rarity == "mythic" else "🟠", "Flex Drop", ("Inspect loadout", "Compare collection"))

    def rivalry_card(self, player: str, rival: str, stat_delta: int) -> ShareCard:
        direction = "overtook" if stat_delta >= 0 else "is chasing"
        return ShareCard(SocialCardType.RIVALRY, "Rivalry Sparked", f"{player} {direction} {rival} by `{abs(stat_delta):,}` rating.", "⚔️", "Challenge Rival", ("Queue ranked", "Spectate duel"))

    def recommended_connections(self, user_id: int, recent_players: list[int], clan_members: list[int], limit: int = 5) -> list[int]:
        ordered = []
        for candidate in [*clan_members, *recent_players]:
            if candidate != user_id and candidate not in ordered:
                ordered.append(candidate)
        return ordered[:limit]
