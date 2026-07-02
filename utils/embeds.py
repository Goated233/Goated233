from __future__ import annotations

import discord

WARM_ROSE = 0xE8839A
SOFT_GOLD = 0xF6C177
CALM_BLUE = 0x8AADF4


def warm_embed(title: str, description: str, *, color: int = WARM_ROSE) -> discord.Embed:
    """Build a consistent warm relationship-assistant embed."""
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="ntm × Kosi Relationship Assistant • private, gentle, never taking sides")
    return embed


def progress_bar(value: int, total: int, *, width: int = 12) -> str:
    """Render a compact unicode progress bar for goals and trackers."""
    total = max(total, 1)
    value = max(0, min(value, total))
    filled = round((value / total) * width)
    return "▰" * filled + "▱" * (width - filled) + f" {value}/{total}"
