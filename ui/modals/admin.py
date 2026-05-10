import discord
from core.admin.audit import AuditRequest
from core.admin.permissions import AdminPermissionName, PermissionContext
from core.admin.service import AdminService


class AdminReasonModal(discord.ui.Modal):
    def __init__(
        self,
        admin_service: AdminService,
        context: PermissionContext,
        action_type: str,
        target_discord_id: int | None = None,
    ):
        super().__init__(title="Admin action reason")
        self.admin_service = admin_service
        self.context = context
        self.action_type = action_type
        self.target_discord_id = target_discord_id
        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Explain why this action is being performed.",
            min_length=5,
            max_length=500,
            style=discord.TextStyle.paragraph,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        allowed, retry_after, bypassed = await self.admin_service.dangerous_action_allowed(
            self.context.discord_id, self.action_type
        )
        if not allowed:
            await interaction.response.send_message(
                f"⏳ Dangerous action cooldown active. Retry in {retry_after}s.", ephemeral=True
            )
            return
        await self.admin_service.audit(
            AuditRequest(
                actor_discord_id=self.context.discord_id,
                target_discord_id=self.target_discord_id,
                action_type=self.action_type,
                reason=str(self.reason.value),
                metadata={"confirmed_by_modal": True, "owner_bypass": bypassed},
                rollback_metadata={"supported": True},
                category="admin",
            )
        )
        await interaction.response.send_message(
            f"✅ `{self.action_type}` queued and audit logged.", ephemeral=True
        )


class UserSearchModal(discord.ui.Modal):
    def __init__(self, admin_service: AdminService, context: PermissionContext):
        super().__init__(title="Inspect player")
        self.admin_service = admin_service
        self.context = context
        self.discord_id = discord.ui.TextInput(
            label="Discord User ID",
            placeholder="123456789012345678",
            min_length=10,
            max_length=24,
        )
        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Why are you inspecting this user?",
            min_length=5,
            max_length=500,
        )
        self.add_item(self.discord_id)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.admin_service.permissions.assert_permission(self.context, AdminPermissionName.USER_INSPECT)
        target_id = int(str(self.discord_id.value).strip())
        await self.admin_service.audit(
            AuditRequest(
                actor_discord_id=self.context.discord_id,
                target_discord_id=target_id,
                action_type="user.inspect",
                reason=str(self.reason.value),
                metadata={"source": "admin_user_search_modal"},
                category="user_management",
            )
        )
        embed = discord.Embed(
            title="👥 User Inspection",
            description=f"Inspection audit created for `<@{target_id}>` (`{target_id}`).",
            color=0x0EA5E9,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class AdminGrantModal(discord.ui.Modal):
    def __init__(self, admin_service: AdminService, context: PermissionContext, grant_type: str):
        super().__init__(title=f"Grant {grant_type.title()}")
        self.admin_service = admin_service
        self.context = context
        self.grant_type = grant_type
        self.target = discord.ui.TextInput(label="Target Discord User ID", min_length=10, max_length=24)
        self.amount_or_item = discord.ui.TextInput(
            label="Amount or Item ID",
            placeholder="1000 or crystal_blade",
            min_length=1,
            max_length=96,
        )
        self.reason = discord.ui.TextInput(label="Reason", min_length=5, max_length=500)
        self.add_item(self.target)
        self.add_item(self.amount_or_item)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        target_id = int(str(self.target.value).strip())
        await self.admin_service.audit(
            AuditRequest(
                actor_discord_id=self.context.discord_id,
                target_discord_id=target_id,
                action_type=f"grant.{self.grant_type}",
                reason=str(self.reason.value),
                metadata={"value": str(self.amount_or_item.value), "source": "admin_grant_modal"},
                rollback_metadata={"reversible": True, "grant_type": self.grant_type},
                category="economy" if self.grant_type in {"coins", "xp"} else "inventory",
            )
        )
        await interaction.response.send_message(
            f"✅ Grant `{self.grant_type}` for `<@{target_id}>` was audit logged. Reward pipeline can now apply it safely.",
            ephemeral=True,
        )
