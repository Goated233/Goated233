from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord.ext import commands

from database.repository import Repository
from services.ai import AIService
from services.analytics import RelationshipAnalyticsService
from services.cards import CardService
from services.guidance import GuidanceService
from services.relationship import RelationshipService
from utils.embeds import CALM_BLUE, SOFT_GOLD, progress_bar, warm_embed
from utils.time import parse_when
from views.pagination import EmbedPaginator
from views.relationship import ComplaintModal, ConfirmView, NTM_ID, KOSI_ID, RelationshipHubView

TRACKER_TYPES = {"movie", "game", "reading"}


class RelationshipCog(commands.Cog):
    """Prefix entrypoints plus guided Discord UI for the relationship assistant."""

    def __init__(self, bot: commands.Bot, repo: Repository, ai: AIService) -> None:
        self.bot = bot
        self.repo = repo
        self.service = RelationshipService(repo)
        self.ai = ai
        self.cards = CardService()
        self.guidance = GuidanceService()
        self.analytics = RelationshipAnalyticsService(repo)

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        if ctx.guild and isinstance(ctx.author, discord.Member):
            await self.repo.upsert_user(ctx.guild.id, ctx.author.id, ctx.author.display_name)

    def _partner_id(self, couple: dict, user_id: int) -> int:
        return int(couple["partner_b_id"] if couple["partner_a_id"] == user_id else couple["partner_a_id"])

    async def _active_couple(self, ctx: commands.Context) -> dict:
        if ctx.guild is None:
            raise commands.NoPrivateMessage("This command needs a shared server context so I can find your couple link.")
        return await self.service.require_couple(ctx.guild.id, ctx.author.id)

    @commands.command(name="relationship", aliases=["rel", "home"])
    async def relationship_home(self, ctx: commands.Context) -> None:
        """Open the warm guided relationship hub."""
        couple = await self._active_couple(ctx)
        cid = str(couple["_id"])
        embed = warm_embed(
            "Your relationship hub",
            "Choose a guided action below. You can still use prefix commands, but buttons and forms make the hard parts easier.",
        )
        embed.add_field(name="Today", value="Daily check-in • appreciation prompt • memory reminder", inline=False)
        embed.add_field(name="Conflict care", value="Guided complaint mediation that DMs the other partner and never takes sides.", inline=False)
        embed.add_field(name="Track together", value="Bucket list • promises • visits • movies • games • reading", inline=False)
        await ctx.send(embed=embed, view=RelationshipHubView(self.repo, self.ai, cid, self._partner_id(couple, ctx.author.id)))

    @commands.group(name="couple", invoke_without_command=True)
    async def couple(self, ctx: commands.Context) -> None:
        await self.relationship_home(ctx)

    @couple.command(name="link")
    async def link(self, ctx: commands.Context, partner: discord.Member | None = None) -> None:
        """Create a couple link; defaults to ntm and Kosi for this personal bot."""
        if ctx.guild is None:
            return
        partner_id = partner.id if partner else (KOSI_ID if ctx.author.id == NTM_ID else NTM_ID)
        cid = await self.service.link_request(ctx.guild.id, ctx.author.id, partner_id)
        target = partner.mention if partner else f"<@{partner_id}>"
        await ctx.send(embed=warm_embed("Link request created", f"{target} can accept with `,couple accept`.\nRelationship ID: `{cid}`"))

    @couple.command(name="accept")
    async def accept(self, ctx: commands.Context) -> None:
        if ctx.guild is None:
            return
        ok = await self.service.accept(ctx.guild.id, ctx.author.id)
        await ctx.send(embed=warm_embed("Couple link activated 💞" if ok else "No pending link found", "You can open the guided hub with `,relationship`." if ok else "Ask your partner to run `,couple link` first."))

    @couple.command(name="stats")
    async def stats(self, ctx: commands.Context) -> None:
        couple = await self._active_couple(ctx)
        cid = str(couple["_id"])
        stats = await self.analytics.communication_stats(cid)
        streak = await self.analytics.streak_days(cid)
        love = await self.analytics.love_language_scores(cid)
        embed = warm_embed("Relationship statistics", f"Current check-in streak: **{streak} day(s)**", color=CALM_BLUE)
        embed.add_field(name="Activity", value="\n".join(f"**{k.replace('_', ' ').title()}**: {v}" for k, v in stats.items()), inline=False)
        embed.add_field(name="Love language signals", value="\n".join(f"**{k.replace('_', ' ').title()}**: {v}" for k, v in love.items()), inline=False)
        await ctx.send(embed=embed)

    @couple.command(name="card")
    async def card(self, ctx: commands.Context) -> None:
        couple = await self._active_couple(ctx)
        stats = await self.analytics.communication_stats(str(couple["_id"]))
        image = await self.cards.couple_card("Relationship Snapshot", [f"{k.title()}: {v}" for k, v in stats.items()])
        await ctx.send(file=discord.File(image, filename="couple-card.png"))

    @commands.command(name="counsel")
    async def counsel(self, ctx: commands.Context, *, message: str) -> None:
        couple = await self._active_couple(ctx)
        memories = [m["text"] for m in await self.repo.list_recent("ai_memories", str(couple["_id"]), 8)]
        async with ctx.typing():
            response = await self.ai.counsel(message, memories)
        await ctx.reply(embed=warm_embed("Gentle counselor", response, color=CALM_BLUE), mention_author=False)

    @commands.command(name="complaint", aliases=["concern"])
    async def complaint(self, ctx: commands.Context, *, text: str | None = None) -> None:
        couple = await self._active_couple(ctx)
        cid = str(couple["_id"])
        partner_id = self._partner_id(couple, ctx.author.id)
        if not text:
            await ctx.send(embed=warm_embed("Guided complaint mediation", "Use the button to explain what happened, how it felt, and what you need. I’ll then DM your partner for their side."), view=RelationshipHubView(self.repo, self.ai, cid, partner_id))
            return
        clean = self.guidance.validate_text(text, min_len=10)
        async with ctx.typing():
            mediation = await self.ai.mediate(clean, [])
        await self.repo.create("complaints", {"couple_id": cid, "author_id": ctx.author.id, "text": clean, "status": "mediated", "mediation": mediation})
        await ctx.reply(embed=warm_embed("Neutral mediation", mediation, color=CALM_BLUE), mention_author=False)

    @commands.command(name="memory")
    async def memory(self, ctx: commands.Context, *, text: str) -> None:
        couple = await self._active_couple(ctx)
        clean = self.guidance.validate_text(text, min_len=5)
        tags = self.guidance.suggest_memory_tags(clean)
        await self.repo.create("memories", {"couple_id": str(couple["_id"]), "author_id": ctx.author.id, "text": clean, "tags": tags})
        await ctx.send(embed=warm_embed("Memory saved 🌸", f"Suggested tags: `{', '.join(tags)}`"))

    @commands.command(name="journal")
    async def journal(self, ctx: commands.Context, title: str, *, body: str) -> None:
        couple = await self._active_couple(ctx)
        mood = await self.analytics.mood_correlation(str(couple["_id"]))
        await self.repo.create("journals", {"couple_id": str(couple["_id"]), "user_id": ctx.author.id, "title": title, "body": self.guidance.validate_text(body), "mood_average_at_entry": mood["average"]})
        await ctx.send(embed=warm_embed("Journal entry saved", f"I linked it with the current mood average: **{mood['average']}/10**."))

    @commands.command(name="mood")
    async def mood(self, ctx: commands.Context, score: int, *, note: str = "") -> None:
        if not 1 <= score <= 10:
            raise commands.BadArgument("Mood score must be 1-10. Example: `,mood 7 missing you but hopeful`")
        couple = await self._active_couple(ctx)
        await self.repo.create("moods", {"couple_id": str(couple["_id"]), "user_id": ctx.author.id, "score": score, "note": note})
        await ctx.send(embed=warm_embed("Mood logged", f"Saved **{score}/10**. Thank you for being honest."))

    @commands.command(name="goal")
    async def goal(self, ctx: commands.Context, progress: int | None = None, target: int | None = None, *, title: str) -> None:
        couple = await self._active_couple(ctx)
        progress = progress if progress is not None else 0
        target = target if target is not None else 10
        await self.repo.create("goals", {"couple_id": str(couple["_id"]), "title": title, "owner_id": ctx.author.id, "progress": progress, "target": target, "completed": progress >= target})
        await ctx.send(embed=warm_embed("Goal created 🎯", f"{title}\n{progress_bar(progress, target)}"))

    @commands.command(name="remind")
    async def remind(self, ctx: commands.Context, when: str, *, message: str) -> None:
        couple = await self._active_couple(ctx)
        await self.repo.create("reminders", {"couple_id": str(couple["_id"]), "user_id": ctx.author.id, "message": self.guidance.validate_text(message), "remind_at": parse_when(when), "delivered": False})
        await ctx.send(embed=warm_embed("Reminder scheduled", "I’ll DM you when it’s time."))

    @commands.command(name="daily")
    async def daily(self, ctx: commands.Context) -> None:
        couple = await self._active_couple(ctx)
        await ctx.send(embed=warm_embed("Daily check-in", "Press the button and I’ll ask about mood, appreciation, and what you need today."), view=RelationshipHubView(self.repo, self.ai, str(couple["_id"]), self._partner_id(couple, ctx.author.id)))

    @commands.command(name="weekly")
    async def weekly(self, ctx: commands.Context) -> None:
        couple = await self._active_couple(ctx)
        cid = str(couple["_id"])
        context = [str(doc) for doc in await self.repo.list_recent("checkins", cid, 14)] + [str(await self.analytics.mood_correlation(cid))]
        async with ctx.typing():
            review = await self.ai.weekly_review(context)
        await self.repo.create("weekly_reviews", {"couple_id": cid, "author_id": ctx.author.id, "summary": review})
        await ctx.send(embed=warm_embed("Weekly relationship review", review, color=SOFT_GOLD))

    @commands.command(name="appreciate")
    async def appreciate(self, ctx: commands.Context) -> None:
        couple = await self._active_couple(ctx)
        async with ctx.typing():
            prompt = await self.ai.appreciation_prompt([m["text"] for m in await self.repo.list_recent("memories", str(couple["_id"]), 5)])
        await ctx.send(embed=warm_embed("Appreciation prompt", prompt, color=SOFT_GOLD))

    @commands.command(name="positive")
    async def positive_memory(self, ctx: commands.Context) -> None:
        couple = await self._active_couple(ctx)
        memories = await self.repo.list_recent("memories", str(couple["_id"]), 50)
        if not memories:
            await ctx.send(embed=warm_embed("No memories yet", "Save one with `,memory our first movie night was so sweet`."))
            return
        memory = memories[datetime.now(timezone.utc).second % len(memories)]
        await ctx.send(embed=warm_embed("Random positive memory", memory["text"], color=SOFT_GOLD))

    @commands.command(name="bucket")
    async def bucket(self, ctx: commands.Context, *, item: str | None = None) -> None:
        couple = await self._active_couple(ctx)
        cid = str(couple["_id"])
        if item:
            await self.repo.create("bucket_items", {"couple_id": cid, "author_id": ctx.author.id, "title": self.guidance.validate_text(item), "done": False})
            await ctx.send(embed=warm_embed("Bucket list item added", item))
            return
        await self._paginate_collection(ctx, "bucket_items", cid, "Shared bucket list", "title")

    @commands.command(name="promise")
    async def promise(self, ctx: commands.Context, *, text: str) -> None:
        couple = await self._active_couple(ctx)
        await self.repo.create("promises", {"couple_id": str(couple["_id"]), "promiser_id": ctx.author.id, "text": self.guidance.validate_text(text), "kept": False})
        await ctx.send(embed=warm_embed("Promise tracked", text))

    @commands.command(name="visit")
    async def visit(self, ctx: commands.Context, date: str, *, note: str = "Next visit") -> None:
        couple = await self._active_couple(ctx)
        visit_at = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        days = max(0, (visit_at.date() - datetime.now(timezone.utc).date()).days)
        await self.repo.create("visits", {"couple_id": str(couple["_id"]), "user_id": ctx.author.id, "command": note, "visit_at": visit_at})
        await ctx.send(embed=warm_embed("Visit countdown", f"**{days} day(s)** until {note}."))

    @commands.command(name="track")
    async def track(self, ctx: commands.Context, kind: str, status: str, *, title: str) -> None:
        if kind not in TRACKER_TYPES:
            raise commands.BadArgument("Tracker type must be `movie`, `game`, or `reading`.")
        couple = await self._active_couple(ctx)
        await self.repo.create("trackers", {"couple_id": str(couple["_id"]), "kind": kind, "status": status, "title": self.guidance.validate_text(title), "user_id": ctx.author.id})
        await ctx.send(embed=warm_embed(f"{kind.title()} tracker updated", f"**{title}** → `{status}`"))

    @commands.command(name="list")
    async def list_items(self, ctx: commands.Context, collection: str = "memories") -> None:
        couple = await self._active_couple(ctx)
        allowed = {"memories", "goals", "promises", "bucket_items", "trackers", "journals"}
        if collection not in allowed:
            raise commands.BadArgument(f"Choose one of: {', '.join(sorted(allowed))}")
        await self._paginate_collection(ctx, collection, str(couple["_id"]), collection.replace("_", " ").title(), "text")

    @commands.command(name="anniversary")
    async def anniversary(self, ctx: commands.Context, date: str) -> None:
        parsed = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        couple = await self._active_couple(ctx)
        await self.repo.db.couples.update_one({"_id": couple["_id"]}, {"$set": {"anniversary": parsed}})
        await ctx.send(embed=warm_embed("Anniversary saved", f"Saved as **{parsed.date().isoformat()}**."))

    @commands.command(name="deletegoal")
    async def delete_goal(self, ctx: commands.Context, goal_id: str) -> None:
        view = ConfirmView(ctx.author.id)
        message = await ctx.send("Delete this goal? This cannot be undone.", view=view)
        await view.wait()
        if view.confirmed:
            from bson import ObjectId
            await self.repo.db.goals.delete_one({"_id": ObjectId(goal_id)})
        await message.delete(delay=3)

    @commands.command(name="hug")
    async def hug(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        await ctx.send(embed=warm_embed("Warm hug", f"{ctx.author.mention} sends a warm hug to {(member or ctx.author).mention}. 🤗"))

    @commands.command(name="dateidea")
    async def dateidea(self, ctx: commands.Context) -> None:
        await ctx.send(embed=warm_embed("Date idea", "Phones-away dessert walk, then each share one appreciation and one hope for the week. 🍰"))

    async def _paginate_collection(self, ctx: commands.Context, collection: str, couple_id: str, title: str, preferred_key: str) -> None:
        docs = await self.repo.list_recent(collection, couple_id, 50)
        pages: list[discord.Embed] = []
        for index in range(0, max(len(docs), 1), 5):
            chunk = docs[index:index + 5]
            embed = warm_embed(title, "No entries yet." if not chunk else f"Page {index // 5 + 1}")
            for doc in chunk:
                value = doc.get(preferred_key) or doc.get("title") or doc.get("body") or doc.get("message") or str(doc)
                embed.add_field(name=str(doc.get("created_at", "Saved"))[:16], value=str(value)[:900], inline=False)
            pages.append(embed)
        await ctx.send(embed=pages[0], view=EmbedPaginator(pages))
