import discord
from discord import app_commands
from app.startup import StartupValidator
from ui.embeds.health import HealthEmbedFactory
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
        await interaction.channel.send(
            embed=build_home_embed(self.bot.settings.owner_display),
            view=ArcadeHomeView(self.bot.admin_service, self.bot.session_manager),
        )

    @app_commands.command(name="health", description="Run startup health checks for the arcade platform.")
    async def health(self, interaction: discord.Interaction) -> None:
        validator = StartupValidator(self.bot.settings, self.bot.db_engine, self.bot.redis)
        checks = await validator.validate_all()
        await interaction.response.send_message(embed=HealthEmbedFactory().build(checks), ephemeral=True)
