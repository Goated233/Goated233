import logging
import discord
from discord.ext import commands
from config import get_settings
from database.client import Mongo
from database.repository import Repository
from services.ai import AIService
from utils.logging import configure_logging
from cogs.relationship import RelationshipCog
from cogs.admin import AdminCog
from cogs.help import RelationshipHelpCog
from events.reminders import ReminderEvents

logger = logging.getLogger(__name__)


class RelationshipBot(commands.Bot):
    def __init__(self) -> None:
        self.settings = get_settings()
        configure_logging(self.settings.log_level)
        intents = discord.Intents.default(); intents.message_content = True; intents.guilds = True; intents.members = True
        super().__init__(command_prefix=self.settings.command_prefix, intents=intents, help_command=None)
        self.mongo = Mongo(self.settings)
        self.repo: Repository | None = None

    async def setup_hook(self) -> None:
        db = await self.mongo.connect(); self.repo = Repository(db); await self.repo.ensure_indexes()
        ai = AIService(self.settings)
        await self.add_cog(RelationshipCog(self, self.repo, ai))
        await self.add_cog(AdminCog(self, self.repo, self.settings.owner_ids))
        await self.add_cog(RelationshipHelpCog(self))
        await self.add_cog(ReminderEvents(self, self.repo, self.settings.reminder_poll_seconds))
        logger.info('Relationship bot loaded with prefix %s', self.settings.command_prefix)

    async def on_ready(self) -> None:
        logger.info('Relationship bot online as %s', self.user)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("I don’t know that command yet. Try `,help` or `,relationship` for guided options.")
            return
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(str(error))
            return
        if isinstance(error, commands.BadArgument | commands.MissingRequiredArgument):
            await ctx.send(f"I need a little more detail: {error}. Try `,help` for examples.")
            return
        logger.exception("Command failed", exc_info=error)
        await ctx.send("Something went wrong while handling that. I logged it so it can be fixed.")

    async def close(self) -> None:
        await self.mongo.close(); await super().close()


def main() -> None:
    bot = RelationshipBot()
    if not bot.settings.discord_token:
        raise RuntimeError('DISCORD_TOKEN is required')
    bot.run(bot.settings.discord_token)


if __name__ == '__main__':
    main()
