from datetime import datetime
from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import Base, TimestampMixin, json_default, list_default


class Achievement(Base, TimestampMixin):
    __tablename__ = "achievements"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(512))
    criteria: Mapped[dict] = mapped_column(JSON, default=json_default)
    points: Mapped[int] = mapped_column(default=10)


class LeaderboardSnapshot(Base, TimestampMixin):
    __tablename__ = "leaderboards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(64), index=True)
    metric: Mapped[str] = mapped_column(String(64), index=True)
    entries: Mapped[list] = mapped_column(JSON, default=list_default)
    season_id: Mapped[str | None] = mapped_column(String(96), nullable=True)


class EconomyTransaction(Base, TimestampMixin):
    __tablename__ = "economy_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    currency: Mapped[str] = mapped_column(String(32), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    balance_after: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(String(256))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)


class Clan(Base, TimestampMixin):
    __tablename__ = "clans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(96), unique=True)
    tag: Mapped[str] = mapped_column(String(8), unique=True)
    xp: Mapped[int] = mapped_column(BigInteger, default=0)
    bank_coins: Mapped[int] = mapped_column(BigInteger, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)


class Tournament(Base, TimestampMixin):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    game_id: Mapped[str] = mapped_column(String(96), index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bracket: Mapped[dict] = mapped_column(JSON, default=json_default)
    rewards: Mapped[dict] = mapped_column(JSON, default=json_default)


class WorldEvent(Base, TimestampMixin):
    __tablename__ = "world_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), index=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    modifiers: Mapped[dict] = mapped_column(JSON, default=json_default)


class Cooldown(Base, TimestampMixin):
    __tablename__ = "cooldowns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    scope: Mapped[str] = mapped_column(String(128), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic: Mapped[str] = mapped_column(String(96), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    message: Mapped[str] = mapped_column(String(1500))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)


class AnalyticsEvent(Base, TimestampMixin):
    __tablename__ = "analytics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_discord_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(96), index=True)
    subject: Mapped[str] = mapped_column(String(128), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)


class Quest(Base, TimestampMixin):
    __tablename__ = "quests"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(512))
    reward: Mapped[dict] = mapped_column(JSON, default=json_default)
    criteria: Mapped[dict] = mapped_column(JSON, default=json_default)
