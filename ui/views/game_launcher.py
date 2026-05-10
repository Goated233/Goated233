import discord
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

    @discord.ui.button(label="Claim Rewards", emoji="🎁", style=discord.ButtonStyle.success, custom_id="aoa:dungeon:claim", row=0)
    async def claim(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        session = await self.session_manager.load_session(self.session_id)
        if session is None:
            await interaction.response.send_message("This dungeon session has expired.", ephemeral=True)
            return
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
        embed.add_field(
            name="Saved",
            value="XP, loot, economy transactions, and leaderboard hooks were saved." if persisted else "Rewards are ready; persistence service was unavailable in this runtime.",
            inline=False,
        )
        await interaction.response.edit_message(embed=embed, view=None)
