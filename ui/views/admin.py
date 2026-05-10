import discord
from core.admin.permissions import PermissionContext
from core.admin.service import AdminService
from ui.embeds.admin import AdminEmbedFactory
from ui.modals.admin import AdminGrantModal, AdminReasonModal, UserSearchModal


class AdminDashboardView(discord.ui.View):
    embed_factory = AdminEmbedFactory()

    def __init__(self, admin_service: AdminService, context: PermissionContext):
        super().__init__(timeout=None)
        self.admin_service = admin_service
        self.context = context

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        candidate = await self.admin_service.context_for_user(
            interaction.user.id, interaction.user.display_name
        )
        if not candidate.has("admin.view"):
            await interaction.response.send_message("🔒 Admin console access denied.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Users", emoji="👥", style=discord.ButtonStyle.primary, custom_id="aoa:admin:users", row=0)
    async def users(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(UserSearchModal(self.admin_service, self.context))

    @discord.ui.button(label="Moderation", emoji="🛡️", style=discord.ButtonStyle.secondary, custom_id="aoa:admin:moderation", row=0)
    async def moderation(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(embed=self.embed_factory.moderation(), view=self)

    @discord.ui.button(label="Games", emoji="🎮", style=discord.ButtonStyle.secondary, custom_id="aoa:admin:games", row=0)
    async def games(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="🎮 Game Control",
            description="Terminate games, spawn bosses, trigger world events, tune loot/XP/drop rates, manage tournaments, seasons, and matchmaking queues.",
            color=0x7C3AED,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Economy", emoji="💰", style=discord.ButtonStyle.secondary, custom_id="aoa:admin:economy", row=0)
    async def economy(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(embed=self.embed_factory.economy(), view=self)

    @discord.ui.button(label="Analytics", emoji="📊", style=discord.ButtonStyle.secondary, custom_id="aoa:admin:analytics", row=0)
    async def analytics(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(embed=self.embed_factory.analytics(), view=self)

    @discord.ui.button(label="Broadcast", emoji="📣", style=discord.ButtonStyle.secondary, custom_id="aoa:admin:broadcast", row=1)
    async def broadcast(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(
            AdminReasonModal(self.admin_service, self.context, "global.broadcast")
        )

    @discord.ui.button(label="Maintenance", emoji="🚨", style=discord.ButtonStyle.danger, custom_id="aoa:admin:maintenance", row=1)
    async def maintenance(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(
            AdminReasonModal(self.admin_service, self.context, "global.maintenance")
        )

    @discord.ui.button(label="Anti-Cheat", emoji="🧿", style=discord.ButtonStyle.secondary, custom_id="aoa:admin:anticheat", row=1)
    async def anticheat(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="🧿 Anti-Cheat Dashboard",
            description="Review exploit flags, impossible stats, economy abuse, spam signals, alternate-account indicators, and reward farming evidence.",
            color=0xEF4444,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.success, custom_id="aoa:admin:refresh", row=1)
    async def refresh(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        stats = await self.admin_service.platform_stats()
        await interaction.response.edit_message(
            embed=self.embed_factory.dashboard(self.context, stats), view=self
        )


    @discord.ui.button(label="Grant Coins", emoji="🪙", style=discord.ButtonStyle.success, custom_id="aoa:admin:grant_coins", row=2)
    async def grant_coins(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(AdminGrantModal(self.admin_service, self.context, "coins"))

    @discord.ui.button(label="Grant XP", emoji="⭐", style=discord.ButtonStyle.success, custom_id="aoa:admin:grant_xp", row=2)
    async def grant_xp(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(AdminGrantModal(self.admin_service, self.context, "xp"))

    @discord.ui.button(label="Grant Item", emoji="🎁", style=discord.ButtonStyle.success, custom_id="aoa:admin:grant_item", row=2)
    async def grant_item(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(AdminGrantModal(self.admin_service, self.context, "item"))

    @discord.ui.button(label="Spawn Event", emoji="🌍", style=discord.ButtonStyle.primary, custom_id="aoa:admin:spawn_event", row=2)
    async def spawn_event(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(AdminReasonModal(self.admin_service, self.context, "event.spawn"))

    @discord.ui.button(label="Sessions", emoji="🕹️", style=discord.ButtonStyle.secondary, custom_id="aoa:admin:sessions", row=2)
    async def sessions(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        stats = await self.admin_service.platform_stats()
        embed = discord.Embed(
            title="🕹️ Active Session Viewer",
            description=f"Redis active sessions: **{stats.active_sessions}**\nActive DB game sessions: **{stats.active_games}**",
            color=0x0EA5E9,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Home", emoji="🏠", style=discord.ButtonStyle.secondary, custom_id="aoa:admin:home", row=3)
    async def home(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        from ui.views.home import ArcadeHomeView, build_home_embed

        await interaction.response.edit_message(
            embed=build_home_embed(self.admin_service.settings.owner_display),
            view=ArcadeHomeView(self.admin_service, self.admin_service.session_store and getattr(self.admin_service.client, "session_manager", None)),
        )
