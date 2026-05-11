import discord
from core.cosmetics.service import CosmeticsService
from core.feed.service import FeedEventType, GlobalFeedService
from core.retention.service import RetentionService
from core.shop.service import ShopService
from core.social.service import InviteType, SocialService
from core.tournaments.service import TournamentService
from core.world_bosses.service import WorldBossService
from ui.branding.identity import THEMES
from ui.embeds.progress import progress_bar
from ui.embeds.theme import COLORS


class EngagementHubView(discord.ui.View):
    def __init__(self, home_view: discord.ui.View | None = None):
        super().__init__(timeout=None)
        self.home_view = home_view

    @discord.ui.button(label="Claim Daily", emoji="🔥", style=discord.ButtonStyle.success, custom_id="aoa:retention:daily", row=0)
    async def daily(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        reward = RetentionService().login_reward(None, 6)
        embed = discord.Embed(
            title="🔥 Daily Login Claimed",
            description=f"{reward.visual}\n`+{reward.xp} XP` • `+{reward.coins} coins` • `+{reward.gems} gems`\nBooster: `{reward.booster_minutes}m`",
            color=COLORS["success"],
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Quest Board", emoji="🎯", style=discord.ButtonStyle.primary, custom_id="aoa:retention:quests", row=0)
    async def quests(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        service = RetentionService()
        quests = service.quest_rotation(interaction.user.id)
        metrics = {"dungeon_clears": 0, "button_clicks": 7, "loot_drops": 2, "sessions_completed": 4, "party_actions": 1, "legendary_drops": 0}
        lines = []
        for quest in quests[:5]:
            progress = service.progress(quest, metrics)
            lines.append(f"{quest.icon} **{quest.name}** `{progress.current}/{quest.target}` {progress_bar(progress.current, quest.target, 8)}")
        embed = discord.Embed(title="🎯 Rotating Quest Board", description="\n".join(lines), color=COLORS["primary"])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Battle Pass", emoji="🎟️", style=discord.ButtonStyle.secondary, custom_id="aoa:retention:pass", row=0)
    async def battle_pass(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="🎟️ Season Pass",
            description="Tier `12/50`\n🌟 `2,450/3,000` Season XP\nNext rewards: `Solar Border Shard`, `250 gems`, `Omega Cache`",
            color=COLORS["legendary"],
        )
        await interaction.response.edit_message(embed=embed, view=self)


class ProfileShowcaseView(discord.ui.View):
    @discord.ui.button(label="Themes", emoji="🎨", style=discord.ButtonStyle.primary, custom_id="aoa:profile:themes", row=0)
    async def themes(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        lines = [f"{theme.border_emoji} **{theme.name}** — `{theme.banner}`" for theme in THEMES.values()]
        await interaction.response.edit_message(embed=discord.Embed(title="🎨 Profile Themes", description="\n".join(lines), color=COLORS["primary"]), view=self)

    @discord.ui.button(label="Badges", emoji="🏅", style=discord.ButtonStyle.secondary, custom_id="aoa:profile:badges", row=0)
    async def badges(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(title="🏅 Badge Showcase", description="🌌 Founder • 🗡️ First Clear • 👑 Raid MVP • 🌍 World First • 🏆 Season Champion", color=COLORS["warning"])
        await interaction.response.edit_message(embed=embed, view=self)


class CosmeticsView(discord.ui.View):
    @discord.ui.button(label="Catalog", emoji="💎", style=discord.ButtonStyle.primary, custom_id="aoa:cosmetics:catalog", row=0)
    async def catalog(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        lines = CosmeticsService().preview_lines({"theme_omega"})
        embed = discord.Embed(title="💎 Cosmetic Vault", description="\n\n".join(lines[:5]), color=COLORS["legendary"])
        await interaction.response.edit_message(embed=embed, view=self)


class SocialView(discord.ui.View):
    @discord.ui.button(label="Create Party", emoji="🤝", style=discord.ButtonStyle.primary, custom_id="aoa:social:party", row=0)
    async def party(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        party = SocialService().create_party(interaction.user.id, "dungeon_raid")
        embed = discord.Embed(title="🤝 Party Created", description=f"Party `{party.id}` is ready for Dungeon Raid matchmaking. Invite friends or queue as a party.", color=COLORS["success"])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Challenge", emoji="⚔️", style=discord.ButtonStyle.secondary, custom_id="aoa:social:challenge", row=0)
    async def challenge(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        invite = SocialService().create_invite(InviteType.CHALLENGE, interaction.user.id, interaction.user.id + 1, "anime_duel")
        invite = SocialService().create_invite(InviteType.CHALLENGE, interaction.user.id, interaction.user.id, "anime_duel")
        embed = discord.Embed(title="⚔️ Challenge Drafted", description=f"Invite `{invite.id}` expires at `{invite.expires_at:%H:%M UTC}`.", color=COLORS["danger"])
        await interaction.response.edit_message(embed=embed, view=self)


class GlobalFeedView(discord.ui.View):
    @discord.ui.button(label="Refresh Feed", emoji="🔄", style=discord.ButtonStyle.primary, custom_id="aoa:feed:refresh", row=0)
    async def refresh(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        service = GlobalFeedService()
        events = service.feed_page([
            service.rare_drop("Nova", "Omega Relic", "legendary", "Dungeon Raid"),
            service.leaderboard_dethrone("Astra", "ntmhaha", "Global XP"),
            service.level_up("Kai", 50),
        ])
        lines = [f"{self._icon(event.event_type)} **{event.title}**\n{event.body}" for event in events]
        await interaction.response.edit_message(embed=discord.Embed(title="🌐 Global Arcade Feed", description="\n\n".join(lines), color=COLORS["info"]), view=self)

    def _icon(self, event_type: FeedEventType) -> str:
        return {FeedEventType.RARE_DROP: "🎁", FeedEventType.LEADERBOARD: "🏆", FeedEventType.LEVEL_UP: "⭐"}.get(event_type, "🌌")


class WorldBossView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.boss = WorldBossService().scheduled_spawn()

    @discord.ui.button(label="Strike Boss", emoji="🐉", style=discord.ButtonStyle.danger, custom_id="aoa:boss:strike", row=0)
    async def strike(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        service = WorldBossService()
        service.apply_damage(self.boss, interaction.user.id, 25_000)
        rankings = service.damage_rankings(self.boss, 5)
        rank_lines = "\n".join(f"`#{rank}` <@{user_id}> — `{damage:,}`" for rank, user_id, damage in rankings) or "No damage yet"
        embed = discord.Embed(title=f"🐉 {self.boss.name}", description=f"{service.hp_visual(self.boss)}\n\n{rank_lines}", color=COLORS["danger"])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Tournament", emoji="🏆", style=discord.ButtonStyle.primary, custom_id="aoa:events:tournament", row=0)
    async def tournament(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(title="🏆 Tournament Center", description="Automated cups, signups, brackets, rewards, and spectating.", color=COLORS["warning"])
        await interaction.response.edit_message(embed=embed, view=TournamentView())

    @discord.ui.button(label="Global Feed", emoji="🌐", style=discord.ButtonStyle.secondary, custom_id="aoa:events:feed", row=0)
    async def feed(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(title="🌐 Global Arcade Feed", description="Rare drops, level ups, clan victories, world-firsts, and leaderboard dethrones.", color=COLORS["info"])
        await interaction.response.edit_message(embed=embed, view=GlobalFeedView())


class TournamentView(discord.ui.View):
    @discord.ui.button(label="Signup", emoji="🏆", style=discord.ButtonStyle.primary, custom_id="aoa:tournament:signup", row=0)
    async def signup(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        service = TournamentService()
        tournament = service.signup(service.create("daily_raid", "Daily Raid Cup", "dungeon_raid"), interaction.user.id)
        tournament = service.generate_bracket(tournament)
        embed = discord.Embed(title="🏆 Tournament Signup", description=f"You joined **{tournament.name}**. Bracket size: `{len(tournament.bracket)}` matches.", color=COLORS["warning"])
        await interaction.response.edit_message(embed=embed, view=self)


class ShopView(discord.ui.View):
    @discord.ui.button(label="Today’s Offers", emoji="🛒", style=discord.ButtonStyle.primary, custom_id="aoa:shop:offers", row=0)
    async def offers(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        offers = ShopService().rotating_offers(1)
        lines = [f"{offer.preview}\n**{offer.name}** — `{offer.price:,} {offer.price_currency}` • `{offer.rarity}`" for offer in offers]
        embed = discord.Embed(title="🛒 Omega Shop", description="\n\n".join(lines), color=COLORS["legendary"])
        await interaction.response.edit_message(embed=embed, view=self)
