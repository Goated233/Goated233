from datetime import datetime, timezone
import logging
import discord
from discord.ext import commands
from app.commands import OwnerSetupCog
from app.config import get_settings
from app.logger import configure_logging
from app.startup import StartupValidator
from core.admin.service import AdminService
from core.sessions.manager import DistributedSessionManager
from database.session import create_engine, create_session_factory
from infra.redis.client import create_redis
from infra.redis.sessions import SessionStore
from ui.views.home import ArcadeHomeView, build_home_embed

logger = logging.getLogger(__name__)


class AlphaOmegaArcadeBot(commands.Bot):
    def __init__(self) -> None:
        self.settings = get_settings()
        configure_logging(self.settings.log_level)
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = False
        super().__init__(command_prefix="aoa!", intents=intents, help_command=None)
        self.started_at = datetime.now(timezone.utc)
        self.db_engine = create_engine(self.settings.database_url)
        self.session_factory = create_session_factory(self.db_engine)
        self.redis = create_redis(self.settings.redis_url)
        self.session_store = SessionStore(self.redis, self.settings.session_ttl_seconds)
        self.session_manager = DistributedSessionManager(self.session_store)
        self.admin_service = AdminService(
            self.settings,
            self.session_factory,
            self.redis,
            self.session_store,
            self,
            self.started_at,
        )

    async def setup_hook(self) -> None:
        validator = StartupValidator(self.settings, self.db_engine, self.redis)
        await validator.assert_ready()
        self.add_view(ArcadeHomeView(self.admin_service, self.session_manager))
        self.tree.add_command(OwnerSetupCog(self))
        await self.tree.sync()
        logger.info("Alpha Omega Arcade startup checks passed and owner commands synced")

    async def on_ready(self) -> None:
        if self.user is None:
            return
        logger.info("Alpha Omega Arcade online as %s • Owner: %s", self.user, self.settings.owner_display)

    async def close(self) -> None:
        await self.redis.aclose()
        await self.db_engine.dispose()
        await super().close()


async def send_home_panel(channel: discord.abc.Messageable, bot: AlphaOmegaArcadeBot) -> discord.Message:
    return await channel.send(
        embed=build_home_embed(bot.settings.owner_display),
        view=ArcadeHomeView(bot.admin_service, bot.session_manager),
    )


def main() -> None:
    bot = AlphaOmegaArcadeBot()
    if not bot.settings.discord_token:
        raise RuntimeError("DISCORD_TOKEN is required. Copy .env.example to .env and set a real Discord bot token.")
    bot.run(bot.settings.discord_token)


if __name__ == "__main__":
    main()
