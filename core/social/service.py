from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4

from core.limits import LimitReason, LimitResult, LimitViolation, format_duration


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


class PartyStatus(StrEnum):
    ACTIVE = "active"
    DISBANDED = "disbanded"
    STALE = "stale"


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

    def expired(self, now: datetime | None = None) -> bool:
        return self.expires_at <= (now or datetime.now(UTC))


@dataclass
class Party:
    id: str
    leader_id: int
    members: list[int] = field(default_factory=list)
    game_id: str | None = None
    matchmaking_mode: str = "casual"
    home_guild_id: int | None = None
    cross_server: bool = True
    status: PartyStatus = PartyStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    disbanded_at: datetime | None = None


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
    active_party_by_user: dict[int, str] = field(default_factory=dict)
    parties: dict[str, Party] = field(default_factory=dict)
    invites: dict[str, SocialInvite] = field(default_factory=dict)
    invite_index: dict[tuple[InviteType, int, int, str | None], str] = field(default_factory=dict)
    party_disband_cooldowns: dict[int, datetime] = field(default_factory=dict)
    invite_cooldowns: dict[tuple[int, int, InviteType], datetime] = field(default_factory=dict)


class SocialService:
    PARTY_DISBAND_COOLDOWN_SECONDS = 180
    INVITE_COOLDOWN_SECONDS = 45
    INVITE_TTL_MINUTES = 15
    PARTY_AFK_TIMEOUT_MINUTES = 30
    DEFAULT_MAX_PARTY_SIZE = 5



class SocialService:
    def create_invite(
        self,
        invite_type: InviteType,
        sender_id: int,
        target_id: int,
        game_id: str | None = None,
        source_guild_id: int | None = None,
        target_guild_id: int | None = None,
        graph: SocialGraph | None = None,
    ) -> SocialInvite:
        if sender_id == target_id:
            raise LimitViolation(LimitResult.block(LimitReason.DUPLICATE, "You cannot send an invite to yourself."))
        now = datetime.now(UTC)
        if graph is not None:
            self.cleanup_stale_invites(graph, now)
            cooldown_key = (sender_id, target_id, invite_type)
            cooldown_until = graph.invite_cooldowns.get(cooldown_key)
            if cooldown_until and cooldown_until > now:
                raise LimitViolation(
                    LimitResult.block(
                        LimitReason.COOLDOWN,
                        f"Invite cooldown active. Try again in {format_duration(cooldown_until - now)}.",
                        retry_after_seconds=round((cooldown_until - now).total_seconds()),
                    )
                )
            duplicate_key = (invite_type, sender_id, target_id, game_id)
            existing_id = graph.invite_index.get(duplicate_key)
            existing = graph.invites.get(existing_id or "")
            if existing and not existing.expired(now):
                raise LimitViolation(
                    LimitResult.block(
                        LimitReason.DUPLICATE,
                        "You already have an active invite pending for this player.",
                        active_reference=existing.id,
                        recovery_action="Wait for them to accept/decline or let it expire.",
                    )
                )
        action = invite_type.value.replace("_", " ")
        gateway = " across the Omega network" if source_guild_id != target_guild_id else ""
        invite = SocialInvite(
    ) -> SocialInvite:
        action = invite_type.value.replace("_", " ")
        gateway = " across the Omega network" if source_guild_id != target_guild_id else ""
        return SocialInvite(
            uuid4().hex[:12],
            invite_type,
            sender_id,
            target_id,
            game_id,
            now + timedelta(minutes=self.INVITE_TTL_MINUTES),
            datetime.now(UTC) + timedelta(minutes=15),
            f"<@{sender_id}> sent you a {action} invite{gateway}",
            source_guild_id,
            target_guild_id,
        )
        if graph is not None:
            graph.invites[invite.id] = invite
            graph.invite_index[(invite_type, sender_id, target_id, game_id)] = invite.id
            graph.invite_cooldowns[(sender_id, target_id, invite_type)] = now + timedelta(seconds=self.INVITE_COOLDOWN_SECONDS)
        return invite

    def validate_invite(self, graph: SocialGraph, invite_id: str, target_id: int) -> SocialInvite:
        invite = graph.invites.get(invite_id)
        if invite is None:
            raise LimitViolation(LimitResult.block(LimitReason.STALE, "That invite no longer exists."))
        if invite.target_id != target_id:
            raise LimitViolation(LimitResult.block(LimitReason.OWNERSHIP, "That invite belongs to another player."))
        if invite.expired():
            self._remove_invite(graph, invite)
            raise LimitViolation(LimitResult.block(LimitReason.EXPIRED, "Your party invite expired."))
        return invite

    def create_party(
        self,
        leader_id: int,
        game_id: str | None = None,
        home_guild_id: int | None = None,
        matchmaking_mode: str = "casual",
        graph: SocialGraph | None = None,
    ) -> Party:
        now = datetime.now(UTC)
        if graph is not None:
            self.cleanup_inactive_parties(graph, now=now)
            active_id = graph.active_party_by_user.get(leader_id)
            if active_id:
                raise LimitViolation(
                    LimitResult.block(
                        LimitReason.DUPLICATE,
                        "You are already in a party.",
                        active_reference=active_id,
                        recovery_action="Use the existing party controls or disband it first.",
                    )
                )
            cooldown_until = graph.party_disband_cooldowns.get(leader_id)
            if cooldown_until and cooldown_until > now:
                raise LimitViolation(
                    LimitResult.block(
                        LimitReason.COOLDOWN,
                        f"Party creation is cooling down after disband. Try again in {format_duration(cooldown_until - now)}.",
                        retry_after_seconds=round((cooldown_until - now).total_seconds()),
                    )
                )
        party = Party(
    ) -> Party:
        return Party(
            id=uuid4().hex[:10],
            leader_id=leader_id,
            members=[leader_id],
            game_id=game_id,
            home_guild_id=home_guild_id,
            matchmaking_mode=matchmaking_mode,
        )
        if graph is not None:
            graph.parties[party.id] = party
            graph.active_party_by_user[leader_id] = party.id
        return party

    def join_party(self, party: Party, user_id: int, max_size: int = DEFAULT_MAX_PARTY_SIZE, source_guild_id: int | None = None, graph: SocialGraph | None = None) -> Party:
        now = datetime.now(UTC)
        if party.status != PartyStatus.ACTIVE:
            raise LimitViolation(LimitResult.block(LimitReason.STALE, "That party is no longer active."))
        if graph is not None:
            active_id = graph.active_party_by_user.get(user_id)
            if active_id and active_id != party.id:
                raise LimitViolation(LimitResult.block(LimitReason.DUPLICATE, "You are already in a party.", active_reference=active_id))
        if user_id in party.members:
            party.updated_at = now
            return party
        if len(party.members) >= max_size:
            raise LimitViolation(LimitResult.block(LimitReason.CAPACITY, f"This party is full ({max_size}/{max_size})."))
        party.members.append(user_id)
        party.updated_at = now
        if source_guild_id is not None and party.home_guild_id is not None and source_guild_id != party.home_guild_id:
            party.cross_server = True
        if graph is not None:
            graph.active_party_by_user[user_id] = party.id
            graph.parties[party.id] = party
        return party

    def leave_party(self, graph: SocialGraph, party_id: str, user_id: int) -> Party | None:
        party = graph.parties.get(party_id)
        if party is None or party.status != PartyStatus.ACTIVE:
            raise LimitViolation(LimitResult.block(LimitReason.STALE, "That party is no longer active."))
        if user_id not in party.members:
            raise LimitViolation(LimitResult.block(LimitReason.OWNERSHIP, "You are not in that party."))
        party.members.remove(user_id)
        graph.active_party_by_user.pop(user_id, None)
        if not party.members:
            return self.disband_party(graph, party_id, user_id, apply_cooldown=False)
        if party.leader_id == user_id:
            party.leader_id = party.members[0]
        party.updated_at = datetime.now(UTC)
        return party

    def transfer_ownership(self, graph: SocialGraph, party_id: str, current_leader_id: int, new_leader_id: int) -> Party:
        party = graph.parties.get(party_id)
        if party is None or party.status != PartyStatus.ACTIVE:
            raise LimitViolation(LimitResult.block(LimitReason.STALE, "That party is no longer active."))
        if party.leader_id != current_leader_id:
            raise LimitViolation(LimitResult.block(LimitReason.OWNERSHIP, "Only the party leader can transfer ownership."))
        if new_leader_id not in party.members:
            raise LimitViolation(LimitResult.block(LimitReason.OWNERSHIP, "The new leader must already be in the party."))
        party.leader_id = new_leader_id
        party.updated_at = datetime.now(UTC)
        return party

    def disband_party(self, graph: SocialGraph, party_id: str, actor_id: int, apply_cooldown: bool = True) -> None:
        party = graph.parties.get(party_id)
        if party is None:
            raise LimitViolation(LimitResult.block(LimitReason.STALE, "That party is already gone."))
        if party.leader_id != actor_id and party.members:
            raise LimitViolation(LimitResult.block(LimitReason.OWNERSHIP, "Only the party leader can disband the party."))
        now = datetime.now(UTC)
        for member_id in list(party.members):
            graph.active_party_by_user.pop(member_id, None)
        party.members.clear()
        party.status = PartyStatus.DISBANDED
        party.disbanded_at = now
        party.updated_at = now
        if apply_cooldown:
            graph.party_disband_cooldowns[actor_id] = now + timedelta(seconds=self.PARTY_DISBAND_COOLDOWN_SECONDS)

    def cleanup_inactive_parties(self, graph: SocialGraph, now: datetime | None = None) -> int:
        moment = now or datetime.now(UTC)
        removed = 0
        for party in list(graph.parties.values()):
            if party.status == PartyStatus.ACTIVE and moment - party.updated_at > timedelta(minutes=self.PARTY_AFK_TIMEOUT_MINUTES):
                for member_id in party.members:
                    graph.active_party_by_user.pop(member_id, None)
                party.status = PartyStatus.STALE
                removed += 1
        return removed

    def cleanup_stale_invites(self, graph: SocialGraph, now: datetime | None = None) -> int:
        moment = now or datetime.now(UTC)
        removed = 0
        for invite in list(graph.invites.values()):
            if invite.expired(moment):
                self._remove_invite(graph, invite)
                removed += 1
        return removed

    def recover_party(self, graph: SocialGraph, user_id: int) -> Party | None:
        party_id = graph.active_party_by_user.get(user_id)
        party = graph.parties.get(party_id or "")
        if party and party.status == PartyStatus.ACTIVE:
            party.updated_at = datetime.now(UTC)
            return party
        if party_id:
            graph.active_party_by_user.pop(user_id, None)
        return None

    def challenge_request(self, sender_id: int, target_id: int, game_id: str, wager_coins: int = 0, graph: SocialGraph | None = None) -> SocialInvite:
        invite = self.create_invite(InviteType.CHALLENGE, sender_id, target_id, game_id, graph=graph)

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

    def _remove_invite(self, graph: SocialGraph, invite: SocialInvite) -> None:
        graph.invites.pop(invite.id, None)
        graph.invite_index.pop((invite.invite_type, invite.sender_id, invite.target_id, invite.game_id), None)
