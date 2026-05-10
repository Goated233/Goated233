import discord
from app.startup import StartupCheck
from ui.embeds.theme import COLORS


class HealthEmbedFactory:
    def build(self, checks: list[StartupCheck]) -> discord.Embed:
        ok = all(check.ok for check in checks)
        embed = discord.Embed(
            title="🩺 Alpha Omega Arcade Health Check",
            description="Runtime readiness for Discord, PostgreSQL, Redis, owner config, and panel deployment.",
            color=COLORS["success"] if ok else COLORS["danger"],
        )
        for check in checks:
            embed.add_field(
                name=("🟢 " if check.ok else "🔴 ") + check.name.replace("_", " ").title(),
                value=check.detail[:1024],
                inline=False,
            )
        embed.set_footer(text="Owner-only panel • use /setup-panel to deploy the persistent launcher")
        return embed
