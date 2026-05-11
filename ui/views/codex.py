import discord

from core.help import HelpCategory, HelpCodexService
from core.onboarding import OnboardingService, StarterClass
from ui.embeds.premium import DIVIDER, PremiumEmbedFactory, PremiumPalette


class HelpCodexView(discord.ui.View):
    def __init__(self, service: HelpCodexService | None = None):
        super().__init__(timeout=300)
        self.service = service or HelpCodexService()
        self.index = 0
        self.topics = self.service.topics

    def embed(self) -> discord.Embed:
        topic = self.topics[self.index]
        lines = [f"**{topic.summary}**", DIVIDER, *[f"• {step}" for step in topic.steps], "", "**Commands** " + " · ".join(f"`{command}`" for command in topic.commands), "**Next** " + " · ".join(topic.next_actions), f"💡 *{topic.advanced_tip}*"]
        embed = PremiumEmbedFactory().compact_codex_page(f"📖 Codex // {topic.title}", lines, PremiumPalette.OMEGA)
        embed.set_footer(text=f"Help Codex • {topic.category.value} • {self.index + 1}/{len(self.topics)}")
        return embed

    @discord.ui.button(label="Back", emoji="◀️", style=discord.ButtonStyle.secondary, custom_id="aoa:help:back")
    async def back(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.index = max(0, self.index - 1)
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Next", emoji="▶️", style=discord.ButtonStyle.secondary, custom_id="aoa:help:next")
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.index = min(len(self.topics) - 1, self.index + 1)
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Beginner", emoji="🌟", style=discord.ButtonStyle.primary, custom_id="aoa:help:beginner")
    async def beginner(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.topics = self.service.category_topics(HelpCategory.START) + self.service.category_topics(HelpCategory.PROGRESSION) + self.service.category_topics(HelpCategory.DUNGEON)
        self.index = 0
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Recovery", emoji="🔄", style=discord.ButtonStyle.secondary, custom_id="aoa:help:recovery")
    async def recovery(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.topics = self.service.category_topics(HelpCategory.RECOVERY)
        self.index = 0
        await interaction.response.edit_message(embed=self.embed(), view=self)


class OnboardingView(discord.ui.View):
    def __init__(self, service: OnboardingService | None = None):
        super().__init__(timeout=300)
        self.service = service or OnboardingService()
        self.step = 0

    def embed(self) -> discord.Embed:
        step = self.service.cinematic_flow()[self.step]
        embed = PremiumEmbedFactory().compact_codex_page(
            f"🌌 {step.title}",
            [step.body, DIVIDER, f"**Action:** {step.action_label}", f"**Reward:** {step.reward_preview}", "Every choice is saved server-side and can be recovered."],
            PremiumPalette.MYTHIC,
        )
        embed.set_footer(text=f"Onboarding • Step {self.step + 1}/{len(self.service.cinematic_flow())}")
        return embed

    @discord.ui.button(label="Continue", emoji="✨", style=discord.ButtonStyle.primary, custom_id="aoa:onboarding:continue")
    async def continue_step(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.step = min(self.step + 1, len(self.service.cinematic_flow()) - 1)
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Vanguard", emoji="🛡️", style=discord.ButtonStyle.secondary, custom_id="aoa:onboarding:vanguard")
    async def vanguard(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(embed=self.class_embed(StarterClass.VANGUARD), view=self)

    @discord.ui.button(label="Riftwalker", emoji="⚡", style=discord.ButtonStyle.secondary, custom_id="aoa:onboarding:riftwalker")
    async def riftwalker(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(embed=self.class_embed(StarterClass.RIFTWALKER), view=self)

    @discord.ui.button(label="Starweaver", emoji="✨", style=discord.ButtonStyle.secondary, custom_id="aoa:onboarding:starweaver")
    async def starweaver(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(embed=self.class_embed(StarterClass.STARWEAVER), view=self)

    def class_embed(self, player_class: StarterClass) -> discord.Embed:
        loadout = self.service.loadout(player_class)
        return PremiumEmbedFactory().compact_codex_page(
            f"{loadout.title} Selected",
            ["Starter rewards prepared:", *[f"• `{key}`: **{value}**" for key, value in loadout.rewards.items()], "", "Cosmetics:", *loadout.cosmetics, "", "Beginner Quests:", *loadout.beginner_quests],
            PremiumPalette.SOLAR,
        )
