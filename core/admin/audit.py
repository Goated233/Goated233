from dataclasses import dataclass
from database.repositories.admin import AdminRepository


@dataclass(frozen=True)
class AuditRequest:
    actor_discord_id: int
    action_type: str
    reason: str
    target_discord_id: int | None = None
    guild_id: int | None = None
    metadata: dict | None = None
    rollback_metadata: dict | None = None
    category: str = "admin"


class AuditService:
    def __init__(self, repository: AdminRepository):
        self.repository = repository

    async def log(self, request: AuditRequest) -> None:
        await self.repository.create_audit_log(
            actor_discord_id=request.actor_discord_id,
            target_discord_id=request.target_discord_id,
            action_type=request.action_type,
            reason=request.reason,
            guild_id=request.guild_id,
            metadata=request.metadata,
            rollback_metadata=request.rollback_metadata,
            category=request.category,
        )
