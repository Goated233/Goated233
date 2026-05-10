from dataclasses import dataclass
from enum import StrEnum


class DungeonModifier(StrEnum):
    ENDLESS = "endless"
    CURSED = "cursed"
    TREASURE_GOBLINS = "treasure_goblins"
    MYTHIC_STORM = "mythic_storm"
    COOP_SYNERGY = "coop_synergy"


@dataclass(frozen=True)
class LegendaryBoss:
    id: str
    name: str
    mechanic: str
    mythic_drop: str
    announcement: str


@dataclass(frozen=True)
class RandomEncounter:
    id: str
    name: str
    description: str
    reward_modifier: float
    risk_modifier: float


LEGENDARY_BOSSES = [
    LegendaryBoss("eclipse_seraph", "Eclipse Seraph", "Alternates shield and burst phases every round.", "seraph_prism", "🌘 The Eclipse Seraph descends into Dungeon Raid!"),
    LegendaryBoss("mythic_behemoth", "Mythic Behemoth", "Gains rage unless players rotate abilities.", "behemoth_heart", "🌈 A Mythic Behemoth shakes the arcade!"),
]

RANDOM_ENCOUNTERS = [
    RandomEncounter("hidden_merchant", "Hidden Merchant", "Trade coins for a chance at rare relics.", 1.2, 0.1),
    RandomEncounter("lost_shrine", "Lost Shrine", "Gain a team buff before the next elite room.", 1.0, 0.0),
    RandomEncounter("mimic_cache", "Mimic Cache", "A chest with teeth. Defeat it for bonus loot.", 1.6, 1.35),
]


class DungeonChallengeService:
    def modifiers_for_tier(self, tier: int, endless: bool = False) -> list[DungeonModifier]:
        modifiers = []
        if endless:
            modifiers.append(DungeonModifier.ENDLESS)
        if tier >= 3:
            modifiers.append(DungeonModifier.TREASURE_GOBLINS)
        if tier >= 5:
            modifiers.append(DungeonModifier.CURSED)
        if tier >= 7:
            modifiers.append(DungeonModifier.MYTHIC_STORM)
        if tier >= 2:
            modifiers.append(DungeonModifier.COOP_SYNERGY)
        return modifiers

    def reward_multiplier(self, modifiers: list[DungeonModifier]) -> float:
        multiplier = 1.0
        if DungeonModifier.ENDLESS in modifiers:
            multiplier += 0.35
        if DungeonModifier.CURSED in modifiers:
            multiplier += 0.4
        if DungeonModifier.MYTHIC_STORM in modifiers:
            multiplier += 0.75
        return multiplier

    def hidden_room_chance(self, tier: int, party_size: int) -> float:
        return min(0.35, 0.05 + tier * 0.025 + max(0, party_size - 1) * 0.03)
