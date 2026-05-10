from dataclasses import dataclass
from enum import StrEnum
import discord
from ui.embeds.progress import progress_bar
from ui.embeds.theme import COLORS


class Rarity(StrEnum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


RARITY_COLORS = {
    Rarity.COMMON: 0x94A3B8,
    Rarity.UNCOMMON: 0x22C55E,
    Rarity.RARE: 0x3B82F6,
    Rarity.EPIC: 0xA855F7,
    Rarity.LEGENDARY: 0xF97316,
    Rarity.MYTHIC: 0xEC4899,
}

RARITY_ICONS = {
    Rarity.COMMON: "⚪",
    Rarity.UNCOMMON: "🟢",
    Rarity.RARE: "🔵",
    Rarity.EPIC: "🟣",
    Rarity.LEGENDARY: "🟠",
    Rarity.MYTHIC: "🌈",
}


@dataclass(frozen=True)
class ProfileCardData:
    username: str
    level: int
    xp: int
    next_level_xp: int
    coins: int
    gems: int
    ranked_rating: int
    title: str
    clan: str | None = None
    avatar_url: str | None = None


class PremiumCardFactory:
    def profile(self, data: ProfileCardData) -> discord.Embed:
        embed = discord.Embed(
            title=f"👤 {data.username} • {data.title}",
            description=(
                f"Level **{data.level}**  {progress_bar(data.xp, data.next_level_xp)}\n"
                f"`{data.xp:,}/{data.next_level_xp:,} XP`"
            ),
            color=COLORS["primary"],
        )
        if data.avatar_url:
            embed.set_thumbnail(url=data.avatar_url)
        embed.add_field(name="🪙 Coins", value=f"{data.coins:,}", inline=True)
        embed.add_field(name="💎 Gems", value=f"{data.gems:,}", inline=True)
        embed.add_field(name="⚔️ Rating", value=f"{data.ranked_rating:,}", inline=True)
        embed.add_field(name="🛡️ Clan", value=data.clan or "No clan", inline=True)
        return embed

    def loot_reward(self, title: str, drops: list[dict], xp: int, coins: int) -> discord.Embed:
        description = ["✨ **Rewards acquired!**", f"`+{xp:,} XP`  •  `+{coins:,} coins`"]
        for drop in drops:
            rarity = Rarity(str(drop.get("rarity", "common")))
            description.append(
                f"{RARITY_ICONS[rarity]} **{drop.get('name', drop.get('item_id', 'Unknown Item'))}** · {rarity.title()} x{drop.get('quantity', 1)}"
            )
        color = RARITY_COLORS[Rarity(str(drops[0].get("rarity", "common")))] if drops else COLORS["success"]
        return discord.Embed(title=f"🎁 {title}", description="\n".join(description), color=color)

    def match_found(self, game_name: str, mode: str, players: list[str], estimated_seconds: int) -> discord.Embed:
        return discord.Embed(
            title="⚡ Match Found",
            description=(
                f"**{game_name}** · `{mode}`\n"
                f"Players: {', '.join(players)}\n"
                f"Starting in **{estimated_seconds}s** — get ready!"
            ),
            color=COLORS["success"],
        )

    def event_announcement(self, name: str, modifiers: dict, ends_in: str) -> discord.Embed:
        lines = [f"🌍 **{name} is live!**", f"Ends in: `{ends_in}`", ""]
        lines.extend(f"• **{key.replace('_', ' ').title()}**: `{value}`" for key, value in modifiers.items())
        return discord.Embed(title="🌍 World Event", description="\n".join(lines), color=COLORS["legendary"])
