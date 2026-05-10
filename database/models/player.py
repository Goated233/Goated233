from sqlalchemy import BigInteger, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base, TimestampMixin, json_default
from sqlalchemy import JSON


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username_cache: Mapped[str] = mapped_column(String(128))
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_game_banned: Mapped[bool] = mapped_column(default=False)
    is_blacklisted: Mapped[bool] = mapped_column(default=False)
    shadow_muted_notifications: Mapped[bool] = mapped_column(default=False)

    profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan")


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    level: Mapped[int] = mapped_column(default=1)
    xp: Mapped[int] = mapped_column(BigInteger, default=0)
    coins: Mapped[int] = mapped_column(BigInteger, default=0)
    gems: Mapped[int] = mapped_column(BigInteger, default=0)
    title: Mapped[str] = mapped_column(String(128), default="Rookie")
    ranked_rating: Mapped[int] = mapped_column(default=1000)
    equipped_cosmetics: Mapped[dict] = mapped_column(JSON, default=json_default)
    progression: Mapped[dict] = mapped_column(JSON, default=json_default)

    user: Mapped[User] = relationship(back_populates="profile")

    __table_args__ = (Index("ix_profiles_xp", "xp"), Index("ix_profiles_ranked_rating", "ranked_rating"))


class RankedRating(Base, TimestampMixin):
    __tablename__ = "ranked_ratings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    game_id: Mapped[str] = mapped_column(String(96))
    rating: Mapped[int] = mapped_column(default=1000)
    wins: Mapped[int] = mapped_column(default=0)
    losses: Mapped[int] = mapped_column(default=0)

    __table_args__ = (UniqueConstraint("user_id", "game_id", name="uq_ranked_user_game"),)
