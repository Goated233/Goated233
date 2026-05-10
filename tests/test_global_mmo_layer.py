import asyncio
from types import SimpleNamespace

from core.clans.service import (
    ClanContributionType,
    ClanCreateRequest,
    ClanPermission,
    ClanRole,
    ClanService,
    ClanWarService,
)
from core.feed.service import FeedEventType, FeedPage, GlobalFeedService
from core.matchmaking.service import MatchmakingService, MatchmakingTicket
from core.social.service import InviteType, PresenceStatus, SocialGraph, SocialService
from core.world import RegionStatus, WorldMapService
from core.world_bosses.service import WorldBossService, WorldRegion


class FakeClanSession:
    def __init__(self, clan):
        self.clan = clan

    async def get(self, model, clan_id):
        assert clan_id == self.clan.id
        return self.clan


class FakeQueueStore:
    def __init__(self):
        self.queues = {}

    async def enqueue(self, queue_name, payload):
        self.queues.setdefault(queue_name, []).append(payload)

    async def dequeue(self, queue_name):
        if not self.queues.get(queue_name):
            return None
        return self.queues[queue_name].pop(0)


def make_clan(clan_id: int, name: str, tag: str, owner_id: int, xp: int = 0):
    request = ClanCreateRequest(name=name, tag=tag, owner_user_id=owner_id, description=f"{name} desc")
    return SimpleNamespace(id=clan_id, name=name, tag=tag, xp=xp, bank_coins=0, metadata_json=ClanService(None).default_metadata(request))


def test_cross_server_clan_identity_membership_contributions_and_permissions():
    asyncio.run(_cross_server_clan_identity_membership_contributions_and_permissions())


async def _cross_server_clan_identity_membership_contributions_and_permissions():
    clan = make_clan(7, "Astral Wolves", "WOLF", 100, xp=900)
    service = ClanService(FakeClanSession(clan))

    await service.add_member(clan.id, user_id=200, server_id=111, role=ClanRole.MEMBER)
    await service.add_member(clan.id, user_id=300, server_id=222, role=ClanRole.OFFICER)
    await service.contribute(clan.id, user_id=200, xp=2_500, coins=500, contribution_type=ClanContributionType.DUNGEON, season_id="s1")
    await service.update_identity(clan.id, icon="🐺", banner="void_howl", theme="midnight_gold", announcement="Rally at the Void Sea.")

    profile = service.profile(clan, global_rank=1)
    member_page = service.member_page(clan, page=1, page_size=2)

    assert profile.icon == "🐺"
    assert profile.member_count == 3
    assert profile.level >= 2
    assert profile.global_rank == 1
    assert member_page.has_next is True
    assert {row["user_id"] for row in member_page.members} == {100, 200}
    assert service.has_permission(clan, 300, ClanPermission.DECLARE_WAR) is True
    assert clan.metadata_json["member_servers"]["200"] == [111]
    assert clan.metadata_json["member_servers"]["300"] == [222]
    assert clan.metadata_json["seasonal"]["s1"]["xp"] == 2_500


def test_clan_war_scoring_scoreboard_and_rewards():
    war_service = ClanWarService()
    war = war_service.declare_war(attacker_clan_id=1, defender_clan_id=2, season_id="season-zero")

    dungeon_score = war_service.record_contribution(war, 1, user_id=10, contribution_type=ClanContributionType.DUNGEON, amount=100)
    pvp_score = war_service.record_contribution(war, 2, user_id=20, contribution_type=ClanContributionType.PVP, amount=50)
    boss_score = war_service.record_contribution(war, 1, user_id=11, contribution_type=ClanContributionType.WORLD_BOSS, amount=200)

    scoreboard = war_service.scoreboard(war)
    rewards = war_service.complete_war(war)

    assert dungeon_score == 800
    assert pvp_score == 500
    assert boss_score == 1_200
    assert scoreboard[0][1] == 1
    assert rewards["winner_clan_id"] == 1
    assert rewards["prestige"] == 1


def test_global_feed_broadcasts_filtering_embeds_and_cache_payloads():
    feed = GlobalFeedService()
    events = [
        feed.rare_drop("Nova", "Omega Relic", "legendary", "Dungeon Raid"),
        feed.world_first("Mira", "Frost Rift Mythic Clear", region="Frost Rift"),
        feed.clan_war_victory("Astral Wolves", "Void Ravens", "season-zero", 2400),
        feed.world_boss_kill("Void Titan", "Kai", clan_name="Astral Wolves"),
    ]

    clan_page = feed.feed_page(events, limit=2, page=1, category="clans")
    specs = feed.embed_specs(events)
    payload = feed.cache_payload(events)

    assert isinstance(clan_page, FeedPage)
    assert clan_page.events[0].event_type == FeedEventType.CLAN_VICTORY
    assert specs[0].title.startswith("🌐")
    assert specs[0].color != specs[1].color
    assert payload[0]["id"]
    assert payload[0]["category"] == "loot"


def test_global_social_cross_server_party_presence_recent_players_and_challenges():
    service = SocialService()
    graph = SocialGraph()
    service.add_friend(graph, 1, 2)
    service.mutual_clan(graph, 1, 2, clan_id=99)
    service.set_presence(graph, 2, PresenceStatus.IN_GAME, current_game="dungeon_raid", current_party_id="party-1", mutual_clan_id=99)
    party = service.create_party(leader_id=1, game_id="dungeon_raid", home_guild_id=111)
    service.join_party(party, user_id=2, source_guild_id=222)
    invite = service.create_invite(InviteType.PARTY, 1, 2, "dungeon_raid", source_guild_id=111, target_guild_id=222)
    challenge = service.challenge_request(1, 3, "anime_duel", wager_coins=100)
    service.track_recent_players(graph, 1, [2, 3, 4])

    friends = service.friends_list(graph, 1)
    assert party.cross_server is True
    assert "Omega network" in invite.message
    assert "100" in challenge.message
    assert friends[0].status == PresenceStatus.IN_GAME
    assert graph.recent_players[1] == [4, 3, 2]


def test_global_matchmaking_uses_shared_region_queue_across_guilds():
    asyncio.run(_global_matchmaking_uses_shared_region_queue_across_guilds())


async def _global_matchmaking_uses_shared_region_queue_across_guilds():
    queues = FakeQueueStore()
    service = MatchmakingService(queues)
    await service.enqueue(MatchmakingTicket(discord_id=10, user_id=1, game_id="anime_duel", mode="casual", rating=1000, guild_id=111))
    await service.enqueue(MatchmakingTicket(discord_id=20, user_id=2, game_id="anime_duel", mode="casual", rating=1000, guild_id=222))

    result = await service.try_match("anime_duel", "casual", needed_players=2, rating=1000)

    assert result.matched is True
    assert {ticket.guild_id for ticket in result.tickets} == {111, 222}
    assert {ticket.user_id for ticket in result.tickets} == {1, 2}


def test_world_boss_regions_live_tracking_clan_rewards_and_world_map_hooks():
    boss_service = WorldBossService()
    boss = boss_service.scheduled_spawn(day_number=4, region=WorldRegion.VOID_SEA)
    boss_service.apply_damage(boss, user_id=1, damage=100_000, clan_id=10, faction_id="umbra_court")
    boss_service.apply_damage(boss, user_id=2, damage=50_000, clan_id=20, faction_id="dawn_vanguard")

    live = boss_service.live_payload(boss)
    reward = boss_service.clan_reward(clan_rank=1, damage=100_000)
    map_service = WorldMapService()
    regions = map_service.starter_regions()
    map_service.assign_clan_territory_hook(regions[0], clan_id=10, faction_id="umbra_court")
    snapshot = map_service.seasonal_map_snapshot("season-zero", regions)

    assert live["region"] == WorldRegion.VOID_SEA.value
    assert live["participants_online"] == 2
    assert boss_service.clan_rankings(boss)[0][1] == 10
    assert reward["badge"] == "world_boss_vanguard"
    assert regions[0].status == RegionStatus.CONTESTED
    assert snapshot["regions"][0]["controlling_clan_id"] == 10
