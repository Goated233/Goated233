from __future__ import annotations

from datetime import datetime, timezone

import discord

from database.repository import Repository
from services.ai import AIService
from services.guidance import GuidanceService
from utils.embeds import CALM_BLUE, SOFT_GOLD, warm_embed

NTM_ID = 1417262684990083142
KOSI_ID = 1516247373716787363


class ConfirmView(discord.ui.View):
    """Two-button confirmation dialog for destructive relationship actions."""

    def __init__(self, author_id: int) -> None:
        super().__init__(timeout=60)
        self.author_id = author_id
        self.confirmed: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This confirmation belongs to someone else.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", emoji="✅", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.confirmed = True
        await interaction.response.edit_message(content="Confirmed.", embed=None, view=None)
        self.stop()

    @discord.ui.button(label="Cancel", emoji="🕊️", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.confirmed = False
        await interaction.response.edit_message(content="Cancelled. Nothing was changed.", embed=None, view=None)
        self.stop()


class ComplaintModal(discord.ui.Modal, title="Share what happened"):
    """Guided complaint form that gathers both facts and feelings without blame."""

    situation = discord.ui.TextInput(label="What happened?", style=discord.TextStyle.paragraph, max_length=900)
    feeling = discord.ui.TextInput(label="How did it make you feel?", style=discord.TextStyle.paragraph, max_length=500)
    need = discord.ui.TextInput(label="What do you need next?", style=discord.TextStyle.paragraph, max_length=500)

    def __init__(self, repo: Repository, ai: AIService, couple_id: str, partner_id: int) -> None:
        super().__init__()
        self.repo = repo
        self.ai = ai
        self.couple_id = couple_id
        self.partner_id = partner_id
        self.guidance = GuidanceService()

    async def on_submit(self, interaction: discord.Interaction) -> None:
        text = self.guidance.validate_text(f"Situation: {self.situation}\nFeeling: {self.feeling}\nNeed: {self.need}", min_len=20)
        await interaction.response.send_message(embed=warm_embed("I’m mediating this gently", "I saved your side and I’m preparing a neutral summary. I’ll DM your partner if possible."), ephemeral=True)
        mediation = await self.ai.mediate(text, [])
        complaint_id = await self.repo.create("complaints", {"couple_id": self.couple_id, "author_id": interaction.user.id, "text": text, "status": "mediated", "mediation": mediation})
        partner = interaction.client.get_user(self.partner_id) or await interaction.client.fetch_user(self.partner_id)
        view = PartnerReflectionView(self.repo, self.ai, complaint_id, self.couple_id)
        try:
            await partner.send(embed=warm_embed("A relationship concern needs care", mediation, color=CALM_BLUE), view=view)
        except discord.HTTPException:
            await interaction.followup.send("I could not DM your partner. Ask them to open DMs with the bot, then try again.", ephemeral=True)


class PartnerReflectionModal(discord.ui.Modal, title="Your reflection"):
    """Partner response modal used by the guided complaint workflow."""

    viewpoint = discord.ui.TextInput(label="What is your viewpoint?", style=discord.TextStyle.paragraph, max_length=900)
    misunderstanding = discord.ui.TextInput(label="What might be misunderstood?", style=discord.TextStyle.paragraph, max_length=500)
    compromise = discord.ui.TextInput(label="What compromise feels fair?", style=discord.TextStyle.paragraph, max_length=500)

    def __init__(self, repo: Repository, ai: AIService, complaint_id: str, couple_id: str) -> None:
        super().__init__()
        self.repo = repo
        self.ai = ai
        self.complaint_id = complaint_id
        self.couple_id = couple_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        reflection = f"Partner viewpoint: {self.viewpoint}\nPossible misunderstanding: {self.misunderstanding}\nCompromise: {self.compromise}"
        await self.repo.create("complaint_reflections", {"couple_id": self.couple_id, "complaint_id": self.complaint_id, "author_id": interaction.user.id, "text": reflection})
        await interaction.response.defer(ephemeral=True, thinking=True)
        final = await self.ai.counsel("Create a balanced conclusion from both viewpoints. Ask one clarifying question and suggest a compromise. Never take sides or shame either person.", [reflection])
        from bson import ObjectId
        await self.repo.db.complaints.update_one({"_id": ObjectId(self.complaint_id)}, {"$set": {"status": "resolved", "final_summary": final, "updated_at": datetime.now(timezone.utc)}})
        await interaction.followup.send(embed=warm_embed("Balanced next step", final, color=SOFT_GOLD), ephemeral=True)


class PartnerReflectionView(discord.ui.View):
    """DM view that lets the other partner respond to a complaint safely."""

    def __init__(self, repo: Repository, ai: AIService, complaint_id: str, couple_id: str) -> None:
        super().__init__(timeout=604800)
        self.repo = repo
        self.ai = ai
        self.complaint_id = complaint_id
        self.couple_id = couple_id

    @discord.ui.button(label="Share my side", emoji="📝", style=discord.ButtonStyle.primary)
    async def reflect(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(PartnerReflectionModal(self.repo, self.ai, self.complaint_id, self.couple_id))


class RelationshipHubView(discord.ui.View):
    """Button hub for command discovery and guided relationship actions."""

    def __init__(self, repo: Repository, ai: AIService, couple_id: str, partner_id: int) -> None:
        super().__init__(timeout=300)
        self.repo = repo
        self.ai = ai
        self.couple_id = couple_id
        self.partner_id = partner_id

    @discord.ui.button(label="Daily check-in", emoji="🌤️", style=discord.ButtonStyle.primary)
    async def checkin(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(CheckInModal(self.repo, self.couple_id))

    @discord.ui.button(label="Raise concern", emoji="🕊️", style=discord.ButtonStyle.secondary)
    async def concern(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(ComplaintModal(self.repo, self.ai, self.couple_id, self.partner_id))

    @discord.ui.button(label="Add memory", emoji="🌸", style=discord.ButtonStyle.secondary)
    async def memory(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(MemoryModal(self.repo, self.couple_id))


class CheckInModal(discord.ui.Modal, title="Daily relationship check-in"):
    """Daily guided check-in that stores mood, gratitude, and needs."""

    mood = discord.ui.TextInput(label="Mood from 1-10", max_length=2)
    gratitude = discord.ui.TextInput(label="One thing you appreciate today", style=discord.TextStyle.paragraph, max_length=500)
    need = discord.ui.TextInput(label="One thing you need today", style=discord.TextStyle.paragraph, max_length=500)

    def __init__(self, repo: Repository, couple_id: str) -> None:
        super().__init__()
        self.repo = repo
        self.couple_id = couple_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        score = int(str(self.mood))
        if not 1 <= score <= 10:
            await interaction.response.send_message("Mood needs to be a number from 1 to 10.", ephemeral=True)
            return
        await self.repo.create("checkins", {"couple_id": self.couple_id, "user_id": interaction.user.id, "mood": score, "gratitude": str(self.gratitude), "need": str(self.need)})
        await self.repo.create("moods", {"couple_id": self.couple_id, "user_id": interaction.user.id, "score": score, "note": str(self.need)})
        await interaction.response.send_message(embed=warm_embed("Check-in saved", "Thank you for showing up today. I’ll use this to make the weekly review more personal."), ephemeral=True)


class MemoryModal(discord.ui.Modal, title="Save a positive memory"):
    """Guided memory modal with automatic tag suggestions."""

    memory = discord.ui.TextInput(label="What should we remember?", style=discord.TextStyle.paragraph, max_length=1000)

    def __init__(self, repo: Repository, couple_id: str) -> None:
        super().__init__()
        self.repo = repo
        self.couple_id = couple_id
        self.guidance = GuidanceService()

    async def on_submit(self, interaction: discord.Interaction) -> None:
        text = self.guidance.validate_text(str(self.memory), min_len=5)
        tags = self.guidance.suggest_memory_tags(text)
        await self.repo.create("memories", {"couple_id": self.couple_id, "author_id": interaction.user.id, "text": text, "tags": tags})
        await interaction.response.send_message(embed=warm_embed("Memory saved", f"Suggested tags: `{', '.join(tags)}`"), ephemeral=True)
