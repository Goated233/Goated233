from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class SettingsLike(Protocol):
    owner_user_id: int
    owner_display: str


class AdminPermissionName(StrEnum):
    ADMIN_VIEW = "admin.view"
    USER_INSPECT = "user.inspect"
    USER_PUNISH = "user.punish"
    USER_ECONOMY = "user.economy"
    USER_INVENTORY = "user.inventory"
    MODERATION_REVIEW = "moderation.review"
    ADMIN_GRANT = "admin.grant"
    GAME_CONTROL = "game.control"
    ECONOMY_CONTROL = "economy.control"
    ANALYTICS_VIEW = "analytics.view"
    GLOBAL_BROADCAST = "global.broadcast"
    MAINTENANCE = "global.maintenance"
    OWNER_OVERRIDE = "owner.override"


OWNER_PERMISSIONS = frozenset(permission.value for permission in AdminPermissionName)


@dataclass(frozen=True)
class PermissionContext:
    discord_id: int
    display_name: str
    permissions: frozenset[str]
    is_owner: bool

    def has(self, permission: AdminPermissionName | str) -> bool:
        return self.is_owner or str(permission) in self.permissions

    @property
    def badge(self) -> str:
        return "👑 Platform Owner" if self.is_owner else "🛡️ Admin"


class PermissionService:
    def __init__(self, settings: SettingsLike):
        self.settings = settings

    def is_owner(self, discord_id: int) -> bool:
        return discord_id == self.settings.owner_user_id

    async def build_context(self, discord_id: int, display_name: str, permissions: set[str] | None = None) -> PermissionContext:
        if self.is_owner(discord_id):
            return PermissionContext(
                discord_id=discord_id,
                display_name=self.settings.owner_display,
                permissions=frozenset(OWNER_PERMISSIONS),
                is_owner=True,
            )
        return PermissionContext(
            discord_id=discord_id,
            display_name=display_name,
            permissions=frozenset(permissions or set()),
            is_owner=False,
        )

    def assert_permission(self, context: PermissionContext, permission: AdminPermissionName) -> None:
        if not context.has(permission):
            raise PermissionError(f"Missing required permission: {permission.value}")
