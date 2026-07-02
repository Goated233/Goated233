from __future__ import annotations

import discord
from discord.ext import commands

from utils.embeds import CALM_BLUE, SOFT_GOLD, warm_embed
from views.pagination import EmbedPaginator


class RelationshipHelpCog(commands.Cog):
    """Polished command discovery pages for guided and prefix workflows."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="help", aliases=["commands", "guide"])
    async def help_command(self, ctx: commands.Context) -> None:
        pages = [
            warm_embed("Start here", "`,relationship` opens the guided hub. Most important flows use buttons and modals so you do not need long commands.", color=SOFT_GOLD),
            warm_embed("Care & conflict", "`,daily` check-in\n`,complaint` guided mediation\n`,counsel <message>` neutral AI support\n`,weekly` relationship review\n`,appreciate` AI appreciation prompt", color=CALM_BLUE),
            warm_embed("Track together", "`,memory <text>` with auto-tags\n`,journal <title> <body>` with mood correlation\n`,goal [progress] [target] <title>` progress bars\n`,promise <text>`\n`,bucket [item]`\n`,visit YYYY-MM-DD <note>`", color=SOFT_GOLD),
            warm_embed("Fun & shared media", "`,track movie watching <title>`\n`,track game playing <title>`\n`,track reading reading <title>`\n`,positive` random memory\n`,hug [member]`\n`,dateidea`", color=CALM_BLUE),
            warm_embed("Lists & cards", "`,list memories|goals|promises|bucket_items|trackers|journals` paginated lists\n`,couple stats` communication and love-language analytics\n`,couple card` image card\n`,backup` owner export", color=SOFT_GOLD),
        ]
        await ctx.send(embed=pages[0], view=EmbedPaginator(pages))
