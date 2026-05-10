import discord
from core.admin.service import AdminService
from core.sessions.manager import DistributedSessionManager
from ui.embeds.about import AboutEmbedFactory
from ui.embeds.theme import COLORS
from ui.views.game_launcher import GameLauncherView
from ui.views.engagement import (
    CosmeticsView,
    EngagementHubView,
    GlobalFeedView,
    ProfileShowcaseView,
    ShopView,
    SocialView,
    WorldBossView,
)


class ArcadeHomeView(discord.ui.View):
    def __init__(self, admin_service: AdminService | None, session_manager: DistributedSessionManager | None = None):
        super().__init__(timeout=None)
        self.admin_service = admin_service
        self.session_manager = session_manager

    async def _panel(self, interaction: discord.Interaction, title: str, description: str, color: int) -> None:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Premium button-first panel • more controls unlock as you progress")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Games", emoji="🎮", style=discord.ButtonStyle.primary, custom_id="aoa:home:games", row=0)
    async def games(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="🎮 Game Launcher",
            description="Choose a playable game below. Dungeon Raid is fully button-playable; more games are registered through reusable engines.",
            color=COLORS["primary"],
        )
        await interaction.response.edit_message(embed=embed, view=GameLauncherView(self.session_manager))

    @discord.ui.button(label="Profile", emoji="👤", style=discord.ButtonStyle.secondary, custom_id="aoa:home:profile", row=0)
    async def profile(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="👤 Premium Profile",
            description="Showcase themes, badges, equipped cosmetics, clan status, achievements, favorite games, and prestige.",
            color=COLORS["info"],
        )
        await interaction.response.edit_message(embed=embed, view=ProfileShowcaseView())

    @discord.ui.button(label="Leaderboards", emoji="🏆", style=discord.ButtonStyle.secondary, custom_id="aoa:home:leaderboards", row=0)
    async def leaderboards(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._panel(interaction, "🏆 Competitive Boards", "Live rankings, dethrone moments, seasonal races, clan ladders, and reward snapshots are shown in compact mobile-first pages.", COLORS["warning"])

    @discord.ui.button(label="Inventory", emoji="🎒", style=discord.ButtonStyle.secondary, custom_id="aoa:home:inventory", row=0)
    async def inventory(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="🎒 Inventory + Cosmetics",
            description="Loot, equipment, filters, tooltips, cosmetics, rarity borders, badges, and banners share the same premium collection loop.",
            color=COLORS["primary"],
        )
        await interaction.response.edit_message(embed=embed, view=CosmeticsView())

    @discord.ui.button(label="Clans", emoji="🛡️", style=discord.ButtonStyle.secondary, custom_id="aoa:home:clans", row=0)
    async def clans(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._panel(interaction, "🛡️ Clan HQ", "Clan XP, banks, war weeks, shared raid progress, social identity, contribution races, and future clan chat live here.", COLORS["success"])

    @discord.ui.button(label="Shop", emoji="🛒", style=discord.ButtonStyle.secondary, custom_id="aoa:home:shop", row=1)
    async def shop(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(title="🛒 Premium Shop", description="Rotating offers, cosmetics, boosters, event caches, previews, and confirmation screens.", color=COLORS["legendary"])
        await interaction.response.edit_message(embed=embed, view=ShopView())

    @discord.ui.button(label="Quests", emoji="🎯", style=discord.ButtonStyle.secondary, custom_id="aoa:home:quests", row=1)
    async def quests(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(title="🎯 Daily Retention Hub", description="Claim streak rewards, view rotating quests, and progress your season pass.", color=COLORS["success"])
        await interaction.response.edit_message(embed=embed, view=EngagementHubView(self))

    @discord.ui.button(label="Ranked", emoji="⚔️", style=discord.ButtonStyle.secondary, custom_id="aoa:home:ranked", row=1)
    async def ranked(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(title="⚔️ Social Ranked", description="Create parties, send challenges, spectate sessions, and queue with friends.", color=COLORS["danger"])
        await interaction.response.edit_message(embed=embed, view=SocialView())

    @discord.ui.button(label="Events", emoji="🌍", style=discord.ButtonStyle.secondary, custom_id="aoa:home:events", row=1)
    async def events(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(title="🌍 Living World", description="Global feed, world bosses, tournaments, rare drops, and viral announcement moments.", color=COLORS["info"])
        await interaction.response.edit_message(embed=embed, view=WorldBossView())

    @discord.ui.button(label="Settings", emoji="⚙️", style=discord.ButtonStyle.secondary, custom_id="aoa:home:settings", row=1)
    async def settings(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(title="🌐 Global Feed + Settings", description="Compact mobile layouts, notifications, privacy, and live arcade feed controls.", color=COLORS["primary"])
        await interaction.response.edit_message(embed=embed, view=GlobalFeedView())

    @discord.ui.button(label="About", emoji="ℹ️", style=discord.ButtonStyle.secondary, custom_id="aoa:home:about", row=2)
    async def about(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if self.admin_service is None:
            await self._panel(interaction, "ℹ️ About", "Alpha Omega Arcade is starting up. Admin services are not attached yet.", COLORS["info"])
            return
        stats = await self.admin_service.platform_stats()
        embed = AboutEmbedFactory(self.admin_service.settings.owner_display).build(stats)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Admin", emoji="👑", style=discord.ButtonStyle.danger, custom_id="aoa:home:admin", row=2)
    async def admin(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        from ui.views.admin import AdminDashboardView

        if self.admin_service is None:
            await interaction.response.send_message("Admin services are still starting up.", ephemeral=True)
            return
        context = await self.admin_service.context_for_user(
            interaction.user.id, interaction.user.display_name
        )
        try:
            await self.admin_service.assert_admin_access(context)
        except PermissionError:
            await interaction.response.send_message("🔒 This panel is restricted to Alpha Omega Arcade admins.", ephemeral=True)
            return
        stats = await self.admin_service.platform_stats()
        await interaction.response.edit_message(
            embed=AdminDashboardView.embed_factory.dashboard(context, stats),
            view=AdminDashboardView(self.admin_service, context),
        )


def build_home_embed(owner_display: str) -> discord.Embed:
    embed = discord.Embed(
        title="🌌 Alpha Omega Arcade",
        description=(
            "A premium button-first gaming console inside Discord. Navigate with buttons, "
            "persistent views, select menus, modals, and polished embeds.\n\n"
            f"👑 Owner: {owner_display}"
        ),
        color=COLORS["primary"],
    )
    embed.add_field(name="🎮 Play", value="Games • Ranked • Events • Quests", inline=True)
    embed.add_field(name="📈 Progress", value="Profiles • Inventory • Cosmetics • Achievements", inline=True)
    embed.add_field(name="🌍 Compete", value="Leaderboards • Clans • Tournaments • Seasons", inline=True)
    return embed
