import discord

from core.admin.service import AdminService
from core.help import HelpCodexService
from core.onboarding import OnboardingService
from core.world.living import LivingWorldService
from core.sessions.manager import DistributedSessionManager
from ui.embeds.about import AboutEmbedFactory
from ui.embeds.premium import HomePanelData, PlayerSnapshot, PremiumEmbedFactory, PremiumPalette, WorldSnapshot, starter_home
from ui.views.codex import HelpCodexView, OnboardingView
from ui.views.engagement import CosmeticsView, EngagementHubView, GlobalFeedView, ProfileShowcaseView, ShopView, SocialView, WorldBossView
from ui.views.game_launcher import GameBrowserView


def build_home_embed(owner_display: str | None = None, username: str = "New Adventurer") -> discord.Embed:
    data = starter_home(username)
    living = LivingWorldService().snapshot(seed=len(username))
    first_signal = living.signals[0]
    data = HomePanelData(
        player=data.player,
        world=WorldSnapshot(
            online_players=living.online_count,
            live_events=len(living.signals),
            world_boss=data.world.world_boss,
            boss_ends_in=data.world.boss_ends_in,
            active_clan_war=data.world.active_clan_war,
            season_name=data.world.season_name,
            highlight=first_signal.narration.replace("**", ""),
            region_status=f"{first_signal.region} • {first_signal.action_label}",
            friend_activity=living.friend_activity[:2],
            clan_status=data.world.clan_status,
            social_notifications=living.social_notifications[:2],
        ),
        featured_games=data.featured_games,
        recent_rewards=data.recent_rewards,
        next_actions=data.next_actions,
    )
    embed = PremiumEmbedFactory().home(data)
    if owner_display:
        embed.set_footer(text=f"Alpha Omega Arcade • Owner {owner_display} • !help for the Codex")
    return embed
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
        self.premium = PremiumEmbedFactory()

    async def _panel(self, interaction: discord.Interaction, embed: discord.Embed, view: discord.ui.View | None = None) -> None:
        await interaction.response.edit_message(embed=embed, view=view or self)

    @discord.ui.button(label="Start", emoji="✨", style=discord.ButtonStyle.success, custom_id="aoa:home:start", row=0)
    async def start(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        view = OnboardingView(OnboardingService())
        await self._panel(interaction, view.embed(), view)

    @discord.ui.button(label="Play", emoji="🎮", style=discord.ButtonStyle.primary, custom_id="aoa:home:games", row=0)
    async def games(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        view = GameBrowserView(self.session_manager)
        await self._panel(interaction, view.embed(), view)

    @discord.ui.button(label="Continue", emoji="🔄", style=discord.ButtonStyle.primary, custom_id="aoa:home:continue", row=0)
    async def recover(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if self.session_manager is None:
            await interaction.response.send_message("No session manager is available in this runtime.", ephemeral=True)
            return
        session = await self.session_manager.recover_or_reject(interaction.user.id)
        if session is None:
            await interaction.response.send_message("No active recoverable session found. Start a new adventure from Play.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=self.premium.recovery_prompt(session.session_id, session.game_id), view=self)

    @discord.ui.button(label="Profile", emoji="👤", style=discord.ButtonStyle.secondary, custom_id="aoa:home:profile", row=0)
    async def profile(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = self.premium.profile_card(PlayerSnapshot(username=interaction.user.display_name, level=7, xp=2420, next_level_xp=3000, coins=2450, gems=90, clan="Seeking Guild", badges=("🌌 Omega Initiate", "🗡️ First Clear", "🟣 Epic Showcase")))
        await self._panel(interaction, embed, ProfileShowcaseView())

    @discord.ui.button(label="Codex", emoji="📖", style=discord.ButtonStyle.secondary, custom_id="aoa:home:help", row=0)
    async def help(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        view = HelpCodexView(HelpCodexService())
        await self._panel(interaction, view.embed(), view)

    @discord.ui.button(label="Inventory", emoji="🎒", style=discord.ButtonStyle.secondary, custom_id="aoa:home:inventory", row=1)
    async def inventory(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._panel(interaction, self.premium.compact_codex_page("🎒 Vault + Cosmetics", ["Luxury inventory with rarity borders, showcase slots, filters, previews, badges, banners, and profile themes.", "Use `!inv` to return here instantly."], PremiumPalette.MYTHIC), CosmeticsView())

    @discord.ui.button(label="Quests", emoji="🎯", style=discord.ButtonStyle.secondary, custom_id="aoa:home:quests", row=1)
    async def quests(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._panel(interaction, self.premium.compact_codex_page("🎯 Quest + Battle Pass", ["Daily streaks, weekly goals, seasonal missions, premium reward pacing, and beginner guidance all live here.", "Next: clear your beginner dungeon, claim daily, open profile."], PremiumPalette.SUCCESS), EngagementHubView(self))

    @discord.ui.button(label="Social", emoji="🤝", style=discord.ButtonStyle.secondary, custom_id="aoa:home:social", row=1)
    async def social(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._panel(interaction, self.premium.compact_codex_page("🤝 Party + Friends", ["Create one persistent party, invite friends across servers, queue globally, challenge rivals, and spectate active runs."], PremiumPalette.OMEGA), SocialView())

    @discord.ui.button(label="Clans", emoji="🛡️", style=discord.ButtonStyle.secondary, custom_id="aoa:home:clans", row=1)
    async def clans(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._panel(interaction, self.premium.compact_codex_page("🛡️ Global Clan Citadel", ["Elite cross-server guild identity with banners, roles, banks, contributions, wars, prestige, applications, and roster pages.", "Clan creation unlocks at level 5."], PremiumPalette.SOLAR))

    @discord.ui.button(label="World", emoji="🌍", style=discord.ButtonStyle.secondary, custom_id="aoa:home:world", row=1)
    async def world(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._panel(interaction, self.premium.home(HomePanelData(player=PlayerSnapshot(username=interaction.user.display_name), world=WorldSnapshot())), WorldBossView())

    @discord.ui.button(label="Shop", emoji="🛒", style=discord.ButtonStyle.secondary, custom_id="aoa:home:shop", row=2)
    async def shop(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._panel(interaction, self.premium.compact_codex_page("🛒 Omega Atelier", ["Rotating cosmetics, previews, boosters, event caches, confirmation screens, and rate-limited purchases."], PremiumPalette.SOLAR), ShopView())

    @discord.ui.button(label="Feed", emoji="📡", style=discord.ButtonStyle.secondary, custom_id="aoa:home:feed", row=2)
    async def feed(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        living = LivingWorldService().snapshot(seed=interaction.user.id % 24)
        await self._panel(interaction, self.premium.living_world(living, LivingWorldService().dashboard_lines(living)), GlobalFeedView(self))

    @discord.ui.button(label="About", emoji="ℹ️", style=discord.ButtonStyle.secondary, custom_id="aoa:home:about", row=2)
    async def about(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._panel(interaction, AboutEmbedFactory().build())

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
