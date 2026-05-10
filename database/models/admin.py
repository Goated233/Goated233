from datetime import datetime
from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import Base, TimestampMixin, json_default


class AdminRole(Base, TimestampMixin):
    __tablename__ = "admin_roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    hierarchy: Mapped[int] = mapped_column(default=0)
    description: Mapped[str] = mapped_column(String(256), default="")
    managed: Mapped[bool] = mapped_column(default=False)


class AdminPermission(Base, TimestampMixin):
    __tablename__ = "admin_permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("admin_roles.id", ondelete="CASCADE"))
    permission: Mapped[str] = mapped_column(String(96), index=True)

    __table_args__ = (UniqueConstraint("role_id", "permission", name="uq_admin_role_permission"),)


class AdminAssignment(Base, TimestampMixin):
    __tablename__ = "admin_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(ForeignKey("admin_roles.id", ondelete="CASCADE"))
    assigned_by_discord_id: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(String(512), default="")

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_admin_assignment"),)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    target_discord_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(96), index=True)
    reason: Mapped[str] = mapped_column(String(512), default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)
    rollback_metadata: Mapped[dict] = mapped_column(JSON, default=json_default)
    guild_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class AdminActionHistory(Base, TimestampMixin):
    __tablename__ = "admin_action_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    audit_log_id: Mapped[int] = mapped_column(ForeignKey("audit_logs.id", ondelete="CASCADE"))
    actor_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)


class UserPunishment(Base, TimestampMixin):
    __tablename__ = "user_punishments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    actor_discord_id: Mapped[int] = mapped_column(BigInteger)
    punishment_type: Mapped[str] = mapped_column(String(64), index=True)
    reason: Mapped[str] = mapped_column(String(512))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active: Mapped[bool] = mapped_column(default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)


class BlacklistEntry(Base, TimestampMixin):
    __tablename__ = "blacklist_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_discord_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    actor_discord_id: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(String(512))
    active: Mapped[bool] = mapped_column(default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)


class ModerationNote(Base, TimestampMixin):
    __tablename__ = "moderation_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    actor_discord_id: Mapped[int] = mapped_column(BigInteger)
    note: Mapped[str] = mapped_column(String(1000))
    pinned: Mapped[bool] = mapped_column(default=False)


class ExploitFlag(Base, TimestampMixin):
    __tablename__ = "exploit_flags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    evidence: Mapped[dict] = mapped_column(JSON, default=json_default)
    reviewed_by_discord_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open")


class MaintenanceState(Base, TimestampMixin):
    __tablename__ = "maintenance_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enabled: Mapped[bool] = mapped_column(default=False)
    reason: Mapped[str] = mapped_column(String(512), default="")
    enabled_by_discord_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
