from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from core.economy.balancing import EconomyBalancer


class ShopSection(StrEnum):
    FEATURED = "featured"
    COSMETICS = "cosmetics"
    EVENT = "event"
    BOOSTERS = "boosters"


@dataclass(frozen=True)
class ShopOffer:
    id: str
    name: str
    section: ShopSection
    rarity: str
    price_currency: str
    price: int
    expires_at: datetime
    preview: str
    limit_per_user: int = 1


class ShopService:
    def __init__(self, balancer: EconomyBalancer | None = None):
        self.balancer = balancer or EconomyBalancer()

    def rotating_offers(self, day_number: int, inflation_index: float = 1.0) -> list[ShopOffer]:
        expires = datetime.now(UTC) + timedelta(hours=24)
        variant = day_number % 3
        featured = [
            ("solar_border", "Solar Crown Border", "legendary", 1800, "☀️ Legendary profile border"),
            ("abyss_banner", "Abyss Banner", "epic", 1200, "🌑 Animated-style abyss banner"),
            ("mythic_prism", "Mythic Prism Theme", "mythic", 2800, "🌈 Mythic profile theme"),
        ][variant]
        return [
            ShopOffer(featured[0], featured[1], ShopSection.FEATURED, featured[2], "gems", self.balancer.sink_price(featured[3], featured[2], inflation_index), expires, featured[4]),
            ShopOffer("xp_booster_30", "30m XP Booster", ShopSection.BOOSTERS, "rare", "coins", 750, expires, "⚡ +50% XP for 30 minutes", 3),
            ShopOffer("event_cache", "Event Loot Cache", ShopSection.EVENT, "epic", "coins", 1500, expires, "🎁 Chance at event-exclusive cosmetics", 5),
        ]

    def purchase_preview(self, offer: ShopOffer, balance: int) -> dict:
        return {"offer_id": offer.id, "can_afford": balance >= offer.price, "remaining": balance - offer.price, "confirmation": f"Buy {offer.name} for {offer.price:,} {offer.price_currency}?"}
