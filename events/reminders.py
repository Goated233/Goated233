import discord
from discord.ext import tasks, commands
from datetime import datetime, timezone
from database.repository import Repository


class ReminderEvents(commands.Cog):
    """Background task that delivers due relationship reminders by DM."""
    def __init__(self, bot: commands.Bot, repo: Repository, interval: int) -> None:
        self.bot = bot; self.repo = repo; self.deliver_reminders.change_interval(seconds=interval); self.deliver_reminders.start()

    def cog_unload(self) -> None:
        self.deliver_reminders.cancel()

    @tasks.loop(seconds=60)
    async def deliver_reminders(self) -> None:
        cursor = self.repo.db.reminders.find({'delivered': False, 'remind_at': {'$lte': datetime.now(timezone.utc)}}).limit(25)
        async for reminder in cursor:
            user = self.bot.get_user(reminder['user_id']) or await self.bot.fetch_user(reminder['user_id'])
            await user.send(f"Relationship reminder: {reminder['message']}")
            await self.repo.db.reminders.update_one({'_id': reminder['_id']}, {'$set': {'delivered': True}})

    @deliver_reminders.before_loop
    async def before_deliver(self) -> None:
        await self.bot.wait_until_ready()
