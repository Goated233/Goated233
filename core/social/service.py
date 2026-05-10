from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4


class InviteType(StrEnum):
    FRIEND = "friend"
    PARTY = "party"
    CHALLENGE = "challenge"
    GAME = "game"
    SPECTATE = "spectate"


class PresenceStatus(StrEnum):
    ONLINE = "online"
    IDLE = "idle"
    OFFLINE = "offline"
    IN_GAME = "in_game"


@dataclass(frozen=True)
class SocialInvite:
    id: str
    invite_type: InviteType
    sender_id: int
    target_id: int
    game_id: str | None
    expires_at: datetime
    message: str
    source_guild_id: int | None = None
    target_guild_id: int | None = None


@dataclass
class Party:
    id: str
    leader_id: int
    members: list[int] = field(default_factory=list)
    game_id: str | None = None
    matchmaking_mode: str = "casual"
    home_guild_id: int | None = None
    cross_server: bool = True


@dataclass(frozen=True)
class FriendProfile:
    user_id: int
    status: PresenceStatus
    current_game: str | None
    current_party_id: str | None
    mutual_clan_id: int | None
    last_seen_at: datetime


@dataclass
class SocialGraph:
    friends: dict[int, set[int]] = field(default_factory=dict)
    recent_players: dict[int, list[int]] = field(default_factory=dict)
    presence: dict[int, FriendProfile] = field(default_factory=dict)
    mutual_clans: dict[tuple[int, int], int] = field(default_factory=dict)


class SocialService:
    def create_invite(
        self,
        invite_type: InviteType,
        sender_id: int,
        target_id: int,
        game_id: str | None = None,
        source_guild_id: int | None = None,
        target_guild_id: int | None = None,
    ) -> SocialInvite:
        action = invite_type.value.replace("_", " ")
        gateway = " across the Omega network" if source_guild_id != target_guild_id else ""
        return SocialInvite(
            uuid4().hex[:12],
            invite_type,
            sender_id,
            target_id,
            game_id,
            datetime.now(UTC) + timedelta(minutes=15),
            f"<@{sender_id}> sent you a {action} invite{gateway}",
            source_guild_id,
            target_guild_id,
        )

    def create_party(
        self,
        leader_id: int,
        game_id: str | None = None,
        home_guild_id: int | None = None,
        matchmaking_mode: str = "casual",
    ) -> Party:
        return Party(
            id=uuid4().hex[:10],
            leader_id=leader_id,
            members=[leader_id],
            game_id=game_id,
            home_guild_id=home_guild_id,
            matchmaking_mode=matchmaking_mode,
        )

    def join_party(self, party: Party, user_id: int, max_size: int = 5, source_guild_id: int | None = None) -> Party:
        if user_id not in party.members and len(party.members) < max_size:
            party.members.append(user_id)
        if source_guild_id is not None and party.home_guild_id is not None and source_guild_id != party.home_guild_id:
            party.cross_server = True
        return party

    def challenge_request(self, sender_id: int, target_id: int, game_id: str, wager_coins: int = 0) -> SocialInvite:
        invite = self.create_invite(InviteType.CHALLENGE, sender_id, target_id, game_id)
        return SocialInvite(
            invite.id,
            invite.invite_type,
            invite.sender_id,
            invite.target_id,
            invite.game_id,
            invite.expires_at,
            f"{invite.message} for **{game_id}**" + (f" with `{wager_coins}` coins at stake." if wager_coins else "."),
            invite.source_guild_id,
            invite.target_guild_id,
        )

    def spectate_payload(self, session_id: str, spectator_id: int, source_guild_id: int | None = None) -> dict:
        return {
            "session_id": session_id,
            "spectator_id": spectator_id,
            "source_guild_id": source_guild_id,
            "mode": "spectate",
            "joined_at": datetime.now(UTC).isoformat(),
            "global": True,
        }

    def add_friend(self, graph: SocialGraph, user_id: int, friend_id: int) -> None:
        graph.friends.setdefault(user_id, set()).add(friend_id)
        graph.friends.setdefault(friend_id, set()).add(user_id)

    def friends_list(self, graph: SocialGraph, user_id: int) -> list[FriendProfile]:
        friend_ids = sorted(graph.friends.get(user_id, set()))
        return [
            graph.presence.get(
                friend_id,
                FriendProfile(friend_id, PresenceStatus.OFFLINE, None, None, graph.mutual_clans.get(tuple(sorted((user_id, friend_id)))), datetime.now(UTC)),
            )
            for friend_id in friend_ids
        ]

    def set_presence(
        self,
        graph: SocialGraph,
        user_id: int,
        status: PresenceStatus,
        current_game: str | None = None,
        current_party_id: str | None = None,
        mutual_clan_id: int | None = None,
    ) -> FriendProfile:
        profile = FriendProfile(user_id, status, current_game, current_party_id, mutual_clan_id, datetime.now(UTC))
        graph.presence[user_id] = profile
        return profile

    def track_recent_players(self, graph: SocialGraph, user_id: int, encountered_ids: list[int], limit: int = 25) -> None:
        recent = graph.recent_players.setdefault(user_id, [])
        for encountered_id in encountered_ids:
            if encountered_id == user_id:
                continue
            if encountered_id in recent:
                recent.remove(encountered_id)
            recent.insert(0, encountered_id)
        del recent[limit:]

    def mutual_clan(self, graph: SocialGraph, user_a: int, user_b: int, clan_id: int | None) -> None:
        key = tuple(sorted((user_a, user_b)))
        if clan_id is None:
            graph.mutual_clans.pop(key, None)
        else:
            graph.mutual_clans[key] = clan_id
