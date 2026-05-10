import discord

from core.game_browser import GameBrowserService, GameTag
from core.sessions.manager import DistributedSessionManager
from games.dungeon_raid.runtime import DungeonRaidDirector, dungeon_to_dict
from core.retention.dopamine import DopamineService
from ui.cards.premium import PremiumCardFactory
from ui.embeds.premium import DIVIDER, PremiumEmbedFactory, PremiumPalette
from ui.embeds.theme import COLORS


class GameBrowserView(discord.ui.View):
    def __init__(self, session_manager: DistributedSessionManager | None, browser: GameBrowserService | None = None):
        super().__init__(timeout=300)
        self.session_manager = session_manager
        self.browser = browser or GameBrowserService()
        self.page_number = 1
        self.tag: GameTag | None = None

    def embed(self) -> discord.Embed:
        page = self.browser.page(page=self.page_number, tag=self.tag)
        lines = []
        for card in page.cards:
            tags = " ".join(f"`{tag.value}`" for tag in card.tags[:4])
            lines.append(f"**{card.name}** · {card.genre} · {'◆' * card.difficulty}\n{card.description[:120]}\n👥 Queue `{card.queue_size}` · {tags}")
        embed = PremiumEmbedFactory().compact_codex_page(
            "🎮 Omega Game Browser",
            ["A global MMO launcher with recommendations, queues, tags, and full discovery.", DIVIDER, *lines],
            PremiumPalette.OMEGA,
        )
        embed.set_footer(text=f"Game Browser • Page {page.page}/{page.total_pages} • Filter {self.tag.value if self.tag else 'all'}")
        return embed

    @discord.ui.button(label="Back", emoji="◀️", style=discord.ButtonStyle.secondary, custom_id="aoa:games:back", row=0)
    async def back(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.page_number = max(1, self.page_number - 1)
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Next", emoji="▶️", style=discord.ButtonStyle.secondary, custom_id="aoa:games:next", row=0)
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.page_number += 1
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Solo", emoji="🧭", style=discord.ButtonStyle.secondary, custom_id="aoa:games:solo", row=1)
    async def solo(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.tag = GameTag.SOLO
        self.page_number = 1
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Co-op", emoji="🤝", style=discord.ButtonStyle.secondary, custom_id="aoa:games:coop", row=1)
    async def coop(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.tag = GameTag.COOP
        self.page_number = 1
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="PvP", emoji="⚔️", style=discord.ButtonStyle.secondary, custom_id="aoa:games:pvp", row=1)
    async def pvp(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.tag = GameTag.PVP
        self.page_number = 1
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Trending", emoji="🔥", style=discord.ButtonStyle.primary, custom_id="aoa:games:trending", row=1)
    async def trending(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.tag = GameTag.TRENDING
        self.page_number = 1
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Dungeon Raid", emoji="🗡️", style=discord.ButtonStyle.success, custom_id="aoa:games:dungeon", row=2)
    async def dungeon(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if self.session_manager is None:
            await interaction.response.send_message("Dungeon sessions are unavailable in this runtime.", ephemeral=True)
            return
from core.sessions.manager import DistributedSessionManager
from games.dungeon_raid.runtime import DungeonRaidDirector, dungeon_to_dict
from ui.cards.premium import PremiumCardFactory
from ui.embeds.theme import COLORS


class GameLauncherView(discord.ui.View):
    def __init__(self, session_manager: DistributedSessionManager | None):
        super().__init__(timeout=None)
        self.session_manager = session_manager

    @discord.ui.button(label="Dungeon Raid", emoji="🗡️", style=discord.ButtonStyle.primary, custom_id="aoa:games:dungeon_raid", row=0)
    async def dungeon_raid(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="🗡️ Dungeon Raid",
            description=(
                "Procedural rooms, elite enemies, boss fights, co-op revives, class abilities, "
                "rarity loot, XP, coins, and daily dungeon rotations."
            ),
            color=COLORS["primary"],
        )
        embed.add_field(name="Recommended", value="Tier 1 • 1-5 players • 8 minutes", inline=True)
        embed.add_field(name="Controls", value="Buttons only: Start, Slash, Shield, Revive, Claim", inline=True)
        await interaction.response.edit_message(embed=embed, view=DungeonLobbyView(self.session_manager))

    @discord.ui.button(label="More Games", emoji="🎲", style=discord.ButtonStyle.secondary, custom_id="aoa:games:more", row=0)
    async def more_games(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="🎮 Arcade Catalog",
            description=(
                "Cosmic Fishing • Space Mining • Anime Duel • Zombie Survival • Pirate Raid • "
                "Memory Rush • Crystal Tower Defense • Frostkeep Dungeon • Skyward Empire\n\n"
                "These games are registered through reusable engines and will open from this launcher as their views are enabled."
            ),
            color=COLORS["info"],
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Home", emoji="🏠", style=discord.ButtonStyle.secondary, custom_id="aoa:games:home", row=1)
    async def home(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        from ui.views.home import ArcadeHomeView, build_home_embed

        admin_service = getattr(interaction.client, "admin_service", None)
        session_manager = getattr(interaction.client, "session_manager", self.session_manager)
        await interaction.response.edit_message(
            embed=build_home_embed(admin_service.settings.owner_display if admin_service else "ntmhaha"),
            view=ArcadeHomeView(admin_service, session_manager),
        )


class DungeonLobbyView(discord.ui.View):
    def __init__(self, session_manager: DistributedSessionManager | None):
        super().__init__(timeout=None)
        self.session_manager = session_manager

    @discord.ui.button(label="Start Tier 1", emoji="▶️", style=discord.ButtonStyle.success, custom_id="aoa:dungeon:start:t1", row=0)
    async def start(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if self.session_manager is None:
            await interaction.response.send_message("Session manager is not ready yet. Try again after startup health is green.", ephemeral=True)
            return
        run = DungeonRaidDirector().generate_run([interaction.user.id], tier=1)
        result = await self.session_manager.start_session(
            game_id="dungeon_raid",
            mode="solo",
            owner_discord_id=interaction.user.id,
            player_discord_ids=[interaction.user.id],
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            state={"dungeon": dungeon_to_dict(DungeonRaidDirector().start_run([interaction.user.id], tier=1))},
        )
        if not result.started or result.session is None:
            await interaction.response.send_message(f"You already have an active adventure: `{result.existing_session_id}`. Use `!recover`.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=DungeonCombatView.combat_embed(result.session.state["dungeon"], result.session.session_id), view=DungeonCombatView(self.session_manager, result.session.session_id))


GameLauncherView = GameBrowserView
            state={"tier": 1, "dungeon": dungeon_to_dict(run), "claimed": False},
        )
        if not result.started:
            await interaction.response.send_message(
                f"⚠️ You are already in session `{result.existing_session_id}`. Finish or recover it first.", ephemeral=True
            )
            return
        await interaction.response.edit_message(
            embed=DungeonCombatView.combat_embed(result.session.state["dungeon"], result.session.session_id),
            view=DungeonCombatView(self.session_manager, result.session.session_id),
        )

    @discord.ui.button(label="Back", emoji="↩️", style=discord.ButtonStyle.secondary, custom_id="aoa:dungeon:back", row=0)
    async def back(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            embed=discord.Embed(title="🎮 Game Launcher", description="Choose a game card below.", color=COLORS["primary"]),
            view=GameLauncherView(self.session_manager),
        )


class DungeonCombatView(discord.ui.View):
    def __init__(self, session_manager: DistributedSessionManager, session_id: str):
        super().__init__(timeout=None)
        self.session_manager = session_manager
        self.session_id = session_id

    @staticmethod
    def combat_embed(dungeon: dict, session_id: str) -> discord.Embed:
        room = dungeon["rooms"][dungeon["room_index"]]
        enemy = room["enemy"]
        log = "\n".join(f"▸ {DungeonCombatView._cinematic_log(line)}" for line in dungeon.get("combat_log", [])[-6:]) or "▸ The air fractures as the party enters the room..."
        hp_bar = "█" * max(1, min(12, round(enemy["hp"] / max(1, enemy.get("max_hp", enemy["hp"])) * 12)))
        embed = discord.Embed(
            title=f"⚔️ Dungeon Raid // {room['theme']}",
            description=f"Session `{session_id}`\n{DIVIDER}\n**{enemy['name']}** HP `{enemy['hp']}`  `{hp_bar:<12}`\n\n{log}",
            color=COLORS["danger"] if room.get("boss_room") else COLORS["primary"],
        )
        embed.add_field(name="Combat Tempo", value="⚡ Crit chains build momentum · 🛡️ Shields stabilize the run · ✨ Revives protect clutch clears", inline=False)
        embed.add_field(name="Encounter Read", value=("👑 Boss chamber" if room.get("boss_room") else "🩸 Elite patrol pressure") + " · watch for burst windows.", inline=False)
        embed.add_field(name="Loot", value=f"`{len(dungeon.get('loot', []))}` drops found", inline=True)
        embed.add_field(name="Room", value=f"`{dungeon['room_index'] + 1}/{len(dungeon['rooms'])}`", inline=True)
        embed.set_footer(text="Dungeon Raid • cinematic combat log • recoverable session")
        return embed


    @staticmethod
    def _cinematic_log(line: str) -> str:
        lowered = line.lower()
        if "crit" in lowered or "critical" in lowered:
            return f"💥 **CRITICAL** // {line}"
        if "shield" in lowered or "block" in lowered:
            return f"🛡️ Guarded // {line}"
        if "revive" in lowered:
            return f"✨ Revival // {line}"
        if "defeated" in lowered or "cleared" in lowered:
            return f"🏁 Finish // {line}"
        return line

    async def _action(self, interaction: discord.Interaction, ability_id: str) -> None:
        if not await self.session_manager.with_interaction_lock(self.session_id, interaction.user.id, str(interaction.id)):
            await interaction.response.send_message("⏳ That action is already resolving or was already processed.", ephemeral=True)
            return
        session = await self.session_manager.load_session(self.session_id)
        if session is None:
            await interaction.response.send_message("This dungeon session has expired. Use `!recover` if you had an active run.", ephemeral=True)
            return
        from games.dungeon_raid.runtime import DungeonRaidDirector, dungeon_from_dict

        run = DungeonRaidDirector().player_action(dungeon_from_dict(session.state["dungeon"]), interaction.user.id, ability_id)
        session.state["dungeon"] = dungeon_to_dict(run)
        await self.session_manager.touch(session)
        completed = run.room_index == len(run.rooms) - 1 and run.current_room.cleared
        await interaction.response.edit_message(embed=self.combat_embed(session.state["dungeon"], self.session_id), view=DungeonRewardView(self.session_manager, self.session_id) if completed else self)
        log = "\n".join(dungeon.get("combat_log", [])[-6:]) or "The party enters the dungeon..."
        embed = discord.Embed(
            title=f"🗡️ Dungeon Raid • {room['theme']}",
            description=f"Session `{session_id}`\nEnemy: **{enemy['name']}** • HP `{enemy['hp']}`\n\n{log}",
            color=COLORS["danger"] if room.get("boss_room") else COLORS["primary"],
        )
        embed.add_field(name="Loot", value=str(len(dungeon.get("loot", []))) + " drops found", inline=True)
        embed.add_field(name="Room", value=f"{dungeon['room_index'] + 1}/{len(dungeon['rooms'])}", inline=True)
        return embed

    async def _action(self, interaction: discord.Interaction, ability_id: str) -> None:
        async with self.session_manager.store.interaction_lock(self.session_id, interaction.user.id) as locked:
            if not locked:
                await interaction.response.send_message("⏳ Another action is resolving. Try again in a moment.", ephemeral=True)
                return
            session = await self.session_manager.load_session(self.session_id)
            if session is None:
                await interaction.response.send_message("This dungeon session has expired.", ephemeral=True)
                return
            from games.dungeon_raid.runtime import DungeonRaidDirector, dungeon_from_dict, dungeon_to_dict

            run = DungeonRaidDirector().player_action(dungeon_from_dict(session.state["dungeon"]), interaction.user.id, ability_id)
            session.state["dungeon"] = dungeon_to_dict(run)
            await self.session_manager.touch(session)
            completed = run.room_index == len(run.rooms) - 1 and run.current_room.cleared
            await interaction.response.edit_message(
                embed=self.combat_embed(session.state["dungeon"], self.session_id),
                view=DungeonRewardView(self.session_manager, self.session_id) if completed else self,
            )

    @discord.ui.button(label="Strike", emoji="⚔️", style=discord.ButtonStyle.primary, custom_id="aoa:dungeon:strike", row=0)
    async def strike(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._action(interaction, "shield_bash")

    @discord.ui.button(label="Shield", emoji="🛡️", style=discord.ButtonStyle.secondary, custom_id="aoa:dungeon:shield", row=0)
    async def shield(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._action(interaction, "bulwark")

    @discord.ui.button(label="Revive", emoji="✨", style=discord.ButtonStyle.secondary, custom_id="aoa:dungeon:revive", row=0)
    async def revive(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._action(interaction, "revive")


class DungeonRewardView(discord.ui.View):
    def __init__(self, session_manager: DistributedSessionManager, session_id: str):
        super().__init__(timeout=None)
        self.session_manager = session_manager
        self.session_id = session_id

    @discord.ui.button(label="Reveal Rewards", emoji="🎁", style=discord.ButtonStyle.success, custom_id="aoa:dungeon:claim", row=0)
    @discord.ui.button(label="Claim Rewards", emoji="🎁", style=discord.ButtonStyle.success, custom_id="aoa:dungeon:claim", row=0)
    async def claim(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        session = await self.session_manager.load_session(self.session_id)
        if session is None:
            await interaction.response.send_message("This dungeon session has expired.", ephemeral=True)
            return
        try:
            await self.session_manager.mark_reward_claimed(self.session_id, f"dungeon:{self.session_id}")
        except Exception:
            await interaction.response.send_message("Rewards already claimed for this run.", ephemeral=True)
            return
        dungeon = session.state["dungeon"]
        dungeon = session.state["dungeon"]
        if session.state.get("claimed"):
            await interaction.response.send_message("Rewards already claimed for this run.", ephemeral=True)
            return
        session.state["claimed"] = True
        await self.session_manager.touch(session)
        drops = dungeon.get("loot", [])
        xp = 180
        coins = 125
        persisted = False
        session_factory = getattr(interaction.client, "session_factory", None)
        if session_factory is not None:
            from core.gameplay.rewards import RewardPersistenceService

            async with session_factory() as db_session:
                await RewardPersistenceService(db_session).apply_dungeon_rewards(discord_id=interaction.user.id, xp=xp, coins=coins, drops=drops, nonce=self.session_id)
                await RewardPersistenceService(db_session).apply_dungeon_rewards(
                    discord_id=interaction.user.id,
                    xp=xp,
                    coins=coins,
                    drops=drops,
                    nonce=self.session_id,
                )
                await db_session.commit()
            persisted = True
        await self.session_manager.end_session(self.session_id)
        embed = PremiumCardFactory().loot_reward("Dungeon Complete", drops, xp=xp, coins=coins)
        if drops:
            reveal = DopamineService().loot_reveal(str(drops[0].get("name", drops[0].get("item_id", "Mystery Relic"))), str(drops[0].get("rarity", "rare")), "Dungeon Raid")
            embed.add_field(name=f"✨ {reveal.title}", value="\n".join(reveal.lines), inline=False)
        embed.add_field(name="Persistence", value="Saved to your global profile." if persisted else "Reward reveal complete; persistence service unavailable in this runtime.", inline=False)
        embed.add_field(
            name="Saved",
            value="XP, loot, economy transactions, and leaderboard hooks were saved." if persisted else "Rewards are ready; persistence service was unavailable in this runtime.",
            inline=False,
        )
        await interaction.response.edit_message(embed=embed, view=None)
