from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from core.feed.service import FeedEvent, FeedEventType, FeedRarity


class WorldSignalType(StrEnum):
    MERCHANT = "merchant"
    INVASION = "invasion"
    WEATHER = "weather"
    RAID = "raid"
    FACTION = "faction"
    CLAN_WAR = "clan_war"
    ECONOMY = "economy"
    SEASONAL = "seasonal"


@dataclass(frozen=True)
class WorldSignal:
    signal_type: WorldSignalType
    title: str
    narration: str
    region: str
    urgency: int
    starts_at: datetime
    ends_at: datetime
    reward_hook: str
    action_label: str


@dataclass(frozen=True)
class LivingWorldSnapshot:
    generated_at: datetime
    signals: tuple[WorldSignal, ...]
    online_count: int
    friend_activity: tuple[str, ...]
    clan_activity: tuple[str, ...]
    social_notifications: tuple[str, ...]


class LivingWorldService:
    """Deterministic ambient world simulation for rich low-population presentation."""

    REGIONS = ("Astral Frontier", "Ember Reach", "Frost Rift", "Void Sea", "Golden Bazaar")
    MERCHANTS = ("Nyx the Relic Broker", "Solari Atelier", "The Prism Caravan", "Kairo's Contraband Cart")
    FACTIONS = ("Dawn Vanguard", "Umbra Court", "Wild Accord")
    WEATHER = ("meteor rain", "void aurora", "ember winds", "frost bloom")

    def snapshot(self, seed: int | None = None, now: datetime | None = None) -> LivingWorldSnapshot:
        moment = now or datetime.now(UTC)
        slot = seed if seed is not None else moment.hour + moment.timetuple().tm_yday
        signals = (
            self._merchant_signal(slot, moment),
            self._invasion_signal(slot + 1, moment),
            self._faction_signal(slot + 2, moment),
            self._weather_signal(slot + 3, moment),
        )
        return LivingWorldSnapshot(
            generated_at=moment,
            signals=signals,
            online_count=240 + (slot * 37) % 900,
            friend_activity=("Mira queued for Anime Duel", "Jax found an Epic Rune", "Kade is spectating Void Titan"),
            clan_activity=("Astral Wolves gained 2,400 war score", "Void Ravens opened 3 raid slots", "Solar Kin leveled their clan bank"),
            social_notifications=("2 friends online", "1 party invite pending", "3 clan applications need review"),
        )

    def feed_events(self, snapshot: LivingWorldSnapshot) -> list[FeedEvent]:
        events = []
        for signal in snapshot.signals:
            event_type = FeedEventType.WORLD_EVENT if signal.signal_type != WorldSignalType.CLAN_WAR else FeedEventType.CLAN_WAR
            rarity = FeedRarity.LEGENDARY.value if signal.urgency >= 85 else FeedRarity.EPIC.value if signal.urgency >= 70 else FeedRarity.RARE.value
            events.append(
                FeedEvent(
                    event_type,
                    signal.title,
                    signal.narration,
                    signal.urgency,
                    snapshot.generated_at,
                    {"region": signal.region, "reward_hook": signal.reward_hook, "action": signal.action_label},
                    category="world",
                    rarity=rarity,
                )
            )
        return events

    def dashboard_lines(self, snapshot: LivingWorldSnapshot, limit: int = 4) -> list[str]:
        return [
            f"{self._icon(signal.signal_type)} **{signal.title}** · `{signal.region}` · {signal.action_label}"
            for signal in sorted(snapshot.signals, key=lambda item: item.urgency, reverse=True)[:limit]
        ]

    def rotating_countdown(self, signal: WorldSignal, now: datetime | None = None) -> str:
        seconds = max(0, round((signal.ends_at - (now or datetime.now(UTC))).total_seconds()))
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m" if hours else f"{minutes}m"

    def _merchant_signal(self, slot: int, now: datetime) -> WorldSignal:
        merchant = self.MERCHANTS[slot % len(self.MERCHANTS)]
        region = self.REGIONS[slot % len(self.REGIONS)]
        return WorldSignal(WorldSignalType.MERCHANT, "Traveling Merchant Sighted", f"**{merchant}** unfolded a radiant stall in **{region}**. Limited cosmetics shimmer for the next rotation.", region, 68, now, now + timedelta(hours=3), "exclusive_cosmetic", "Open Shop")

    def _invasion_signal(self, slot: int, now: datetime) -> WorldSignal:
        region = self.REGIONS[slot % len(self.REGIONS)]
        return WorldSignal(WorldSignalType.INVASION, "Invasion Rift Opening", f"A hostile rift tears through **{region}**. Parties that respond now earn boosted battle-pass XP and invasion titles.", region, 92, now, now + timedelta(hours=2), "battle_pass_xp_boost", "Join Event")

    def _faction_signal(self, slot: int, now: datetime) -> WorldSignal:
        faction = self.FACTIONS[slot % len(self.FACTIONS)]
        region = self.REGIONS[(slot + 1) % len(self.REGIONS)]
        return WorldSignal(WorldSignalType.FACTION, "Faction Momentum Shift", f"The **{faction}** seized momentum near **{region}**. Clan contributions there echo louder on the war board.", region, 76, now, now + timedelta(hours=4), "faction_score", "View Map")

    def _weather_signal(self, slot: int, now: datetime) -> WorldSignal:
        weather = self.WEATHER[slot % len(self.WEATHER)]
        region = self.REGIONS[(slot + 2) % len(self.REGIONS)]
        return WorldSignal(WorldSignalType.WEATHER, "Seasonal Weather Surge", f"A **{weather}** rolls across **{region}**, changing drop flavor and dungeon narration for this hour.", region, 61, now, now + timedelta(hours=1), "regional_modifier", "Browse Games")

    def _icon(self, signal_type: WorldSignalType) -> str:
        return {
            WorldSignalType.MERCHANT: "🛒",
            WorldSignalType.INVASION: "🚨",
            WorldSignalType.WEATHER: "🌌",
            WorldSignalType.RAID: "🐉",
            WorldSignalType.FACTION: "🏰",
            WorldSignalType.CLAN_WAR: "⚔️",
            WorldSignalType.ECONOMY: "💱",
            WorldSignalType.SEASONAL: "✨",
        }[signal_type]
