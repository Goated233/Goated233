import discord
from core.inventory.service import InventoryEntry
from ui.cards.premium import RARITY_COLORS, RARITY_ICONS, Rarity


class InventoryCardFactory:
    def menu(self, username: str, entries: list[InventoryEntry], page: int, total_pages: int) -> discord.Embed:
        embed = discord.Embed(
            title=f"🎒 {username}'s Inventory",
            description="Filter, sort, equip, and inspect loot with buttons and item tooltips.",
            color=0x7C3AED,
        )
        if not entries:
            embed.add_field(name="Empty", value="No items match this filter yet. Go raid a dungeon!", inline=False)
        for entry in entries:
            rarity = Rarity(entry.rarity)
            equipped = "✅ Equipped" if entry.equipped else "▫️ Stored"
            embed.add_field(
                name=f"{RARITY_ICONS[rarity]} {entry.name} x{entry.quantity}",
                value=f"`{entry.item_type}` • `{entry.rarity}` • {equipped}\n{entry.description[:120]}",
                inline=False,
            )
        embed.set_footer(text=f"Page {page}/{total_pages} • Tap an item for tooltips and equip controls")
        return embed

    def tooltip(self, entry: InventoryEntry) -> discord.Embed:
        rarity = Rarity(entry.rarity)
        embed = discord.Embed(
            title=f"{RARITY_ICONS[rarity]} {entry.name}",
            description=entry.description,
            color=RARITY_COLORS[rarity],
        )
        embed.add_field(name="Rarity", value=entry.rarity.title(), inline=True)
        embed.add_field(name="Type", value=entry.item_type.title(), inline=True)
        embed.add_field(name="Quantity", value=str(entry.quantity), inline=True)
        embed.add_field(name="Slot", value=entry.slot or "—", inline=True)
        embed.add_field(name="Status", value="Equipped" if entry.equipped else "Stored", inline=True)
        return embed
