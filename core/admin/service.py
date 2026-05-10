from dataclasses import dataclass
from datetime import datetime, timezone
from discord import Client
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.config import Settings
from core.admin.audit import AuditRequest, AuditService
from core.admin.permissions import AdminPermissionName, PermissionContext, PermissionService
from database.repositories.admin import AdminRepository
from database.repositories.profiles import ProfileRepository
from redis.asyncio import Redis
from infra.redis.cooldowns import CooldownStore
from infra.redis.sessions import SessionStore


@dataclass(frozen=True)
class PlatformStats:
    server_count: int
    shard_count: int
    active_users: int
    active_games: int
    active_sessions: int
    database_status: str
    redis_status: str
    uptime_seconds: int


class AdminService:
    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession],
        redis: Redis,
        session_store: SessionStore,
        client: Client,
        started_at: datetime,
    ):
        self.settings = settings
        self.session_factory = session_factory
        self.redis = redis
        self.session_store = session_store
        self.client = client
        self.started_at = started_at
        self.permissions = PermissionService(settings)
        self.cooldowns = CooldownStore(redis, settings.owner_user_id)

    async def context_for_user(self, discord_id: int, display_name: str) -> PermissionContext:
        if self.permissions.is_owner(discord_id):
            return await self.permissions.build_context(discord_id, display_name, set())
        async with self.session_factory() as session:
            user = await ProfileRepository(session).get_by_discord_id(discord_id)
            permissions = await AdminRepository(session).get_permissions_for_user(user.id) if user else set()
        return await self.permissions.build_context(discord_id, display_name, permissions)

    async def platform_stats(self) -> PlatformStats:
        database_status = "online"
        redis_status = "online"
        active_sessions = 0
        active_users = 0
        active_games = 0
        try:
            await self.redis.ping()
            active_sessions = await self.session_store.active_count()
        except Exception:
            redis_status = "degraded"
        try:
            async with self.session_factory() as session:
                repo = AdminRepository(session)
                counts = await repo.platform_counts()
                active_users = counts["users"]
                active_games = counts["active_sessions"]
        except Exception:
            database_status = "degraded"
        uptime = int((datetime.now(timezone.utc) - self.started_at).total_seconds())
        return PlatformStats(
            server_count=len(self.client.guilds),
            shard_count=self.client.shard_count or 1,
            active_users=active_users,
            active_games=active_games,
            active_sessions=active_sessions,
            database_status=database_status,
            redis_status=redis_status,
            uptime_seconds=uptime,
        )

    async def assert_admin_access(self, context: PermissionContext) -> None:
        self.permissions.assert_permission(context, AdminPermissionName.ADMIN_VIEW)

    async def dangerous_action_allowed(self, actor_discord_id: int, scope: str) -> tuple[bool, int, bool]:
        result = await self.cooldowns.consume(
            f"dangerous:{scope}", actor_discord_id, self.settings.dangerous_action_cooldown_seconds
        )
        return result.allowed, result.retry_after_seconds, result.bypassed

    async def audit(self, request: AuditRequest) -> None:
        async with self.session_factory() as session:
            service = AuditService(AdminRepository(session))
            await service.log(request)
            await session.commit()
