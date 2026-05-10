from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from ui.embeds.progress import progress_bar


class WorldRegion(StrEnum):
    ASTRAL_FRONTIER = "astral_frontier"
    EMBER_REACH = "ember_reach"
    FROST_RIFT = "frost_rift"
    VOID_SEA = "void_sea"


class BossModifier(StrEnum):
    ARMORED = "armored"
    ENRAGED = "enraged"
    TREASURE_HOARD = "treasure_hoard"
    CLAN_GLORY = "clan_glory"
    FACTION_SURGE = "faction_surge"
    REGION_VOLATILE = "region_volatile"


@dataclass
class WorldBossState:
    id: str
    name: str
    max_hp: int
    hp: int
    starts_at: datetime
    ends_at: datetime
    modifiers: list[BossModifier]
    damage_by_user: dict[int, int] = field(default_factory=dict)
    clan_damage: dict[int, int] = field(default_factory=dict)
    region: WorldRegion = WorldRegion.ASTRAL_FRONTIER
    faction_damage: dict[str, int] = field(default_factory=dict)
    participants_online: set[int] = field(default_factory=set)
    event_chain_id: str | None = None


class WorldBossService:
    BOSS_ROTATION = [
        ("void_titan", "Void Titan", 1_000_000, [BossModifier.ARMORED, BossModifier.CLAN_GLORY]),
        ("solar_wyrm", "Solar Wyrm", 750_000, [BossModifier.ENRAGED, BossModifier.TREASURE_HOARD]),
        ("omega_colossus", "Omega Colossus", 1_250_000, [BossModifier.TREASURE_HOARD]),
    ]

    def scheduled_spawn(self, day_number: int | None = None, now: datetime | None = None, region: WorldRegion | None = None) -> WorldBossState:
        moment = now or datetime.now(UTC)
        day = day_number or moment.timetuple().tm_yday
        boss_id, name, hp, modifiers = self.BOSS_ROTATION[day % len(self.BOSS_ROTATION)]
        chosen_region = region or list(WorldRegion)[day % len(WorldRegion)]
        active_modifiers = list(modifiers) + self.region_modifiers(chosen_region)
        return WorldBossState(boss_id, name, hp, hp, moment, moment + timedelta(hours=6), active_modifiers, region=chosen_region, event_chain_id=f"chain-{day // 7}")

    def apply_damage(self, boss: WorldBossState, user_id: int, damage: int, clan_id: int | None = None, faction_id: str | None = None) -> WorldBossState:
        actual = max(0, round(damage * (0.72 if BossModifier.ARMORED in boss.modifiers else 1.0)))
        boss.hp = max(0, boss.hp - actual)
        boss.damage_by_user[user_id] = boss.damage_by_user.get(user_id, 0) + actual
        boss.participants_online.add(user_id)
        if clan_id is not None:
            boss.clan_damage[clan_id] = boss.clan_damage.get(clan_id, 0) + actual
        if faction_id is not None:
            boss.faction_damage[faction_id] = boss.faction_damage.get(faction_id, 0) + actual
        return boss

    def damage_rankings(self, boss: WorldBossState, limit: int = 10) -> list[tuple[int, int, int]]:
        ranked = sorted(boss.damage_by_user.items(), key=lambda row: row[1], reverse=True)[:limit]
        return [(index + 1, user_id, damage) for index, (user_id, damage) in enumerate(ranked)]

    def reward_tier(self, rank: int, damage: int) -> dict:
        if rank == 1:
            return {"xp": 3000, "coins": 5000, "gems": 125, "badge": "raid_mvp"}
        if rank <= 10:
            return {"xp": 1800, "coins": 2500, "gems": 50}
        if damage > 0:
            return {"xp": 750, "coins": 800, "gems": 10}
        return {"xp": 0, "coins": 0, "gems": 0}

    def clan_rankings(self, boss: WorldBossState, limit: int = 10) -> list[tuple[int, int, int]]:
        ranked = sorted(boss.clan_damage.items(), key=lambda row: row[1], reverse=True)[:limit]
        return [(index + 1, clan_id, damage) for index, (clan_id, damage) in enumerate(ranked)]

    def live_payload(self, boss: WorldBossState) -> dict:
        return {
            "id": boss.id,
            "name": boss.name,
            "hp": boss.hp,
            "max_hp": boss.max_hp,
            "region": boss.region.value,
            "modifiers": [modifier.value for modifier in boss.modifiers],
            "participants_online": len(boss.participants_online),
            "top_clans": self.clan_rankings(boss, 3),
            "ends_at": boss.ends_at.isoformat(),
        }

    def scheduled_event_rotation(self, start_day: int, count: int = 3) -> list[WorldBossState]:
        return [self.scheduled_spawn(day_number=start_day + offset) for offset in range(count)]

    def region_modifiers(self, region: WorldRegion) -> list[BossModifier]:
        if region == WorldRegion.EMBER_REACH:
            return [BossModifier.ENRAGED]
        if region == WorldRegion.FROST_RIFT:
            return [BossModifier.ARMORED]
        if region == WorldRegion.VOID_SEA:
            return [BossModifier.FACTION_SURGE]
        return [BossModifier.REGION_VOLATILE]

    def clan_reward(self, clan_rank: int, damage: int) -> dict:
        if clan_rank == 1:
            return {"clan_xp": 2500, "bank_coins": 4000, "badge": "world_boss_vanguard"}
        if clan_rank <= 5:
            return {"clan_xp": 1200, "bank_coins": 1500}
        return {"clan_xp": 400 if damage else 0, "bank_coins": 500 if damage else 0}

    def boss_intro(self, boss: WorldBossState) -> str:
        return f"A rift tears open above {boss.region.value.replace('_', ' ').title()} — **{boss.name}** has entered the Omega world."

    def hp_visual(self, boss: WorldBossState) -> str:
        return f"{progress_bar(boss.hp, boss.max_hp, 18)} `{boss.hp:,}/{boss.max_hp:,}`"
