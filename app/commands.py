import discord
from discord import app_commands
from discord.ext import commands

from app.startup import StartupValidator
from core.help import HelpCodexService
from core.onboarding import OnboardingService
from core.retention.dopamine import DopamineService
from core.social.viral import SocialViralService
from core.world.living import LivingWorldService
from ui.embeds.health import HealthEmbedFactory
from ui.embeds.premium import PlayerSnapshot, PremiumEmbedFactory, PremiumPalette
from ui.views.codex import HelpCodexView, OnboardingView
from ui.views.game_launcher import GameBrowserView
from ui.views.home import ArcadeHomeView, build_home_embed


class OwnerSetupCog(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="arcade", description="Alpha Omega Arcade owner setup and health tools")
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.bot.settings.owner_user_id:
            await interaction.response.send_message("🔒 Owner-only setup command.", ephemeral=True)
            return False
        return True

    @app_commands.command(name="setup-panel", description="Post the persistent Alpha Omega Arcade home panel here.")
    async def setup_panel(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("🚀 Deploying Alpha Omega Arcade panel...", ephemeral=True)
        if interaction.channel is None:
            return
        await interaction.channel.send(embed=build_home_embed(self.bot.settings.owner_display), view=ArcadeHomeView(self.bot.admin_service, self.bot.session_manager))

    @app_commands.command(name="health", description="Run startup health checks for the arcade platform.")
    async def health(self, interaction: discord.Interaction) -> None:
        validator = StartupValidator(self.bot.settings, self.bot.db_engine, self.bot.redis)
        checks = await validator.validate_all()
        await interaction.response.send_message(embed=HealthEmbedFactory().build(checks), ephemeral=True)


class PlayerCommandCog(commands.Cog):
    """Polished hybrid commands that redirect players into persistent MMO UI flows."""

    def __init__(self, bot):
        self.bot = bot
        self.premium = PremiumEmbedFactory()
        self.help_service = HelpCodexService()
        self.onboarding = OnboardingService()
        self.living_world = LivingWorldService()
        self.dopamine = DopamineService()
        self.viral = SocialViralService()

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        # Profile auto-creation is handled by persistence services when DB-backed commands mutate state.
        # Read-only launcher commands remain instant and never block on DB availability.
        return None

    async def _send_home(self, ctx: commands.Context) -> None:
        await ctx.send(embed=build_home_embed(getattr(self.bot.settings, "owner_display", None), ctx.author.display_name), view=ArcadeHomeView(self.bot.admin_service, self.bot.session_manager))

    @commands.hybrid_command(name="start", aliases=["begin"], description="Open the cinematic first-login adventure flow.")
    async def start(self, ctx: commands.Context) -> None:
        view = OnboardingView(self.onboarding)
        await ctx.send(embed=view.embed(), view=view)

    @commands.hybrid_command(name="play", aliases=["p"], description="Open the MMO home launcher.")
    async def play(self, ctx: commands.Context) -> None:
        await self._send_home(ctx)

    @commands.hybrid_command(name="games", aliases=["g"], description="Browse every game in the Omega launcher.")
    async def games(self, ctx: commands.Context) -> None:
        view = GameBrowserView(self.bot.session_manager)
        await ctx.send(embed=view.embed(), view=view)

    @commands.hybrid_command(name="profile", aliases=["me"], description="Open your premium player card.")
    async def profile(self, ctx: commands.Context) -> None:
        embed = self.premium.profile_card(PlayerSnapshot(username=ctx.author.display_name, level=7, xp=2420, next_level_xp=3000, coins=2450, gems=90, clan="Seeking Guild", badges=("🌌 Omega Initiate", "🗡️ First Clear", "🟣 Epic Showcase")))
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="inventory", aliases=["inv"], description="Open your vault and cosmetic showcase.")
    async def inventory(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.premium.compact_codex_page("🎒 Vault + Cosmetics", ["Rarity borders, showcase slots, profile themes, badges, banners, and loot filters live here.", "Use the Home Hub buttons for catalog previews."], PremiumPalette.MYTHIC))

    @commands.hybrid_command(name="daily", description="Open daily streak rewards.")
    async def daily(self, ctx: commands.Context) -> None:
        reveal = self.dopamine.streak_reveal(7, 260, 220, 10)
        await ctx.send(embed=self.premium.reward_reveal(reveal))

    @commands.hybrid_command(name="quests", description="Open quests and recommendations.")
    async def quests(self, ctx: commands.Context) -> None:
        lines = self.help_service.recommendations(level=1, has_clan=False, active_session=False)
        await ctx.send(embed=self.premium.compact_codex_page("🎯 What Should I Do Next?", lines, PremiumPalette.SUCCESS))

    @commands.hybrid_command(name="battlepass", aliases=["bp"], description="Open the seasonal battle pass overview.")
    async def battlepass(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.premium.compact_codex_page("🎟️ Season Zero Battle Pass", ["Tier 12/50", "Next: Solar Border Shard • 250 gems • Omega Cache", "Earn season XP from every major activity."], PremiumPalette.SOLAR))

    @commands.hybrid_command(name="raid", description="Jump to Dungeon Raid.")
    async def raid(self, ctx: commands.Context) -> None:
        view = GameBrowserView(self.bot.session_manager)
        await ctx.send(embed=self.premium.compact_codex_page("🗡️ Dungeon Raid", ["Open the Game Browser and press Dungeon Raid to start a recoverable session.", "Combat uses cinematic logs, locks, and protected rewards."], PremiumPalette.DANGER), view=view)

    @commands.hybrid_command(name="boss", description="Open world boss status.")
    async def boss(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.premium.world_announcement("Void Titan Warning", "A world boss signal is active. Contribute verified damage, climb clan rankings, and claim rewards once."))

    @commands.hybrid_command(name="events", description="Open live world events.")
    async def events(self, ctx: commands.Context) -> None:
        snapshot = self.living_world.snapshot(seed=ctx.author.id % 24)
        await ctx.send(embed=self.premium.living_world(snapshot, self.living_world.dashboard_lines(snapshot)))

    @commands.hybrid_command(name="party", description="Open party and social matchmaking guidance.")
    async def party(self, ctx: commands.Context) -> None:
        card = self.viral.rivalry_card(ctx.author.display_name, "Nearest Rival", 42)
        await ctx.send(embed=self.premium.social_share_card(card))

    @commands.hybrid_command(name="clan", description="Open global clan guidance.")
    async def clan(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.help_embed("clans"))

    @commands.hybrid_command(name="leaderboard", aliases=["lb"], description="Open rankings overview.")
    async def leaderboard(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.premium.compact_codex_page("🏆 Omega Leaderboards", ["Global XP", "Seasonal clans", "World boss damage", "War score", "Tournament champions"], PremiumPalette.SOLAR))

    @commands.hybrid_command(name="rank", description="Open ranked overview.")
    async def rank(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.premium.compact_codex_page("⚔️ Ranked Signal", ["Queue cooldowns and AFK penalties keep ranked fair.", "Party up, challenge rivals, and climb seasonal ladders."], PremiumPalette.DANGER))

    @commands.hybrid_command(name="stats", description="Open stat card.")
    async def stats(self, ctx: commands.Context) -> None:
        await self.profile(ctx)

    @commands.hybrid_command(name="shop", description="Open shop overview.")
    async def shop(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.premium.compact_codex_page("🛒 Omega Atelier", ["Rotating cosmetics", "Event caches", "Boost previews", "Purchase rate limits protect your wallet and the economy."], PremiumPalette.SOLAR))

    @commands.hybrid_command(name="friends", description="Open global friends guidance.")
    async def friends(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.help_embed("matchmaking"))

    @commands.hybrid_command(name="settings", description="Open settings overview.")
    async def settings(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.premium.compact_codex_page("⚙️ Settings", ["Accessibility, compact layouts, notification preferences, recovery prompts, and feed filters."], PremiumPalette.OMEGA))

    @commands.hybrid_command(name="help", aliases=["guide", "tutorial"], description="Open the interactive help Codex.")
    async def help_command(self, ctx: commands.Context, *, query: str | None = None) -> None:
        if query:
            results = self.help_service.search(query)
            lines = [f"**{row.topic.title}** · `{row.topic.category.value}`\n{row.topic.summary}" for row in results]
            await ctx.send(embed=self.premium.compact_codex_page("📖 Codex Search", lines or ["No topics found. Try `dungeon`, `clan`, `reward`, or `recover`."], PremiumPalette.OMEGA))
            return
        view = HelpCodexView(self.help_service)
        await ctx.send(embed=view.embed(), view=view)

    @commands.hybrid_command(name="recover", description="Recover an interrupted session.")
    async def recover(self, ctx: commands.Context) -> None:
        session = await self.bot.session_manager.recover_or_reject(ctx.author.id)
        if session is None:
            await ctx.send(embed=self.premium.compact_codex_page("🔄 Recovery", ["No active recoverable session was found.", "Open `!games` to begin a fresh adventure."], PremiumPalette.SOLAR))
            return
        await ctx.send(embed=self.premium.recovery_prompt(session.session_id, session.game_id))

    def help_embed(self, topic_id: str) -> discord.Embed:
        topic = self.help_service.topic(topic_id)
        return self.premium.compact_codex_page(f"📖 {topic.title}", [topic.summary, *topic.steps, "Commands: " + " · ".join(topic.commands), topic.advanced_tip], PremiumPalette.OMEGA)
