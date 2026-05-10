from datetime import timedelta

import discord

from core.limits import LimitResult, format_duration
from ui.embeds.theme import COLORS


class LimitEmbedFactory:
    def blocked(self, result: LimitResult, title: str = "Action blocked") -> discord.Embed:
        embed = discord.Embed(
            title=f"🛡️ {title}",
            description=result.message,
            color=COLORS["warning"],
        )
        if result.retry_after_seconds:
            embed.add_field(name="Retry In", value=format_duration(timedelta(seconds=result.retry_after_seconds)), inline=True)
        if result.active_reference:
            embed.add_field(name="Active Reference", value=f"`{result.active_reference}`", inline=False)
        if result.recovery_action:
            embed.add_field(name="Recovery", value=result.recovery_action, inline=False)
        embed.set_footer(text="Alpha Omega protections • limits keep the global world fair")
        return embed
