from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha1

from ui.embeds.theme import COLORS


class FeedEventType(StrEnum):
    RARE_DROP = "rare_drop"
    LEADERBOARD = "leaderboard"
    WORLD_BOSS = "world_boss"
    CLAN_VICTORY = "clan_victory"
    TOURNAMENT = "tournament"
    LEVEL_UP = "level_up"
    WORLD_EVENT = "world_event"
    WORLD_FIRST = "world_first"
    PRESTIGE = "prestige"
    CLAN_WAR = "clan_war"
    COSMETIC = "cosmetic"


class FeedRarity(StrEnum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


RARITY_COLORS = {
    FeedRarity.COMMON.value: COLORS["info"],
    FeedRarity.RARE.value: 0x2563EB,
    FeedRarity.EPIC.value: COLORS["primary"],
    FeedRarity.LEGENDARY.value: COLORS["legendary"],
    FeedRarity.MYTHIC.value: 0xEC4899,
}


@dataclass(frozen=True)
class FeedEvent:
    event_type: FeedEventType
    title: str
    body: str
    priority: int
    created_at: datetime
    metadata: dict
    category: str = "global"
    rarity: str = FeedRarity.COMMON.value
    id: str = ""

    def stable_id(self) -> str:
        if self.id:
            return self.id
        seed = f"{self.event_type}:{self.title}:{self.created_at.isoformat()}:{self.body}"
        return sha1(seed.encode(), usedforsecurity=False).hexdigest()[:12]


@dataclass(frozen=True)
class FeedPage:
    events: list[FeedEvent]
    page: int
    total_pages: int
    category: str | None
    has_next: bool
    has_previous: bool


@dataclass(frozen=True)
class FeedEmbedSpec:
    title: str
    description: str
    color: int
    timestamp: datetime
    footer: str
    fields: list[tuple[str, str]] = field(default_factory=list)


class GlobalFeedService:
    """Builds global platform broadcasts that can be cached or rendered by Discord views."""

    def rare_drop(self, username: str, item_name: str, rarity: str, game_name: str) -> FeedEvent:
        normalized = rarity.lower()
        priority = 100 if normalized in {FeedRarity.LEGENDARY, FeedRarity.MYTHIC} else 40
        return FeedEvent(
            FeedEventType.RARE_DROP,
            f"{normalized.title()} Drop!",
            f"{username} found **{item_name}** in {game_name}.",
            priority,
            datetime.now(UTC),
            {"rarity": normalized, "game": game_name},
            category="loot",
            rarity=normalized,
        )

    def leaderboard_dethrone(self, old_name: str, new_name: str, board: str) -> FeedEvent:
        return FeedEvent(
            FeedEventType.LEADERBOARD,
            "Leaderboard Dethroned",
            f"**{new_name}** passed **{old_name}** on `{board}`.",
            90,
            datetime.now(UTC),
            {"board": board},
            category="leaderboards",
            rarity=FeedRarity.EPIC.value,
        )

    def level_up(self, username: str, level: int) -> FeedEvent:
        return FeedEvent(
            FeedEventType.LEVEL_UP,
            "Level Up",
            f"**{username}** reached level `{level}`!",
            30 + level // 5,
            datetime.now(UTC),
            {"level": level},
            category="progression",
        )

    def world_first(self, username: str, achievement: str, region: str | None = None) -> FeedEvent:
        region_text = f" in {region}" if region else ""
        return FeedEvent(
            FeedEventType.WORLD_FIRST,
            "World-First Achievement",
            f"The Omega network records **{username}** as first to complete **{achievement}**{region_text}.",
            120,
            datetime.now(UTC),
            {"achievement": achievement, "region": region},
            category="achievements",
            rarity=FeedRarity.MYTHIC.value,
        )

    def clan_war_victory(self, clan_name: str, opponent_name: str, season_id: str, score: int) -> FeedEvent:
        return FeedEvent(
            FeedEventType.CLAN_VICTORY,
            "Clan War Victory",
            f"**{clan_name}** defeated **{opponent_name}** in `{season_id}` with `{score:,}` war score.",
            110,
            datetime.now(UTC),
            {"season_id": season_id, "score": score},
            category="clans",
            rarity=FeedRarity.LEGENDARY.value,
        )

    def world_boss_kill(self, boss_name: str, slayer_name: str, clan_name: str | None = None) -> FeedEvent:
        clan_text = f" alongside **{clan_name}**" if clan_name else ""
        return FeedEvent(
            FeedEventType.WORLD_BOSS,
            "World Boss Defeated",
            f"**{boss_name}** has fallen to **{slayer_name}**{clan_text}. The realm trembles in victory.",
            115,
            datetime.now(UTC),
            {"boss": boss_name, "slayer": slayer_name, "clan": clan_name},
            category="events",
            rarity=FeedRarity.LEGENDARY.value,
        )

    def tournament_win(self, username: str, tournament_name: str) -> FeedEvent:
        return FeedEvent(
            FeedEventType.TOURNAMENT,
            "Tournament Champion",
            f"**{username}** claimed the crown in **{tournament_name}**.",
            95,
            datetime.now(UTC),
            {"tournament": tournament_name},
            category="competitive",
            rarity=FeedRarity.EPIC.value,
        )

    def prestige_unlock(self, clan_or_user: str, prestige: int) -> FeedEvent:
        return FeedEvent(
            FeedEventType.PRESTIGE,
            "Prestige Awakened",
            f"**{clan_or_user}** unlocked Prestige `{prestige}` and etched their name into the Omega archives.",
            100 + prestige,
            datetime.now(UTC),
            {"prestige": prestige},
            category="progression",
            rarity=FeedRarity.LEGENDARY.value,
        )

    def clan_level_up(self, clan_name: str, level: int) -> FeedEvent:
        return FeedEvent(
            FeedEventType.LEVEL_UP,
            "Clan Level Up",
            f"**{clan_name}** reached Guild Level `{level}`. Their banner burns brighter across every server.",
            75 + level,
            datetime.now(UTC),
            {"level": level, "clan": clan_name},
            category="clans",
            rarity=FeedRarity.RARE.value,
        )

    def rare_cosmetic(self, username: str, cosmetic_name: str, rarity: str) -> FeedEvent:
        return FeedEvent(
            FeedEventType.COSMETIC,
            "Rare Cosmetic Unlocked",
            f"**{username}** unlocked the **{cosmetic_name}** cosmetic.",
            85,
            datetime.now(UTC),
            {"cosmetic": cosmetic_name, "rarity": rarity},
            category="cosmetics",
            rarity=rarity.lower(),
        )

    def feed_page(
        self,
        events: list[FeedEvent],
        limit: int = 8,
        page: int = 1,
        category: str | None = None,
    ) -> FeedPage | list[FeedEvent]:
        filtered = [event for event in events if category is None or event.category == category]
        ordered = sorted(filtered, key=lambda event: (event.priority, event.created_at), reverse=True)
        if page == 1 and category is None:
            return ordered[:limit]
        total_pages = max(1, (len(ordered) + limit - 1) // limit)
        safe_page = min(max(1, page), total_pages)
        start = (safe_page - 1) * limit
        return FeedPage(ordered[start : start + limit], safe_page, total_pages, category, safe_page < total_pages, safe_page > 1)

    def embed_specs(self, events: list[FeedEvent], mobile: bool = True) -> list[FeedEmbedSpec]:
        specs = []
        for event in events:
            body = event.body if not mobile or len(event.body) <= 180 else f"{event.body[:177]}..."
            specs.append(
                FeedEmbedSpec(
                    title=f"🌐 {event.title}",
                    description=body,
                    color=RARITY_COLORS.get(event.rarity, COLORS["primary"]),
                    timestamp=event.created_at,
                    footer=f"Alpha Omega Global Feed • {event.category} • {event.stable_id()}",
                    fields=[("Signal", event.event_type.value.replace("_", " ").title())],
                )
            )
        return specs

    def cache_payload(self, events: list[FeedEvent]) -> list[dict]:
        return [
            {
                "id": event.stable_id(),
                "event_type": event.event_type.value,
                "title": event.title,
                "body": event.body,
                "priority": event.priority,
                "created_at": event.created_at.isoformat(),
                "metadata": event.metadata,
                "category": event.category,
                "rarity": event.rarity,
            }
            for event in events
        ]
