import json
import discord
from discord.ext import commands
from database.repository import Repository


class AdminCog(commands.Cog):
    """Owner-only backup and configuration commands."""
    def __init__(self, bot: commands.Bot, repo: Repository, owner_ids: list[int]) -> None:
        self.bot = bot; self.repo = repo; self.owner_ids = set(owner_ids)

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await self.bot.is_owner(ctx) or ctx.author.id in self.owner_ids

    @commands.command(name='backup')
    async def backup(self, ctx: commands.Context) -> None:
        payload = {}
        for name in await self.repo.db.list_collection_names():
            payload[name] = [{**doc, '_id': str(doc['_id'])} async for doc in self.repo.db[name].find().limit(1000)]
        data = json.dumps(payload, default=str, indent=2).encode()
        await ctx.send(file=discord.File(fp=__import__('io').BytesIO(data), filename='relationship-backup.json'))

    @commands.command(name='rblog')
    async def rblog(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        await self.repo.db.settings.update_one({'guild_id': ctx.guild.id}, {'$set': {'logging_channel_id': channel.id}}, upsert=True)
        await ctx.send(f'Logging channel set to {channel.mention}.')
