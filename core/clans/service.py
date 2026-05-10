from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import floor
from uuid import uuid4

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from database.models.platform import Clan
else:
    AsyncSession = Any
    Clan = Any


class ClanRole(StrEnum):
    OWNER = "owner"
    OFFICER = "officer"
    MEMBER = "member"


class ClanPermission(StrEnum):
    MANAGE_PROFILE = "manage_profile"
    MANAGE_MEMBERS = "manage_members"
    MANAGE_BANK = "manage_bank"
    DECLARE_WAR = "declare_war"
    POST_ANNOUNCEMENT = "post_announcement"
    START_EVENTS = "start_events"


class ClanContributionType(StrEnum):
    XP = "xp"
    COINS = "coins"
    DUNGEON = "dungeon"
    PVP = "pvp"
    WORLD_BOSS = "world_boss"
    EVENT = "event"


class ClanWarStatus(StrEnum):
    DECLARED = "declared"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass(frozen=True)
class ClanCreateRequest:
    name: str
    tag: str
    owner_user_id: int
    description: str
    icon: str = "🛡️"
    banner: str = "astral_vanguard"
    theme: str = "omega_violet"


@dataclass(frozen=True)
class ClanProfile:
    clan_id: int | None
    name: str
    tag: str
    icon: str
    banner: str
    theme: str
    description: str
    announcement: str | None
    level: int
    xp: int
    prestige: int
    bank_coins: int
    badges: list[str]
    titles: list[str]
    member_count: int
    active_members: int
    global_rank: int | None = None
    season_rank: int | None = None


@dataclass(frozen=True)
class ClanMemberPage:
    members: list[dict]
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool


@dataclass(frozen=True)
class ClanInvite:
    id: str
    clan_id: int
    sender_user_id: int
    target_user_id: int
    expires_at: datetime
    message: str


@dataclass(frozen=True)
class ClanJoinRequest:
    id: str
    clan_id: int
    user_id: int
    server_id: int | None
    created_at: datetime
    note: str


@dataclass(frozen=True)
class ClanLeaderboardEntry:
    rank: int
    clan_id: int
    name: str
    tag: str
    score: int
    metric: str
    metadata: dict = field(default_factory=dict)


@dataclass
class ClanWar:
    id: str
    attacker_clan_id: int
    defender_clan_id: int
    season_id: str
    status: ClanWarStatus
    starts_at: datetime
    ends_at: datetime
    scores: dict[int, int] = field(default_factory=dict)
    contribution_breakdown: dict[int, dict[str, int]] = field(default_factory=dict)
    announcements: list[str] = field(default_factory=list)
    rewards_claimed: bool = False


class ClanService:
    """Global MMO guild operations backed by the existing Clan record.

    Discord guild/server IDs are deliberately metadata on requests or activity rows only; membership,
    identity, progression, bank state, and rankings are scoped to the Alpha Omega Arcade world.
    """

    ROLE_PERMISSIONS: dict[ClanRole, set[ClanPermission]] = {
        ClanRole.OWNER: set(ClanPermission),
        ClanRole.OFFICER: {
            ClanPermission.MANAGE_MEMBERS,
            ClanPermission.DECLARE_WAR,
            ClanPermission.POST_ANNOUNCEMENT,
            ClanPermission.START_EVENTS,
        },
        ClanRole.MEMBER: set(),
    }

    def __init__(self, session: AsyncSession, clan_model: type | None = None):
        self.session = session
        self.clan_model = clan_model

    async def create_clan(self, request: ClanCreateRequest) -> Clan:
        from sqlalchemy import select
        from database.models.platform import Clan

        existing = await self.session.execute(
            select(Clan).where((Clan.name == request.name) | (Clan.tag == request.tag.upper()))
        )
        if existing.scalar_one_or_none():
            raise ValueError("Clan name or tag is already taken")
        clan = Clan(
            name=request.name,
            tag=request.tag.upper()[:8],
            metadata_json=self.default_metadata(request),
        )
        self.session.add(clan)
        return clan

    def default_metadata(self, request: ClanCreateRequest) -> dict:
        now = datetime.now(UTC).isoformat()
        return {
            "global": True,
            "owner_user_id": request.owner_user_id,
            "description": request.description,
            "identity": {"icon": request.icon, "banner": request.banner, "theme": request.theme},
            "announcement": None,
            "members": [request.owner_user_id],
            "member_roles": {str(request.owner_user_id): ClanRole.OWNER.value},
            "member_servers": {str(request.owner_user_id): []},
            "member_contributions": {},
            "activity_feed": [{"type": "founded", "body": "A new banner rises in Alpha Omega Arcade.", "created_at": now}],
            "join_requests": [],
            "invites": [],
            "badges": [],
            "titles": ["Founding Guild"],
            "prestige": 0,
            "seasonal": {},
            "stats": {
                "total_wins": 0,
                "raid_clears": 0,
                "world_boss_damage": 0,
                "tournament_wins": 0,
                "war_score": 0,
            },
            "economy": {
                "contribution_currency": 0,
                "upgrades": {},
                "unlocks": [],
                "boosts": {},
                "shop_purchases": [],
                "exclusive_cosmetics": [],
            },
        }

    async def update_identity(
        self,
        clan_id: int,
        *,
        icon: str | None = None,
        banner: str | None = None,
        theme: str | None = None,
        description: str | None = None,
        announcement: str | None = None,
    ) -> Clan:
        clan = await self._get_clan(clan_id)
        data = self._metadata(clan)
        identity = data.setdefault("identity", {})
        if icon is not None:
            identity["icon"] = icon
        if banner is not None:
            identity["banner"] = banner
        if theme is not None:
            identity["theme"] = theme
        if description is not None:
            data["description"] = description
        if announcement is not None:
            data["announcement"] = announcement
            self._append_activity(data, "announcement", announcement)
        clan.metadata_json = data
        return clan

    async def request_join(self, clan_id: int, user_id: int, server_id: int | None, note: str = "") -> ClanJoinRequest:
        clan = await self._get_clan(clan_id)
        data = self._metadata(clan)
        request = ClanJoinRequest(uuid4().hex[:12], clan_id, user_id, server_id, datetime.now(UTC), note)
        data.setdefault("join_requests", []).append(
            {**request.__dict__, "created_at": request.created_at.isoformat()}
        )
        self._append_activity(data, "join_request", f"<@{user_id}> asked to join from a world gateway.")
        clan.metadata_json = data
        return request

    async def invite_member(self, clan_id: int, sender_user_id: int, target_user_id: int) -> ClanInvite:
        clan = await self._get_clan(clan_id)
        data = self._metadata(clan)
        invite = ClanInvite(
            uuid4().hex[:12],
            clan_id,
            sender_user_id,
            target_user_id,
            datetime.now(UTC) + timedelta(days=3),
            f"<@{sender_user_id}> invited <@{target_user_id}> to join [{clan.tag}] {clan.name}.",
        )
        data.setdefault("invites", []).append({**invite.__dict__, "expires_at": invite.expires_at.isoformat()})
        self._append_activity(data, "invite", invite.message)
        clan.metadata_json = data
        return invite

    async def add_member(self, clan_id: int, user_id: int, server_id: int | None = None, role: ClanRole = ClanRole.MEMBER) -> Clan:
        clan = await self._get_clan(clan_id)
        data = self._metadata(clan)
        members = data.setdefault("members", [])
        if user_id not in members:
            members.append(user_id)
        data.setdefault("member_roles", {})[str(user_id)] = role.value
        servers = data.setdefault("member_servers", {}).setdefault(str(user_id), [])
        if server_id is not None and server_id not in servers:
            servers.append(server_id)
        self._append_activity(data, "member_joined", f"<@{user_id}> joined the global clan roster.")
        clan.metadata_json = data
        return clan

    async def promote_member(self, clan_id: int, user_id: int, role: ClanRole) -> Clan:
        clan = await self._get_clan(clan_id)
        data = self._metadata(clan)
        if user_id not in data.get("members", []):
            raise ValueError("Clan member not found")
        data.setdefault("member_roles", {})[str(user_id)] = role.value
        self._append_activity(data, "role_changed", f"<@{user_id}> is now a clan {role.value}.")
        clan.metadata_json = data
        return clan

    async def contribute(
        self,
        clan_id: int,
        user_id: int,
        xp: int,
        coins: int,
        contribution_type: ClanContributionType = ClanContributionType.XP,
        season_id: str | None = None,
    ) -> None:
        clan = await self._get_clan(clan_id)
        data = self._metadata(clan)
        old_level = self.level_for_xp(clan.xp)
        clan.xp += max(0, xp)
        clan.bank_coins += max(0, coins)
        economy = data.setdefault("economy", {})
        economy["contribution_currency"] = economy.get("contribution_currency", 0) + max(0, xp // 10 + coins // 50)
        members = data.setdefault("member_contributions", {})
        member = members.setdefault(str(user_id), {"xp": 0, "coins": 0, "types": {}})
        member["xp"] = member.get("xp", 0) + max(0, xp)
        member["coins"] = member.get("coins", 0) + max(0, coins)
        member.setdefault("types", {})[contribution_type.value] = member.setdefault("types", {}).get(contribution_type.value, 0) + max(0, xp)
        if season_id:
            seasonal = data.setdefault("seasonal", {}).setdefault(season_id, {"xp": 0, "war_score": 0, "wins": 0})
            seasonal["xp"] += max(0, xp)
        new_level = self.level_for_xp(clan.xp)
        if new_level > old_level:
            self._append_activity(data, "level_up", f"{clan.name} reached Guild Level {new_level}.")
        clan.metadata_json = data

    def profile(self, clan: Clan, global_rank: int | None = None, season_rank: int | None = None) -> ClanProfile:
        data = self._metadata(clan)
        identity = data.get("identity", {})
        members = data.get("members", [])
        return ClanProfile(
            clan.id,
            clan.name,
            clan.tag,
            identity.get("icon", "🛡️"),
            identity.get("banner", "astral_vanguard"),
            identity.get("theme", "omega_violet"),
            data.get("description", ""),
            data.get("announcement"),
            self.level_for_xp(clan.xp),
            clan.xp,
            int(data.get("prestige", 0)),
            clan.bank_coins,
            list(data.get("badges", [])),
            list(data.get("titles", [])),
            len(members),
            len([member for member in members if self.member_total_contribution(data, member) > 0]),
            global_rank,
            season_rank,
        )

    def member_page(self, clan: Clan, page: int = 1, page_size: int = 10) -> ClanMemberPage:
        data = self._metadata(clan)
        members = list(data.get("members", []))
        total_pages = max(1, (len(members) + page_size - 1) // page_size)
        safe_page = min(max(1, page), total_pages)
        start = (safe_page - 1) * page_size
        rows = []
        for user_id in members[start : start + page_size]:
            contribution = data.get("member_contributions", {}).get(str(user_id), {})
            rows.append(
                {
                    "user_id": user_id,
                    "role": data.get("member_roles", {}).get(str(user_id), ClanRole.MEMBER.value),
                    "xp": contribution.get("xp", 0),
                    "coins": contribution.get("coins", 0),
                    "servers_seen": data.get("member_servers", {}).get(str(user_id), []),
                }
            )
        return ClanMemberPage(rows, safe_page, total_pages, safe_page < total_pages, safe_page > 1)

    def global_leaderboard(self, clans: list[Clan], metric: str = "xp", season_id: str | None = None, limit: int = 10) -> list[ClanLeaderboardEntry]:
        scored = [(clan, self._score(clan, metric, season_id)) for clan in clans]
        scored.sort(key=lambda row: row[1], reverse=True)
        return [
            ClanLeaderboardEntry(index + 1, clan.id, clan.name, clan.tag, score, metric, {"season_id": season_id} if season_id else {})
            for index, (clan, score) in enumerate(scored[:limit])
        ]

    def has_permission(self, clan: Clan, user_id: int, permission: ClanPermission) -> bool:
        role = ClanRole(self._metadata(clan).get("member_roles", {}).get(str(user_id), ClanRole.MEMBER.value))
        return permission in self.ROLE_PERMISSIONS[role]

    def purchase_upgrade(self, clan: Clan, upgrade_id: str, cost: int, boost: dict) -> None:
        if clan.bank_coins < cost:
            raise ValueError("Clan bank does not have enough coins")
        data = self._metadata(clan)
        clan.bank_coins -= cost
        economy = data.setdefault("economy", {})
        economy.setdefault("upgrades", {})[upgrade_id] = {"purchased_at": datetime.now(UTC).isoformat(), "boost": boost}
        economy.setdefault("boosts", {}).update(boost)
        self._append_activity(data, "upgrade", f"Clan upgrade `{upgrade_id}` is now active.")
        clan.metadata_json = data

    @staticmethod
    def level_for_xp(xp: int) -> int:
        return max(1, floor((max(0, xp) / 1000) ** 0.5) + 1)

    @staticmethod
    def member_total_contribution(data: dict, user_id: int) -> int:
        contribution = data.get("member_contributions", {}).get(str(user_id), {})
        return int(contribution.get("xp", 0)) + int(contribution.get("coins", 0))

    async def _get_clan(self, clan_id: int) -> Clan:
        clan = await self.session.get(self.clan_model, clan_id)
        if clan is None:
            raise ValueError("Clan not found")
        return clan

    def _score(self, clan: Clan, metric: str, season_id: str | None) -> int:
        data = self._metadata(clan)
        if season_id:
            return int(data.get("seasonal", {}).get(season_id, {}).get(metric, 0))
        if metric == "xp":
            return int(clan.xp)
        if metric == "bank_coins":
            return int(clan.bank_coins)
        if metric == "prestige":
            return int(data.get("prestige", 0))
        if metric == "active_members":
            return len([member for member in data.get("members", []) if self.member_total_contribution(data, member) > 0])
        return int(data.get("stats", {}).get(metric, 0))

    @staticmethod
    def _metadata(clan: Clan) -> dict:
        return dict(clan.metadata_json or {})

    @staticmethod
    def _append_activity(data: dict, event_type: str, body: str) -> None:
        feed = data.setdefault("activity_feed", [])
        feed.insert(0, {"type": event_type, "body": body, "created_at": datetime.now(UTC).isoformat()})
        del feed[50:]


class ClanWarService:
    SCORING_WEIGHTS: dict[ClanContributionType, int] = {
        ClanContributionType.DUNGEON: 8,
        ClanContributionType.PVP: 10,
        ClanContributionType.WORLD_BOSS: 6,
        ClanContributionType.EVENT: 5,
        ClanContributionType.XP: 1,
        ClanContributionType.COINS: 1,
    }

    def declare_war(self, attacker_clan_id: int, defender_clan_id: int, season_id: str, duration_hours: int = 48) -> ClanWar:
        if attacker_clan_id == defender_clan_id:
            raise ValueError("A clan cannot declare war on itself")
        now = datetime.now(UTC)
        war = ClanWar(
            id=uuid4().hex[:12],
            attacker_clan_id=attacker_clan_id,
            defender_clan_id=defender_clan_id,
            season_id=season_id,
            status=ClanWarStatus.ACTIVE,
            starts_at=now,
            ends_at=now + timedelta(hours=duration_hours),
            scores={attacker_clan_id: 0, defender_clan_id: 0},
        )
        war.announcements.append("War horns echo across the Omega network. A global clan war has begun.")
        return war

    def record_contribution(self, war: ClanWar, clan_id: int, user_id: int, contribution_type: ClanContributionType, amount: int) -> int:
        if clan_id not in {war.attacker_clan_id, war.defender_clan_id}:
            raise ValueError("Clan is not participating in this war")
        weighted_score = max(0, amount) * self.SCORING_WEIGHTS[contribution_type]
        war.scores[clan_id] = war.scores.get(clan_id, 0) + weighted_score
        clan_breakdown = war.contribution_breakdown.setdefault(clan_id, {})
        key = f"{contribution_type.value}:{user_id}"
        clan_breakdown[key] = clan_breakdown.get(key, 0) + weighted_score
        return weighted_score

    def scoreboard(self, war: ClanWar) -> list[tuple[int, int, int]]:
        ranked = sorted(war.scores.items(), key=lambda row: row[1], reverse=True)
        return [(index + 1, clan_id, score) for index, (clan_id, score) in enumerate(ranked)]

    def complete_war(self, war: ClanWar) -> dict:
        war.status = ClanWarStatus.COMPLETED
        winner = self.scoreboard(war)[0]
        rewards = {
            "winner_clan_id": winner[1],
            "prestige": 1,
            "bank_coins": 2500,
            "season_points": max(100, winner[2] // 10),
        }
        war.announcements.append(f"Clan {winner[1]} claims victory with {winner[2]:,} war score.")
        return rewards
