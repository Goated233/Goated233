from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import discord

from ui.branding.identity import RARITY_PALETTE, THEMES, compact_stat
from ui.embeds.progress import progress_bar
from ui.embeds.theme import COLORS

DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
THIN_DIVIDER = "────── ✦ ──────"


class PremiumPalette(StrEnum):
    OMEGA = "omega"
    SOLAR = "solar"
    ABYSS = "abyss"
    MYTHIC = "mythic"
    SUCCESS = "success"
    DANGER = "danger"


PALETTE_COLORS = {
    PremiumPalette.OMEGA: COLORS["primary"],
    PremiumPalette.SOLAR: COLORS["legendary"],
    PremiumPalette.ABYSS: 0x111827,
    PremiumPalette.MYTHIC: RARITY_PALETTE["mythic"]["color"],
    PremiumPalette.SUCCESS: COLORS["success"],
    PremiumPalette.DANGER: COLORS["danger"],
}


@dataclass(frozen=True)
class PlayerSnapshot:
    username: str
    level: int = 1
    xp: int = 0
    next_level_xp: int = 1000
    coins: int = 0
    gems: int = 0
    player_class: str = "Vanguard"
    title: str = "New Light"
    clan: str | None = None
    seasonal_rank: str = "Unranked"
    favorite_game: str = "Dungeon Raid"
    active_quest: str = "Clear the Beginner Dungeon"
    active_session_id: str | None = None
    badges: tuple[str, ...] = ("🌌 Founder",)


@dataclass(frozen=True)
class WorldSnapshot:
    online_players: int = 128
    live_events: int = 3
    world_boss: str = "Void Titan"
    boss_ends_in: str = "2h 14m"
    active_clan_war: str = "Astral Wolves vs Void Ravens"
    season_name: str = "Season Zero: First Dawn"
    highlight: str = "Mythic loot rates boosted in the Frost Rift."
    region_status: str = "Void Sea is a contested warzone."
    active_tournament: str = "Omega Cup signups close soon"
    battle_pass: str = "Tier 12/50 • 550 XP to next cache"
    friend_activity: tuple[str, ...] = ("Mira queued Anime Duel", "Jax found an Epic Rune")
    clan_status: str = "No clan yet • Level 5 unlocks creation"
    social_notifications: tuple[str, ...] = ("2 friends online", "1 party invite pending")


@dataclass(frozen=True)
class HomePanelData:
    player: PlayerSnapshot
    world: WorldSnapshot = field(default_factory=WorldSnapshot)
    featured_games: tuple[str, ...] = ("Dungeon Raid", "Anime Duel", "World Boss", "Cosmic Fishing")
    recent_rewards: tuple[str, ...] = ("+180 XP", "+125 coins", "Rare Frost Rune")
    next_actions: tuple[str, ...] = ("Start Adventure", "Claim Daily", "Join a Party")


class PremiumEmbedFactory:
    """Cinematic Discord embed compositions used by persistent MMO panels."""

    def shell(self, title: str, description: str, palette: PremiumPalette = PremiumPalette.OMEGA) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=PALETTE_COLORS[palette], timestamp=datetime.now(UTC))
        embed.set_footer(text="Alpha Omega Arcade • persistent MMO world inside Discord")
        return embed

    def home(self, data: HomePanelData) -> discord.Embed:
        player = data.player
        world = data.world
        theme = THEMES["omega"]
        embed = self.shell(
            f"{theme.border_emoji} ALPHA OMEGA ARCADE",
            "**A living MMO launcher. Your profile, party, clan, quests, and world events persist across every server.**\n" + DIVIDER,
            PremiumPalette.OMEGA,
        )
        embed.add_field(
            name="👤 Player Command Center",
            value=(
                f"**{player.username}** · *{player.title}*\n"
                f"Level **{player.level}** {progress_bar(player.xp, player.next_level_xp, 12)}\n"
                f"`{player.xp:,}/{player.next_level_xp:,} XP` · **{player.player_class}**\n"
                f"{compact_stat('Coins', f'{player.coins:,}', '🪙')}  {compact_stat('Gems', f'{player.gems:,}', '💎')}\n"
                f"🛡️ **Clan:** {player.clan or 'No clan yet'} · 🏅 **Season:** `{player.seasonal_rank}`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🌍 Live World Pulse",
            value=(
                f"👥 `{world.online_players:,}` players online · 🌐 `{world.live_events}` live events\n"
                f"🐉 **{world.world_boss}** ends in `{world.boss_ends_in}`\n"
                f"⚔️ **Clan War:** {world.active_clan_war}\n"
                f"✨ {world.highlight}\n"
                f"🗺️ {world.region_status}"
            ),
            inline=False,
        )
        embed.add_field(name="🎮 Featured Launch Deck", value="\n".join(f"`{idx}` ✦ **{game}**" for idx, game in enumerate(data.featured_games, 1)), inline=True)
        embed.add_field(name="🎁 Recent Dopamine", value="\n".join(f"• {reward}" for reward in data.recent_rewards), inline=True)
        embed.add_field(name="🎟️ Season + Tournament", value=f"**Battle Pass:** {world.battle_pass}\n🏆 {world.active_tournament}", inline=False)
        embed.add_field(name="🤝 Social Pulse", value="\n".join([*(f"• {line}" for line in world.friend_activity), f"🛡️ {world.clan_status}", *(f"🔔 {note}" for note in world.social_notifications)]), inline=False)
        embed.add_field(name="✨ Continue Adventure", value="\n".join(f"**{idx}.** {action}" for idx, action in enumerate(data.next_actions, 1)), inline=False)
        embed.set_author(name=world.season_name)
        return embed

    def profile_card(self, player: PlayerSnapshot) -> discord.Embed:
        embed = self.shell(
            f"🌌 {player.username} • {player.title}",
            f"{DIVIDER}\nA collectible prestige card with showcase slots, badges, cosmetics, and seasonal identity.",
            PremiumPalette.MYTHIC,
        )
        embed.add_field(name="Progression", value=f"Level **{player.level}** {progress_bar(player.xp, player.next_level_xp, 14)}\n`{player.xp:,}/{player.next_level_xp:,}` XP", inline=False)
        embed.add_field(name="Identity", value=f"⚔️ **Class:** {player.player_class}\n🛡️ **Clan:** {player.clan or 'Seeking guild'}\n🎮 **Favorite:** {player.favorite_game}", inline=True)
        embed.add_field(name="Wallet", value=f"🪙 `{player.coins:,}` coins\n💎 `{player.gems:,}` gems\n🏅 `{player.seasonal_rank}`", inline=True)
        embed.add_field(name="Showcase", value="\n".join(player.badges), inline=False)
        return embed

    def world_announcement(self, title: str, body: str, rarity: str = "legendary") -> discord.Embed:
        rarity_meta = RARITY_PALETTE.get(rarity, RARITY_PALETTE["legendary"])
        embed = discord.Embed(
            title=f"{rarity_meta['emoji']} WORLD SIGNAL // {title.upper()}",
            description=f"{DIVIDER}\n{body}\n{THIN_DIVIDER}\n*The Omega network is alive. Someone, somewhere, just changed the world.*",
            color=rarity_meta["color"],
            timestamp=datetime.now(UTC),
        )
        embed.set_footer(text=f"Global Feed • {rarity_meta['label']} signal")
        return embed

    def recovery_prompt(self, session_id: str, game_name: str, updated_at: datetime | None = None) -> discord.Embed:
        age = "moments ago"
        if updated_at:
            minutes = max(0, round((datetime.now(UTC) - updated_at).total_seconds() / 60))
            age = f"{minutes}m ago"
        embed = self.shell(
            "🔄 Continue Your Run",
            f"A recoverable **{game_name}** session was found.\nSession `{session_id}` · last seen `{age}`\n\nUse **Recover** to resume safely without losing progress.",
            PremiumPalette.SOLAR,
        )
        embed.add_field(name="Protection", value="Session locks, reward idempotency, and reconnect tokens prevent duplicate progress while restoring your run.", inline=False)
        return embed


    def reward_reveal(self, reveal) -> discord.Embed:
        embed = discord.Embed(
            title=f"✨ {reveal.title}",
            description=f"{DIVIDER}\n" + "\n".join(reveal.lines) + f"\n{THIN_DIVIDER}\n**Next:** {reveal.next_hook}",
            color=reveal.color,
            timestamp=datetime.now(UTC),
        )
        embed.add_field(name="Share Prompt", value=reveal.share_text, inline=False)
        embed.set_footer(text=f"Reward Reveal • {reveal.intensity.value} moment")
        return embed

    def social_share_card(self, card) -> discord.Embed:
        embed = self.shell(
            f"{card.accent} {card.title}",
            f"{DIVIDER}\n{card.body}\n{THIN_DIVIDER}\n**Action:** {card.call_to_action}",
            PremiumPalette.MYTHIC,
        )
        if card.compare_lines:
            embed.add_field(name="Social Hooks", value="\n".join(f"• {line}" for line in card.compare_lines), inline=False)
        return embed

    def living_world(self, snapshot, lines: list[str]) -> discord.Embed:
        embed = self.shell(
            "📡 Living World Broadcast",
            f"{DIVIDER}\n" + "\n".join(lines) + f"\n{THIN_DIVIDER}\n`{snapshot.online_count:,}` players visible across the Omega network.",
            PremiumPalette.SOLAR,
        )
        embed.add_field(name="Friend Activity", value="\n".join(f"• {line}" for line in snapshot.friend_activity), inline=True)
        embed.add_field(name="Clan Activity", value="\n".join(f"• {line}" for line in snapshot.clan_activity), inline=True)
        embed.add_field(name="Notifications", value="\n".join(f"🔔 {line}" for line in snapshot.social_notifications), inline=False)
        return embed

    def compact_codex_page(self, title: str, lines: list[str], palette: PremiumPalette = PremiumPalette.OMEGA) -> discord.Embed:
        clipped = [line[:240] for line in lines[:8]]
        return self.shell(title, f"{DIVIDER}\n" + "\n".join(clipped), palette)


def countdown_label(end_time: datetime, now: datetime | None = None) -> str:
    delta = end_time - (now or datetime.now(UTC))
    seconds = max(0, round(delta.total_seconds()))
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"


def starter_home(username: str = "New Adventurer") -> HomePanelData:
    return HomePanelData(
        player=PlayerSnapshot(username=username, level=1, xp=120, next_level_xp=1000, coins=500, gems=25),
        world=WorldSnapshot(online_players=342, live_events=4, boss_ends_in=countdown_label(datetime.now(UTC) + timedelta(hours=2, minutes=14))),
    )
