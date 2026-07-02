from __future__ import annotations

import discord


class EmbedPaginator(discord.ui.View):
    """Reusable button paginator for long relationship lists."""

    def __init__(self, pages: list[discord.Embed], *, timeout: float = 180) -> None:
        super().__init__(timeout=timeout)
        self.pages = pages or [discord.Embed(title="Nothing here yet", description="Add an entry and I’ll keep it safe.")]
        self.index = 0
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        self.previous.disabled = self.index == 0
        self.next.disabled = self.index >= len(self.pages) - 1

    @discord.ui.button(label="Previous", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.index = max(0, self.index - 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="Next", emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.index = min(len(self.pages) - 1, self.index + 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)
