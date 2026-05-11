from datetime import datetime
from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import Base, TimestampMixin, json_default, list_default


class GameDefinition(Base, TimestampMixin):
    __tablename__ = "game_definitions"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(512))
    engine_type: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(64))
    min_players: Mapped[int] = mapped_column(default=1)
    max_players: Mapped[int] = mapped_column(default=1)
    enabled: Mapped[bool] = mapped_column(default=True)
    config: Mapped[dict] = mapped_column(JSON, default=json_default)


class PlayerStat(Base, TimestampMixin):
    __tablename__ = "stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    game_id: Mapped[str] = mapped_column(String(96))
    wins: Mapped[int] = mapped_column(default=0)
    losses: Mapped[int] = mapped_column(default=0)
    draws: Mapped[int] = mapped_column(default=0)
    xp_gained: Mapped[int] = mapped_column(BigInteger, default=0)
    coins_gained: Mapped[int] = mapped_column(BigInteger, default=0)
    matches_started: Mapped[int] = mapped_column(default=0)
    matches_completed: Mapped[int] = mapped_column(default=0)
    abandoned_matches: Mapped[int] = mapped_column(default=0)
    buttons_clicked: Mapped[int] = mapped_column(default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)

    __table_args__ = (UniqueConstraint("user_id", "game_id", name="uq_stats_user_game"),)


class GameSession(Base, TimestampMixin):
    __tablename__ = "game_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    game_id: Mapped[str] = mapped_column(String(96), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="lobby")
    mode: Mapped[str] = mapped_column(String(32), default="casual")
    guild_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    player_user_ids: Mapped[list] = mapped_column(JSON, default=list_default)
    state: Mapped[dict] = mapped_column(JSON, default=json_default)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GameResult(Base, TimestampMixin):
    __tablename__ = "game_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("game_sessions.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    game_id: Mapped[str] = mapped_column(String(96), index=True)
    outcome: Mapped[str] = mapped_column(String(32))
    xp_gained: Mapped[int] = mapped_column(default=0)
    coins_gained: Mapped[int] = mapped_column(default=0)
    gems_gained: Mapped[int] = mapped_column(default=0)
    items_gained: Mapped[list] = mapped_column(JSON, default=list_default)
    time_played_seconds: Mapped[int] = mapped_column(default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)

    __table_args__ = (Index("ix_game_results_user_created", "user_id", "created_at"),)
