from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import random
from games.dungeon_raid.content import (
    ABILITIES,
    BOSSES,
    ENEMIES,
    ROOM_THEMES,
    HeroClass,
    StatusEffect,
    choose_weighted_loot,
    daily_rotation_seed,
)


@dataclass
class DungeonEnemy:
    id: str
    name: str
    hp: int
    damage: int
    elite: bool
    statuses: list[str] = field(default_factory=list)


@dataclass
class DungeonRoom:
    index: int
    theme: str
    enemy: DungeonEnemy
    cleared: bool = False
    boss_room: bool = False


@dataclass
class DungeonPlayerState:
    discord_id: int
    hero_class: HeroClass
    hp: int = 100
    max_hp: int = 100
    damage_done: int = 0
    revived: bool = False
    statuses: list[str] = field(default_factory=list)
    cooldowns: dict[str, int] = field(default_factory=dict)


@dataclass
class DungeonRunState:
    tier: int
    rooms: list[DungeonRoom]
    players: dict[int, DungeonPlayerState]
    room_index: int = 0
    combat_log: list[str] = field(default_factory=list)
    loot: list[dict] = field(default_factory=list)

    @property
    def current_room(self) -> DungeonRoom:
        return self.rooms[self.room_index]


class DungeonRaidDirector:
    """Procedural Dungeon Raid director for scaling rooms, elite enemies, bosses, AI, and loot."""

    def generate_run(self, player_ids: list[int], tier: int, day_number: int | None = None) -> DungeonRunState:
        day = day_number or datetime.now(UTC).timetuple().tm_yday
        rng = random.Random(daily_rotation_seed(day, tier))
        room_count = min(8, 3 + tier)
        rooms: list[DungeonRoom] = []
        for index in range(room_count):
            boss_room = index == room_count - 1
            template = rng.choice(BOSSES if boss_room else ENEMIES)
            elite = boss_room or rng.random() < template.elite_chance + tier * 0.015
            hp_scale = 1 + tier * 0.22 + len(player_ids) * 0.18
            damage_scale = 1 + tier * 0.13
            enemy = DungeonEnemy(
                id=template.id,
                name=("Elite " if elite and not boss_room else "") + template.name,
                hp=round(template.base_hp * hp_scale * (1.45 if elite else 1)),
                damage=round(template.base_damage * damage_scale * (1.25 if elite else 1)),
                elite=elite,
            )
            rooms.append(
                DungeonRoom(
                    index=index,
                    theme=rng.choice(ROOM_THEMES),
                    enemy=enemy,
                    boss_room=boss_room,
                )
            )
        classes = list(HeroClass)
        players = {
            player_id: DungeonPlayerState(discord_id=player_id, hero_class=classes[i % len(classes)])
            for i, player_id in enumerate(player_ids)
        }
        return DungeonRunState(tier=tier, rooms=rooms, players=players)

    def player_action(self, run: DungeonRunState, discord_id: int, ability_id: str) -> DungeonRunState:
        player = run.players[discord_id]
        room = run.current_room
        ability = next((ability for ability in ABILITIES[player.hero_class] if ability.id == ability_id), ABILITIES[player.hero_class][0])
        if player.cooldowns.get(ability.id, 0) > 0:
            run.combat_log.append(f"⏳ <@{discord_id}> tried **{ability.name}**, but it is still cooling down.")
            return run
        if ability.target == "ally" and ability.effect == StatusEffect.SHIELD:
            player.statuses.append(StatusEffect.SHIELD.value)
            run.combat_log.append(f"🛡️ <@{discord_id}> raised **{ability.name}** and shielded the party.")
        elif ability.target == "ally" and ability.effect == StatusEffect.INSPIRE:
            revived = self._revive_ally(run)
            run.combat_log.append(f"✨ <@{discord_id}> used **{ability.name}** and {'revived an ally' if revived else 'inspired the team'}.")
        else:
            damage = self._scaled_damage(ability.power, run.tier, player)
            room.enemy.hp = max(0, room.enemy.hp - damage)
            player.damage_done += damage
            if ability.effect:
                room.enemy.statuses.append(ability.effect.value)
            run.combat_log.append(f"⚔️ <@{discord_id}> used **{ability.name}** for `{damage}` damage.")
        player.cooldowns[ability.id] = ability.cooldown_rounds
        if room.enemy.hp == 0:
            self._clear_room(run)
        else:
            self.enemy_turn(run)
        self._tick_cooldowns(run)
        run.combat_log = run.combat_log[-8:]
        return run

    def enemy_turn(self, run: DungeonRunState) -> None:
        room = run.current_room
        living = [player for player in run.players.values() if player.hp > 0]
        if not living:
            run.combat_log.append("💀 The party has fallen. Use revive or reconnect for recovery.")
            return
        target = min(living, key=lambda player: player.hp)
        damage = room.enemy.damage
        if StatusEffect.SHIELD.value in target.statuses:
            damage = round(damage * 0.45)
            target.statuses.remove(StatusEffect.SHIELD.value)
        target.hp = max(0, target.hp - damage)
        run.combat_log.append(f"👹 **{room.enemy.name}** hit <@{target.discord_id}> for `{damage}` damage.")

    def _clear_room(self, run: DungeonRunState) -> None:
        room = run.current_room
        room.cleared = True
        loot = choose_weighted_loot(run.tier, random.Random(room.index + run.tier * 31))
        run.loot.append({"item_id": loot.item_id, "name": loot.name, "rarity": loot.rarity, "quantity": loot.quantity})
        run.combat_log.append(f"🎁 Cleared **{room.theme}** and found **{loot.name}**!")
        if run.room_index < len(run.rooms) - 1:
            run.room_index += 1
            run.combat_log.append(f"🚪 Entering **{run.current_room.theme}**...")
        else:
            run.combat_log.append("🏆 Dungeon complete! Claim your rewards.")

    def _revive_ally(self, run: DungeonRunState) -> bool:
        fallen = next((player for player in run.players.values() if player.hp <= 0 and not player.revived), None)
        if not fallen:
            return False
        fallen.hp = round(fallen.max_hp * 0.45)
        fallen.revived = True
        fallen.statuses.append(StatusEffect.INSPIRE.value)
        return True

    def _scaled_damage(self, power: int, tier: int, player: DungeonPlayerState) -> int:
        inspire = 1.18 if StatusEffect.INSPIRE.value in player.statuses else 1.0
        return round(power * (1 + tier * 0.09) * inspire)

    def _tick_cooldowns(self, run: DungeonRunState) -> None:
        for player in run.players.values():
            for ability_id, remaining in list(player.cooldowns.items()):
                player.cooldowns[ability_id] = max(0, remaining - 1)


def dungeon_to_dict(run: DungeonRunState) -> dict:
    return asdict(run)


def dungeon_from_dict(payload: dict) -> DungeonRunState:
    rooms = []
    for room_data in payload.get("rooms", []):
        enemy_data = room_data["enemy"]
        rooms.append(
            DungeonRoom(
                index=int(room_data["index"]),
                theme=str(room_data["theme"]),
                enemy=DungeonEnemy(
                    id=str(enemy_data["id"]),
                    name=str(enemy_data["name"]),
                    hp=int(enemy_data["hp"]),
                    damage=int(enemy_data["damage"]),
                    elite=bool(enemy_data["elite"]),
                    statuses=list(enemy_data.get("statuses", [])),
                ),
                cleared=bool(room_data.get("cleared", False)),
                boss_room=bool(room_data.get("boss_room", False)),
            )
        )
    players = {
        int(discord_id): DungeonPlayerState(
            discord_id=int(player_data["discord_id"]),
            hero_class=HeroClass(str(player_data["hero_class"])),
            hp=int(player_data.get("hp", 100)),
            max_hp=int(player_data.get("max_hp", 100)),
            damage_done=int(player_data.get("damage_done", 0)),
            revived=bool(player_data.get("revived", False)),
            statuses=list(player_data.get("statuses", [])),
            cooldowns={str(key): int(value) for key, value in player_data.get("cooldowns", {}).items()},
        )
        for discord_id, player_data in payload.get("players", {}).items()
    }
    return DungeonRunState(
        tier=int(payload.get("tier", 1)),
        rooms=rooms,
        players=players,
        room_index=int(payload.get("room_index", 0)),
        combat_log=list(payload.get("combat_log", [])),
        loot=list(payload.get("loot", [])),
    )
