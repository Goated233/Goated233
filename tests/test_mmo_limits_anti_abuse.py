import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from core.clans.service import ClanCreateRequest, ClanLimitState, ClanRole, ClanService, ClanWarService
from core.economy.anti_abuse import EconomyGuard, EconomyGuardState, MAX_CURRENCY_BALANCE
from core.interactions import InteractionGuard
from core.limits import LimitReason, LimitViolation
from core.matchmaking.service import MatchmakingGuardState, MatchmakingService, MatchmakingTicket
from core.retention.service import RetentionService
from core.sessions.manager import DistributedSessionManager
from core.social.service import InviteType, SocialGraph, SocialService
from core.tournaments.service import TournamentService
from core.world_bosses.service import WorldBossService


class FakeQueueStore:
    def __init__(self):
        self.queues = {}

    async def enqueue(self, queue_name, payload):
        self.queues.setdefault(queue_name, []).append(payload)

    async def dequeue(self, queue_name):
        if not self.queues.get(queue_name):
            return None
        return self.queues[queue_name].pop(0)


class FakeSessionStore:
    def __init__(self):
        self.sessions = {}
        self.user_sessions = {}
        self.locks = set()

    async def active_count(self):
        return len(self.sessions)

    async def active_for_user(self, discord_id):
        return self.user_sessions.get(discord_id)

    async def save(self, session_id, state):
        self.sessions[session_id] = state
        for player_id in state.get("player_discord_ids", []):
            self.user_sessions[player_id] = session_id

    async def load(self, session_id):
        return self.sessions.get(session_id)

    async def delete(self, session_id):
        state = self.sessions.pop(session_id, None)
        if state:
            for player_id in state.get("player_discord_ids", []):
                self.user_sessions.pop(player_id, None)

    async def acquire_lock(self, session_id, actor_id):
        lock = SimpleNamespace(acquired=session_id not in self.locks)
        self.locks.add(session_id)
        return lock

    async def release_lock(self, lock):
        self.locks.clear()

    async def mark_reconnect_token(self, session_id, discord_id, token):
        self.user_sessions[(discord_id, token)] = session_id

    async def consume_reconnect_token(self, discord_id, token):
        return self.user_sessions.pop((discord_id, token), None)

    async def cleanup_stale(self, stale_before_timestamp):
        return 0

    async def list_active_ids(self, limit=100):
        return list(self.sessions)[:limit]


class FakeClanSession:
    def __init__(self, clan):
        self.clan = clan

    async def get(self, model, clan_id):
        return self.clan if clan_id == self.clan.id else None


def make_clan(clan_id=1, owner_id=10):
    service = ClanService(None)
    request = ClanCreateRequest("Omega Guard", "GUARD", owner_id, "Protected guild")
    return SimpleNamespace(id=clan_id, name="Omega Guard", tag="GUARD", xp=1000, bank_coins=20_000, metadata_json=service.default_metadata(request))


def test_party_limits_duplicate_invites_cooldowns_and_transfer_recovery():
    social = SocialService()
    graph = SocialGraph()
    party = social.create_party(1, "dungeon_raid", graph=graph)
    with pytest.raises(LimitViolation) as duplicate_party:
        social.create_party(1, "dungeon_raid", graph=graph)
    assert duplicate_party.value.result.reason == LimitReason.DUPLICATE

    social.join_party(party, 2, graph=graph)
    social.transfer_ownership(graph, party.id, 1, 2)
    assert party.leader_id == 2
    invite = social.create_invite(InviteType.PARTY, 2, 3, "dungeon_raid", graph=graph)
    with pytest.raises(LimitViolation) as duplicate_invite:
        social.create_invite(InviteType.PARTY, 2, 3, "dungeon_raid", graph=graph)
    assert duplicate_invite.value.result.reason == LimitReason.COOLDOWN
    recovered = social.recover_party(graph, 1)
    assert recovered.id == party.id
    invite = SocialService().create_invite(InviteType.PARTY, 4, 5, graph=graph)
    graph.invites[invite.id] = SimpleNamespace(**{**invite.__dict__, "expires_at": datetime.now(UTC) - timedelta(seconds=1), "expired": lambda now=None: True})
    assert social.cleanup_stale_invites(graph) >= 1


def test_clan_limits_one_clan_requirements_roster_capacity_war_and_upgrade_duplicates():
    limits = ClanLimitState()
    clan = make_clan(owner_id=10)
    service = ClanService(FakeClanSession(clan), limits=limits)
    with pytest.raises(LimitViolation) as low_level:
        service.validate_creation_requirements(99, user_level=1, user_coins=100_000)
    assert low_level.value.result.reason == LimitReason.REQUIREMENT

    asyncio.run(service.add_member(clan.id, 20, role=ClanRole.OFFICER))
    with pytest.raises(LimitViolation):
        asyncio.run(service.add_member(clan.id, 20))
    asyncio.run(service.invite_member(clan.id, 20, 30))
    with pytest.raises(LimitViolation) as duplicate_invite:
        asyncio.run(service.invite_member(clan.id, 20, 30))
    assert duplicate_invite.value.result.reason in {LimitReason.COOLDOWN, LimitReason.DUPLICATE}
    service.purchase_upgrade(clan, "vault_1", 1000, {"bank_bonus": 1.1})
    with pytest.raises(LimitViolation):
        service.purchase_upgrade(clan, "vault_1", 1000, {"bank_bonus": 1.1})
    war_service = ClanWarService()
    war_service.declare_war(1, 2, "s1", limits=limits)
    with pytest.raises(LimitViolation) as war_cooldown:
        war_service.declare_war(1, 3, "s1", limits=limits)
    assert war_cooldown.value.result.reason == LimitReason.COOLDOWN


def test_matchmaking_duplicate_queue_timeout_and_abandon_penalty():
    asyncio.run(_matchmaking_duplicate_queue_timeout_and_abandon_penalty())


async def _matchmaking_duplicate_queue_timeout_and_abandon_penalty():
    guard = MatchmakingGuardState()
    service = MatchmakingService(FakeQueueStore(), guard=guard)
    ticket = MatchmakingTicket(1, 1, "anime_duel", "ranked", 1000)
    await service.enqueue(ticket)
    with pytest.raises(LimitViolation) as duplicate:
        await service.enqueue(ticket)
    assert duplicate.value.result.reason == LimitReason.DUPLICATE
    service.record_abandonment(1, afk=True)
    with pytest.raises(LimitViolation) as penalty:
        await service.enqueue(ticket)
    assert penalty.value.result.reason == LimitReason.COOLDOWN
    guard.penalties.clear()
    guard.active_ticket_by_user[2] = "matchmaking:global:test"
    guard.enqueued_at["matchmaking:global:test:2"] = datetime.now(UTC) - timedelta(seconds=999)
    assert service.cleanup_timeouts() == 1
    assert 2 not in guard.active_ticket_by_user


def test_economy_daily_duplicate_overflow_trade_and_purchase_limits():
    guard = EconomyGuard(EconomyGuardState())
    guard.claim_daily(1)
    with pytest.raises(LimitViolation) as daily:
        guard.claim_daily(1)
    assert daily.value.result.reason == LimitReason.COOLDOWN
    guard.validate_transaction(1, "coins", 100, 0, "reward-key")
    with pytest.raises(LimitViolation):
        guard.validate_transaction(1, "coins", 100, 0, "reward-key")
    with pytest.raises(LimitViolation):
        guard.validate_transaction(1, "coins", 100, MAX_CURRENCY_BALANCE, "overflow")
    with pytest.raises(LimitViolation):
        guard.validate_trade(1, 1, 100, 1000)
    for _ in range(10):
        guard.purchase_allowed(1, 1, 100)
    with pytest.raises(LimitViolation):
        guard.purchase_allowed(1, 1, 100)
    retention = RetentionService(guard)
    with pytest.raises(LimitViolation):
        retention.claim_login_reward(1, None, 0)


def test_sessions_interactions_world_and_tournament_duplicate_rewards():
    asyncio.run(_sessions_interactions_world_and_tournament_duplicate_rewards())


async def _sessions_interactions_world_and_tournament_duplicate_rewards():
    manager = DistributedSessionManager(FakeSessionStore(), max_concurrent_sessions=1)
    first = await manager.start_session(game_id="dungeon_raid", mode="solo", owner_discord_id=1, player_discord_ids=[1], guild_id=None, channel_id=None)
    assert first.started is True
    duplicate = await manager.start_session(game_id="dungeon_raid", mode="solo", owner_discord_id=1, player_discord_ids=[1], guild_id=None, channel_id=None)
    assert duplicate.started is False
    assert await manager.with_interaction_lock(first.session.session_id, 1, "click-1") is True
    assert await manager.with_interaction_lock(first.session.session_id, 1, "click-1") is False
    await manager.mark_reward_claimed(first.session.session_id, "clear:1")
    with pytest.raises(LimitViolation):
        await manager.mark_reward_claimed(first.session.session_id, "clear:1")

    interactions = InteractionGuard()
    interactions.validate(interaction_id="i1", user_id=1, component_id="attack")
    interactions.release("attack")
    with pytest.raises(LimitViolation):
        interactions.validate(interaction_id="i1", user_id=1, component_id="attack")

    boss_service = WorldBossService()
    boss = boss_service.scheduled_spawn(day_number=2)
    boss_service.apply_damage(boss, 1, 1000)
    boss_service.claim_reward(boss, 1)
    with pytest.raises(LimitViolation):
        boss_service.claim_reward(boss, 1)

    tournament = TournamentService().create("cup", "Cup", "dungeon_raid")
    TournamentService().signup(tournament, 1)
    with pytest.raises(LimitViolation):
        TournamentService().signup(tournament, 1)
