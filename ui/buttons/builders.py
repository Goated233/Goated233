import discord


def nav_button(custom_id: str, label: str, emoji: str, row: int = 0) -> discord.ui.Button:
    return discord.ui.Button(
        custom_id=custom_id,
        label=label,
        emoji=emoji,
        style=discord.ButtonStyle.secondary,
        row=row,
    )


def primary_action(custom_id: str, label: str, emoji: str, row: int = 0) -> discord.ui.Button:
    return discord.ui.Button(
        custom_id=custom_id,
        label=label,
        emoji=emoji,
        style=discord.ButtonStyle.primary,
        row=row,
    )


def danger_action(custom_id: str, label: str, emoji: str = "⚠️", row: int = 0) -> discord.ui.Button:
    return discord.ui.Button(
        custom_id=custom_id,
        label=label,
        emoji=emoji,
        style=discord.ButtonStyle.danger,
        row=row,
    )
