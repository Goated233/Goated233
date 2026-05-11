import discord
from core.admin.service import PlatformStats
from ui.embeds.progress import format_uptime
from ui.embeds.theme import COLORS


class AboutEmbedFactory:
    def __init__(self, owner_display: str):
        self.owner_display = owner_display

    def build(self, stats: PlatformStats) -> discord.Embed:
        embed = discord.Embed(
            title="🌌 Alpha Omega Arcade • System Info",
            description=(
                "A premium button-first Discord gaming platform with persistent progression, "
                "global events, leaderboards, clans, matchmaking, and reusable game engines."
            ),
            color=COLORS["info"],
        )
        embed.add_field(name="👑 Owner", value=self.owner_display, inline=True)
        embed.add_field(name="⏱️ Uptime", value=format_uptime(stats.uptime_seconds), inline=True)
        embed.add_field(name="🧩 Shards", value=str(stats.shard_count), inline=True)
        embed.add_field(name="🏰 Servers", value=str(stats.server_count), inline=True)
        embed.add_field(name="👥 Active Users", value=str(stats.active_users), inline=True)
        embed.add_field(name="🎮 Active Games", value=str(stats.active_games), inline=True)
        embed.add_field(name="🕹️ Redis Sessions", value=str(stats.active_sessions), inline=True)
        embed.add_field(name="🗄️ Database", value=self._status(stats.database_status), inline=True)
        embed.add_field(name="⚡ Redis", value=self._status(stats.redis_status), inline=True)
        embed.set_footer(text="Button-first • Persistent views • PostgreSQL • Redis • discord.py")
        return embed

    def _status(self, value: str) -> str:
        return "🟢 Online" if value == "online" else "🟡 Degraded"
