from core.economy.balancing import EconomyBalancer, EconomyGrant
from core.profiles.progression import ProgressionService
from games.dungeon_raid.runtime import DungeonRaidDirector, dungeon_from_dict, dungeon_to_dict


def test_progression_levels_daily_rewards_and_titles():
    service = ProgressionService()
    progress = service.apply_xp(current_xp=0, gained_xp=service.total_xp_for_level(5), current_level=1)
    assert progress.level >= 5
    assert progress.leveled_up is True
    assert "Dungeon Delver" in progress.unlocked_titles
    reward = service.daily_reward(streak=6, claimed_on=None)
    assert reward["claimable"] is True
    assert reward["coins"] > 0


def test_economy_balancer_caps_sinks_and_idempotency():
    balancer = EconomyBalancer()
    assert balancer.reward_cap(user_level=500, game_id="dungeon_raid", base_amount=999_999) == 4500
    assert balancer.sink_price(base_price=100, rarity="legendary", inflation_index=1.2) == 900
    key = balancer.idempotency_key(1, "dungeon", "abc")
    assert balancer.verify_grant(EconomyGrant("coins", 100, "test", key, {})) is True


def test_dungeon_state_serializes_and_combat_advances():
    director = DungeonRaidDirector()
    run = director.generate_run([123], tier=2, day_number=42)
    payload = dungeon_to_dict(run)
    restored = dungeon_from_dict(payload)
    assert restored.tier == 2
    assert len(restored.rooms) == 5
    before_hp = restored.current_room.enemy.hp
    restored = director.player_action(restored, 123, "shield_bash")
    assert restored.current_room.enemy.hp < before_hp or restored.current_room.cleared
    assert restored.combat_log
