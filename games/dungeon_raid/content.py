from dataclasses import dataclass
from enum import StrEnum
import random


class HeroClass(StrEnum):
    GUARDIAN = "guardian"
    RANGER = "ranger"
    ARCANIST = "arcanist"
    MEDIC = "medic"


class StatusEffect(StrEnum):
    BLEED = "bleed"
    BURN = "burn"
    SHIELD = "shield"
    INSPIRE = "inspire"
    STUN = "stun"


@dataclass(frozen=True)
class Ability:
    id: str
    name: str
    power: int
    cooldown_rounds: int
    effect: StatusEffect | None = None
    target: str = "enemy"


@dataclass(frozen=True)
class EnemyTemplate:
    id: str
    name: str
    base_hp: int
    base_damage: int
    elite_chance: float
    abilities: tuple[str, ...]


@dataclass(frozen=True)
class LootEntry:
    item_id: str
    name: str
    rarity: str
    weight: int
    min_tier: int = 1
    quantity: int = 1


ABILITIES = {
    HeroClass.GUARDIAN: [Ability("shield_bash", "Shield Bash", 24, 2, StatusEffect.STUN), Ability("bulwark", "Bulwark", 0, 3, StatusEffect.SHIELD, "ally")],
    HeroClass.RANGER: [Ability("piercing_shot", "Piercing Shot", 34, 1, StatusEffect.BLEED), Ability("volley", "Volley", 22, 2)],
    HeroClass.ARCANIST: [Ability("ember_lance", "Ember Lance", 38, 2, StatusEffect.BURN), Ability("mana_burst", "Mana Burst", 30, 1)],
    HeroClass.MEDIC: [Ability("smite", "Smite", 20, 1), Ability("revive", "Revive", 0, 5, StatusEffect.INSPIRE, "ally")],
}

ENEMIES = [
    EnemyTemplate("goblin_raider", "Goblin Raider", 80, 12, 0.08, ("slash",)),
    EnemyTemplate("crystal_slime", "Crystal Slime", 110, 10, 0.12, ("split", "slow")),
    EnemyTemplate("abyss_knight", "Abyss Knight", 150, 18, 0.16, ("cleave", "guard")),
]

BOSSES = [
    EnemyTemplate("omega_lich", "Omega Lich", 650, 28, 1.0, ("curse", "summon", "drain")),
    EnemyTemplate("vault_dragon", "Vault Dragon", 820, 34, 1.0, ("flame", "tail_sweep", "enrage")),
]

LOOT_TABLE = [
    LootEntry("iron_coin_cache", "Iron Coin Cache", "common", 42, quantity=3),
    LootEntry("goblin_charm", "Goblin Charm", "uncommon", 25),
    LootEntry("crystal_blade", "Crystal Blade", "rare", 14, 2),
    LootEntry("abyss_plate", "Abyss Plate", "epic", 7, 3),
    LootEntry("omega_relic", "Omega Relic", "legendary", 3, 4),
    LootEntry("mythic_dragon_core", "Mythic Dragon Core", "mythic", 1, 5),
]

ROOM_THEMES = ["Crypt Gate", "Mushroom Hollow", "Crystal Cavern", "Abyssal Bridge", "Vault Antechamber"]


def daily_rotation_seed(day_number: int, tier: int) -> int:
    return day_number * 10_000 + tier * 97


def choose_weighted_loot(tier: int, rng: random.Random) -> LootEntry:
    eligible = [entry for entry in LOOT_TABLE if entry.min_tier <= tier]
    total = sum(entry.weight for entry in eligible)
    roll = rng.randint(1, total)
    running = 0
    for entry in eligible:
        running += entry.weight
        if roll <= running:
            return entry
    return eligible[0]
