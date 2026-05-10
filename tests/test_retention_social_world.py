from datetime import UTC, datetime, timedelta
from core.cosmetics.service import CosmeticsService, CosmeticSlot
from core.feed.service import FeedEventType, GlobalFeedService
from core.retention.service import RetentionService
from core.shop.service import ShopService
from core.social.service import InviteType, SocialService
from core.tournaments.service import TournamentService, TournamentStatus
from core.world_bosses.service import WorldBossService
from games.dungeon_raid.advanced import DungeonChallengeService, DungeonModifier
from games.registry import ALL_GAMES


def test_retention_rewards_quests_and_battle_pass_boosters():
    service = RetentionService()
    yesterday = datetime.now(UTC).date() - timedelta(days=1)
    reward = service.login_reward(yesterday, 6)
    assert reward.claimable is True
    assert reward.streak_day == 7
    assert reward.gems == 10
    quests = service.quest_rotation(user_id=42, today=yesterday)
    progress = service.progress(quests[0], {quests[0].metric: quests[0].target})
    assert progress.completed is True
    assert service.battle_pass_xp(100, booster_active=True, premium=True) == 180


def test_social_feed_cosmetics_and_shop_rotation():
    cosmetics = CosmeticsService()
    assert cosmetics.catalog_for_slot(CosmeticSlot.THEME)
    assert any("Omega Violet" in line for line in cosmetics.preview_lines({"theme_omega"}))
    invite = SocialService().create_invite(InviteType.CHALLENGE, 1, 2, "anime_duel")
    assert invite.game_id == "anime_duel"
    feed = GlobalFeedService().rare_drop("Nova", "Omega Relic", "legendary", "Dungeon Raid")
    assert feed.event_type == FeedEventType.RARE_DROP
    offers = ShopService().rotating_offers(day_number=3)
    assert len(offers) == 3
    assert offers[0].price > 0


def test_world_boss_tournament_dungeon_modifiers_and_expanded_games():
    boss_service = WorldBossService()
    boss = boss_service.scheduled_spawn(day_number=1)
    boss_service.apply_damage(boss, user_id=10, damage=50_000, clan_id=99)
    assert boss.hp < boss.max_hp
    assert boss_service.damage_rankings(boss)[0][1] == 10
    tournament_service = TournamentService()
    tournament = tournament_service.create("cup", "Omega Cup", "dungeon_raid", 5)
    tournament_service.signup(tournament, 10)
    tournament_service.signup(tournament, 20)
    tournament_service.generate_bracket(tournament)
    assert tournament.status == TournamentStatus.ACTIVE
    modifiers = DungeonChallengeService().modifiers_for_tier(7, endless=True)
    assert DungeonModifier.MYTHIC_STORM in modifiers
    assert len(ALL_GAMES) >= 20
