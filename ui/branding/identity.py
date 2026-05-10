from dataclasses import dataclass
from enum import StrEnum


class BrandColor(StrEnum):
    VOID = "void"
    OMEGA = "omega"
    NEBULA = "nebula"
    GOLD = "gold"
    DANGER = "danger"
    SUCCESS = "success"


class Badge(StrEnum):
    FOUNDER = "founder"
    FIRST_CLEAR = "first_clear"
    RAID_MVP = "raid_mvp"
    WORLD_FIRST = "world_first"
    SEASON_CHAMPION = "season_champion"
    LEGENDARY_DROP = "legendary_drop"


BRAND_COLORS = {
    BrandColor.VOID: 0x111827,
    BrandColor.OMEGA: 0x7C3AED,
    BrandColor.NEBULA: 0x0EA5E9,
    BrandColor.GOLD: 0xF59E0B,
    BrandColor.DANGER: 0xEF4444,
    BrandColor.SUCCESS: 0x22C55E,
}

RARITY_PALETTE = {
    "common": {"emoji": "⚪", "color": 0x94A3B8, "label": "Common"},
    "uncommon": {"emoji": "🟢", "color": 0x22C55E, "label": "Uncommon"},
    "rare": {"emoji": "🔵", "color": 0x3B82F6, "label": "Rare"},
    "epic": {"emoji": "🟣", "color": 0xA855F7, "label": "Epic"},
    "legendary": {"emoji": "🟠", "color": 0xF97316, "label": "Legendary"},
    "mythic": {"emoji": "🌈", "color": 0xEC4899, "label": "Mythic"},
}

BADGE_EMOJIS = {
    Badge.FOUNDER: "🌌",
    Badge.FIRST_CLEAR: "🗡️",
    Badge.RAID_MVP: "👑",
    Badge.WORLD_FIRST: "🌍",
    Badge.SEASON_CHAMPION: "🏆",
    Badge.LEGENDARY_DROP: "🟠",
}

GAME_ICONS = {
    "dungeon_raid": "🗡️",
    "boss_battle": "🐉",
    "blackjack": "🃏",
    "mafia": "🎭",
    "empire_conquest": "🏰",
    "cosmic_fishing": "🎣",
    "space_mining": "⛏️",
    "anime_duel": "⚡",
}


@dataclass(frozen=True)
class ThemeToken:
    id: str
    name: str
    color: int
    border_emoji: str
    banner: str


THEMES = {
    "omega": ThemeToken("omega", "Omega Violet", BRAND_COLORS[BrandColor.OMEGA], "💜", "🌌 OMEGA // ARCADE"),
    "solar": ThemeToken("solar", "Solar Gold", BRAND_COLORS[BrandColor.GOLD], "☀️", "✨ SOLAR CHAMPION"),
    "abyss": ThemeToken("abyss", "Abyss Black", BRAND_COLORS[BrandColor.VOID], "🖤", "🌑 ABYSS WALKER"),
    "mythic": ThemeToken("mythic", "Mythic Prism", RARITY_PALETTE["mythic"]["color"], "🌈", "💫 MYTHIC PROFILE"),
}


def compact_stat(label: str, value: int | str, emoji: str) -> str:
    return f"{emoji} **{label}:** `{value}`"
