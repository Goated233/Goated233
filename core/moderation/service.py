from sqlalchemy.ext.asyncio import AsyncSession
from core.admin.audit import AuditRequest, AuditService
from core.admin.permissions import AdminPermissionName, PermissionContext, PermissionService
from database.repositories.admin import AdminRepository
from database.repositories.profiles import ProfileRepository


class ModerationService:
    def __init__(self, session: AsyncSession, permission_service: PermissionService):
        self.session = session
        self.permissions = permission_service
        self.admin_repo = AdminRepository(session)
        self.profile_repo = ProfileRepository(session)
        self.audit = AuditService(self.admin_repo)

    async def ban_from_games(self, context: PermissionContext, target_discord_id: int, reason: str) -> None:
        self.permissions.assert_permission(context, AdminPermissionName.USER_PUNISH)
        target = await self.profile_repo.get_by_discord_id(target_discord_id)
        if target is None:
            raise ValueError("Target user does not exist in Alpha Omega Arcade yet.")
        target.is_game_banned = True
        await self.admin_repo.create_punishment(target.id, context.discord_id, "game_ban", reason)
        await self.audit.log(
            AuditRequest(
                actor_discord_id=context.discord_id,
                target_discord_id=target_discord_id,
                action_type="user.game_ban",
                reason=reason,
                rollback_metadata={"previous_is_game_banned": False},
                category="moderation",
            )
        )

    async def unban_from_games(self, context: PermissionContext, target_discord_id: int, reason: str) -> None:
        self.permissions.assert_permission(context, AdminPermissionName.USER_PUNISH)
        target = await self.profile_repo.get_by_discord_id(target_discord_id)
        if target is None:
            raise ValueError("Target user does not exist in Alpha Omega Arcade yet.")
        target.is_game_banned = False
        await self.audit.log(
            AuditRequest(
                actor_discord_id=context.discord_id,
                target_discord_id=target_discord_id,
                action_type="user.game_unban",
                reason=reason,
                rollback_metadata={"previous_is_game_banned": True},
                category="moderation",
            )
        )
