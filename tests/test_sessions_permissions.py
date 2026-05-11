from types import SimpleNamespace
import asyncio
from core.admin.permissions import AdminPermissionName, PermissionService
from core.sessions.manager import DistributedSessionManager


class FakeSessionStore:
    def __init__(self):
        self.sessions = {}
        self.user_sessions = {}
        self.tokens = {}
        self.deleted = []

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
        self.deleted.append(session_id)

    async def mark_reconnect_token(self, session_id, discord_id, token):
        self.tokens[(discord_id, token)] = session_id

    async def consume_reconnect_token(self, discord_id, token):
        return self.tokens.pop((discord_id, token), None)

    async def cleanup_stale(self, stale_before_timestamp):
        return 0

    async def list_active_ids(self, limit=100):
        return list(self.sessions)[:limit]


def test_session_manager_prevents_duplicates_and_reconnects():
    asyncio.run(_session_manager_prevents_duplicates_and_reconnects())


async def _session_manager_prevents_duplicates_and_reconnects():
    manager = DistributedSessionManager(FakeSessionStore())
    first = await manager.start_session(game_id="dungeon_raid", mode="solo", owner_discord_id=1, player_discord_ids=[1], guild_id=None, channel_id=None)
    assert first.started is True
    duplicate = await manager.start_session(game_id="dungeon_raid", mode="solo", owner_discord_id=1, player_discord_ids=[1], guild_id=None, channel_id=None)
    assert duplicate.started is False
    token = await manager.create_reconnect_token(first.session.session_id, 1)
    reconnected = await manager.reconnect(1, token)
    assert reconnected is not None
    assert reconnected.session_id == first.session.session_id


def test_owner_permission_bypasses_everything():
    asyncio.run(_owner_permission_bypasses_everything())


async def _owner_permission_bypasses_everything():
    settings = SimpleNamespace(owner_user_id=1417262684990083142, owner_display="ntmhaha")
    service = PermissionService(settings)
    context = await service.build_context(settings.owner_user_id, "ignored", set())
    assert context.is_owner is True
    assert context.has(AdminPermissionName.MAINTENANCE)
    service.assert_permission(context, AdminPermissionName.GLOBAL_BROADCAST)
