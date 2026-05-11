from dataclasses import dataclass
from enum import StrEnum
from ui.branding.identity import RARITY_PALETTE, THEMES


class CosmeticSlot(StrEnum):
    THEME = "theme"
    BORDER = "border"
    BADGE = "badge"
    BANNER = "banner"
    ICON = "icon"


@dataclass(frozen=True)
class CosmeticDefinition:
    id: str
    name: str
    slot: CosmeticSlot
    rarity: str
    source: str
    preview: str
    seasonal: bool = False
    event_exclusive: bool = False


class CosmeticsService:
    CATALOG = [
        CosmeticDefinition("theme_omega", "Omega Violet Theme", CosmeticSlot.THEME, "epic", "starter", THEMES["omega"].banner),
        CosmeticDefinition("border_solar", "Solar Crown Border", CosmeticSlot.BORDER, "legendary", "shop", "☀️ ══ PROFILE ══ ☀️"),
        CosmeticDefinition("badge_founder", "Founder Badge", CosmeticSlot.BADGE, "mythic", "owner_event", "🌌 Founder"),
        CosmeticDefinition("banner_corruption", "Corruption Invasion Banner", CosmeticSlot.BANNER, "legendary", "world_event", "🌑 CORRUPTION HERO", event_exclusive=True),
        CosmeticDefinition("icon_dragon", "Vault Dragon Icon", CosmeticSlot.ICON, "epic", "boss_drop", "🐉"),
    ]

    def catalog_for_slot(self, slot: CosmeticSlot | None = None) -> list[CosmeticDefinition]:
        return [item for item in self.CATALOG if slot is None or item.slot == slot]

    def rarity_color(self, rarity: str) -> int:
        return int(RARITY_PALETTE.get(rarity, RARITY_PALETTE["common"])["color"])

    def preview_lines(self, owned_ids: set[str]) -> list[str]:
        lines = []
        for item in self.CATALOG:
            owned = "✅" if item.id in owned_ids else "🔒"
            rarity = RARITY_PALETTE[item.rarity]
            limited = " • Event" if item.event_exclusive else ""
            lines.append(f"{owned} {rarity['emoji']} **{item.name}** `{item.slot.value}`{limited}\n{item.preview}")
        return lines
