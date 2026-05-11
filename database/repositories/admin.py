from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.admin import (
    AdminActionHistory,
    AdminAssignment,
    AdminPermission,
    AdminRole,
    AuditLog,
    BlacklistEntry,
    ExploitFlag,
    MaintenanceState,
    ModerationNote,
    UserPunishment,
)
from database.models.game import GameSession
from database.models.platform import AnalyticsEvent, EconomyTransaction
from database.models.player import User


class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_permissions_for_user(self, user_id: int) -> set[str]:
        stmt = (
            select(AdminPermission.permission)
            .join(AdminRole, AdminRole.id == AdminPermission.role_id)
            .join(AdminAssignment, AdminAssignment.role_id == AdminRole.id)
            .where(AdminAssignment.user_id == user_id)
        )
        rows = await self.session.execute(stmt)
        return set(rows.scalars().all())

    async def create_audit_log(
        self,
        *,
        actor_discord_id: int,
        action_type: str,
        reason: str,
        target_discord_id: int | None = None,
        guild_id: int | None = None,
        metadata: dict | None = None,
        rollback_metadata: dict | None = None,
        category: str = "admin",
    ) -> AuditLog:
        audit = AuditLog(
            actor_discord_id=actor_discord_id,
            target_discord_id=target_discord_id,
            action_type=action_type,
            reason=reason,
            guild_id=guild_id,
            metadata_json=metadata or {},
            rollback_metadata=rollback_metadata or {},
        )
        self.session.add(audit)
        await self.session.flush()
        self.session.add(
            AdminActionHistory(
                audit_log_id=audit.id,
                actor_discord_id=actor_discord_id,
                category=category,
                metadata_json=metadata or {},
            )
        )
        return audit

    async def latest_audits(self, limit: int = 10) -> list[AuditLog]:
        result = await self.session.execute(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit))
        return list(result.scalars().all())

    async def platform_counts(self) -> dict[str, int]:
        async def count(model: type) -> int:
            result = await self.session.execute(select(func.count()).select_from(model))
            return int(result.scalar_one())

        active_sessions = await self.session.execute(
            select(func.count()).select_from(GameSession).where(GameSession.status.in_(["lobby", "active"]))
        )
        return {
            "users": await count(User),
            "active_sessions": int(active_sessions.scalar_one()),
            "analytics_events": await count(AnalyticsEvent),
            "economy_transactions": await count(EconomyTransaction),
            "exploit_flags": await count(ExploitFlag),
        }

    async def create_punishment(
        self, target_user_id: int, actor_discord_id: int, punishment_type: str, reason: str
    ) -> UserPunishment:
        punishment = UserPunishment(
            target_user_id=target_user_id,
            actor_discord_id=actor_discord_id,
            punishment_type=punishment_type,
            reason=reason,
        )
        self.session.add(punishment)
        return punishment

    async def blacklist(self, target_discord_id: int, actor_discord_id: int, reason: str) -> BlacklistEntry:
        entry = BlacklistEntry(
            target_discord_id=target_discord_id,
            actor_discord_id=actor_discord_id,
            reason=reason,
        )
        self.session.add(entry)
        return entry

    async def add_note(self, target_discord_id: int, actor_discord_id: int, note: str) -> ModerationNote:
        moderation_note = ModerationNote(
            target_discord_id=target_discord_id, actor_discord_id=actor_discord_id, note=note
        )
        self.session.add(moderation_note)
        return moderation_note

    async def maintenance_state(self) -> MaintenanceState | None:
        result = await self.session.execute(select(MaintenanceState).order_by(desc(MaintenanceState.id)).limit(1))
        return result.scalar_one_or_none()
