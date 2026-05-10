import discord
from core.admin.permissions import PermissionContext
from core.admin.service import PlatformStats
from ui.embeds.progress import format_uptime
from ui.embeds.theme import COLORS


class AdminEmbedFactory:
    def dashboard(self, context: PermissionContext, stats: PlatformStats) -> discord.Embed:
        embed = discord.Embed(
            title="👑 Alpha Omega Arcade Admin Console",
            description=(
                f"{context.badge} **{context.display_name}**\n"
                "Use the control panels below. Dangerous actions require confirmation and are audit logged."
            ),
            color=COLORS["admin"],
        )
        embed.add_field(name="🏰 Servers", value=str(stats.server_count), inline=True)
        embed.add_field(name="👥 Users", value=str(stats.active_users), inline=True)
        embed.add_field(name="🎮 Active Games", value=str(stats.active_games), inline=True)
        embed.add_field(name="🕹️ Redis Sessions", value=str(stats.active_sessions), inline=True)
        embed.add_field(name="🗄️ Database", value=stats.database_status.title(), inline=True)
        embed.add_field(name="⚡ Redis", value=stats.redis_status.title(), inline=True)
        embed.add_field(name="⏱️ Uptime", value=format_uptime(stats.uptime_seconds), inline=True)
        embed.add_field(name="🛡️ Security", value="Owner override active" if context.is_owner else "Delegated admin", inline=True)
        embed.set_footer(text="Every admin button writes audit history with rollback metadata when possible.")
        return embed

    def moderation(self) -> discord.Embed:
        return discord.Embed(
            title="🛡️ Moderation Dashboard",
            description="Review punishments, exploit flags, account notes, blacklist state, and anti-cheat evidence.",
            color=COLORS["warning"],
        ).add_field(
            name="Available actions",
            value="Ban/unban games • Warnings • Notes • Exploit review • Shadow mute • Blacklist",
            inline=False,
        )

    def economy(self) -> discord.Embed:
        return discord.Embed(
            title="💰 Economy Control",
            description="Inspect transactions, freeze economy flows, rollback suspicious grants, and inject audited rewards.",
            color=COLORS["legendary"],
        )

    def analytics(self) -> discord.Embed:
        return discord.Embed(
            title="📊 Analytics Dashboard",
            description="Track retention, player activity, game popularity, economy inflation, abuse statistics, and button usage.",
            color=COLORS["info"],
        )
