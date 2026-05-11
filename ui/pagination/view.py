from collections.abc import Callable, Sequence
import discord


class PaginatedEmbedView(discord.ui.View):
    def __init__(self, pages: Sequence[discord.Embed], footer_builder: Callable[[int, int], str] | None = None):
        super().__init__(timeout=180)
        if not pages:
            raise ValueError("PaginatedEmbedView requires at least one page")
        self.pages = list(pages)
        self.index = 0
        self.footer_builder = footer_builder
        self._sync_buttons()

    def current_embed(self) -> discord.Embed:
        embed = self.pages[self.index].copy()
        if self.footer_builder:
            embed.set_footer(text=self.footer_builder(self.index + 1, len(self.pages)))
        return embed

    def _sync_buttons(self) -> None:
        self.previous.disabled = self.index == 0
        self.next.disabled = self.index >= len(self.pages) - 1

    @discord.ui.button(label="Back", emoji="◀️", style=discord.ButtonStyle.secondary, custom_id="aoa:page:prev")
    async def previous(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.index = max(0, self.index - 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)

    @discord.ui.button(label="Next", emoji="▶️", style=discord.ButtonStyle.secondary, custom_id="aoa:page:next")
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.index = min(len(self.pages) - 1, self.index + 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)
