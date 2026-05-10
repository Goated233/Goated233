from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class FactionAlignment(StrEnum):
    DAWN = "dawn"
    UMBRA = "umbra"
    WILD = "wild"
    NEUTRAL = "neutral"


class RegionStatus(StrEnum):
    PEACEFUL = "peaceful"
    CONTESTED = "contested"
    EVENT = "event"
    WARZONE = "warzone"


@dataclass(frozen=True)
class Faction:
    id: str
    name: str
    alignment: FactionAlignment
    description: str
    seasonal_score: int = 0


@dataclass
class WorldRegionState:
    id: str
    name: str
    status: RegionStatus
    controlling_faction_id: str | None = None
    controlling_clan_id: int | None = None
    active_event_id: str | None = None
    modifiers: list[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class WorldMapService:
    DEFAULT_FACTIONS = [
        Faction("dawn_vanguard", "Dawn Vanguard", FactionAlignment.DAWN, "Explorers who secure new gateways into the Omega world."),
        Faction("umbra_court", "Umbra Court", FactionAlignment.UMBRA, "Strategists who bend shadows, markets, and warfronts."),
        Faction("wild_accord", "Wild Accord", FactionAlignment.WILD, "Raiders and beast-tamers bound to living regions."),
    ]

    def starter_regions(self) -> list[WorldRegionState]:
        return [
            WorldRegionState("astral_frontier", "Astral Frontier", RegionStatus.EVENT, modifiers=["new_player_surge"]),
            WorldRegionState("ember_reach", "Ember Reach", RegionStatus.CONTESTED, modifiers=["boss_damage_up"]),
            WorldRegionState("frost_rift", "Frost Rift", RegionStatus.PEACEFUL, modifiers=["defense_up"]),
            WorldRegionState("void_sea", "Void Sea", RegionStatus.WARZONE, modifiers=["war_score_up"]),
        ]

    def assign_clan_territory_hook(self, region: WorldRegionState, clan_id: int, faction_id: str | None = None) -> WorldRegionState:
        region.controlling_clan_id = clan_id
        region.controlling_faction_id = faction_id or region.controlling_faction_id
        region.status = RegionStatus.CONTESTED
        region.updated_at = datetime.now(UTC)
        return region

    def start_region_event(self, region: WorldRegionState, event_id: str, modifier: str) -> WorldRegionState:
        region.active_event_id = event_id
        region.status = RegionStatus.EVENT
        if modifier not in region.modifiers:
            region.modifiers.append(modifier)
        region.updated_at = datetime.now(UTC)
        return region

    def seasonal_map_snapshot(self, season_id: str, regions: list[WorldRegionState]) -> dict:
        return {
            "season_id": season_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "regions": [
                {
                    "id": region.id,
                    "name": region.name,
                    "status": region.status.value,
                    "controlling_faction_id": region.controlling_faction_id,
                    "controlling_clan_id": region.controlling_clan_id,
                    "active_event_id": region.active_event_id,
                    "modifiers": region.modifiers,
                }
                for region in regions
            ],
        }
