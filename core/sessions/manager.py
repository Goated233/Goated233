from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4
from infra.redis.sessions import SessionStore


class SessionStatus(StrEnum):
    LOBBY = "lobby"
    ACTIVE = "active"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class ActiveSession:
    session_id: str
    game_id: str
    mode: str
    guild_id: int | None
    channel_id: int | None
    owner_discord_id: int
    player_discord_ids: list[int]
    status: SessionStatus = SessionStatus.LOBBY
    state: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_redis(self) -> dict:
        return {
            "session_id": self.session_id,
            "game_id": self.game_id,
            "mode": self.mode,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "owner_discord_id": self.owner_discord_id,
            "player_discord_ids": self.player_discord_ids,
            "status": self.status.value,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def from_redis(cls, payload: dict) -> "ActiveSession":
        return cls(
            session_id=str(payload["session_id"]),
            game_id=str(payload["game_id"]),
            mode=str(payload["mode"]),
            guild_id=payload.get("guild_id"),
            channel_id=payload.get("channel_id"),
            owner_discord_id=int(payload["owner_discord_id"]),
            player_discord_ids=[int(player_id) for player_id in payload.get("player_discord_ids", [])],
            status=SessionStatus(str(payload.get("status", SessionStatus.LOBBY.value))),
            state=dict(payload.get("state", {})),
            created_at=str(payload.get("created_at", datetime.now(UTC).isoformat())),
            updated_at=str(payload.get("updated_at", datetime.now(UTC).isoformat())),
        )


@dataclass(frozen=True)
class SessionStartResult:
    started: bool
    session: ActiveSession | None
    existing_session_id: str | None = None
    reason: str | None = None


class DistributedSessionManager:
    """Coordinates game session lifecycle across shards/workers via Redis."""

    def __init__(self, store: SessionStore, timeout_seconds: int = 1800):
        self.store = store
        self.timeout_seconds = timeout_seconds

    async def start_session(
        self,
        *,
        game_id: str,
        mode: str,
        owner_discord_id: int,
        player_discord_ids: list[int],
        guild_id: int | None,
        channel_id: int | None,
        state: dict | None = None,
        force_recovery: bool = False,
    ) -> SessionStartResult:
        for player_id in player_discord_ids:
            existing = await self.store.active_for_user(player_id)
            if existing and not force_recovery:
                return SessionStartResult(False, None, existing, "player_already_in_session")
        session = ActiveSession(
            session_id=str(uuid4()),
            game_id=game_id,
            mode=mode,
            guild_id=guild_id,
            channel_id=channel_id,
            owner_discord_id=owner_discord_id,
            player_discord_ids=player_discord_ids,
            state=state or {},
        )
        await self.store.save(session.session_id, session.to_redis())
        return SessionStartResult(True, session)

    async def load_session(self, session_id: str) -> ActiveSession | None:
        payload = await self.store.load(session_id)
        return ActiveSession.from_redis(payload) if payload else None

    async def with_interaction_lock(self, session_id: str, actor_discord_id: int) -> bool:
        lock = await self.store.acquire_lock(session_id, actor_discord_id)
        if not lock.acquired:
            return False
        await self.store.release_lock(lock)
        return True

    async def touch(self, session: ActiveSession) -> None:
        await self.store.save(session.session_id, session.to_redis())

    async def end_session(self, session_id: str, status: SessionStatus = SessionStatus.COMPLETED) -> None:
        session = await self.load_session(session_id)
        if session:
            session.status = status
            await self.store.save(session.session_id, session.to_redis())
        await self.store.delete(session_id)

    async def create_reconnect_token(self, session_id: str, discord_id: int) -> str:
        token = uuid4().hex[:12]
        await self.store.mark_reconnect_token(session_id, discord_id, token)
        return token

    async def reconnect(self, discord_id: int, token: str) -> ActiveSession | None:
        session_id = await self.store.consume_reconnect_token(discord_id, token)
        if not session_id:
            return None
        session = await self.load_session(session_id)
        if session:
            session.status = SessionStatus.ACTIVE
            await self.touch(session)
        return session

    async def cleanup_stale_sessions(self) -> int:
        threshold = (datetime.now(UTC) - timedelta(seconds=self.timeout_seconds)).timestamp()
        return await self.store.cleanup_stale(threshold)

    async def safe_shutdown_snapshot(self) -> list[dict]:
        snapshots: list[dict] = []
        for session_id in await self.store.list_active_ids(limit=500):
            session = await self.load_session(session_id)
            if session:
                session.status = SessionStatus.RECOVERING
                await self.touch(session)
                snapshots.append(session.to_redis())
        return snapshots
