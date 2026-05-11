from datetime import UTC, datetime

from core.retention.dopamine import CelebrationIntensity, DopamineService
from core.social.viral import SocialCardType, SocialViralService
from core.world.living import LivingWorldService, WorldSignalType
from ui.embeds.premium import PremiumEmbedFactory, starter_home
from ui.views.game_launcher import DungeonCombatView
from ui.views.home import build_home_embed


def test_living_world_generates_non_empty_broadcasts_and_feed_events():
    service = LivingWorldService()
    snapshot = service.snapshot(seed=8, now=datetime(2026, 5, 10, 12, tzinfo=UTC))
    assert len(snapshot.signals) == 4
    assert snapshot.online_count > 0
    assert any(signal.signal_type == WorldSignalType.INVASION for signal in snapshot.signals)
    lines = service.dashboard_lines(snapshot)
    events = service.feed_events(snapshot)
    assert lines and all("**" in line for line in lines)
    assert len(events) == len(snapshot.signals)
    assert all(event.category == "world" for event in events)


def test_home_panel_includes_social_retention_and_world_urgency():
    embed = build_home_embed("owner", "Nova")
    names = [field.name for field in embed.fields]
    assert "🎟️ Season + Tournament" in names
    assert "🤝 Social Pulse" in names
    assert any("players online" in field.value for field in embed.fields)
    assert len(embed.description) < 900


def test_dopamine_reveals_and_social_cards_are_shareable():
    dopamine = DopamineService()
    streak = dopamine.streak_reveal(30, 500, 400, 50)
    loot = dopamine.loot_reveal("Omega Halo", "mythic", "Void Titan")
    assert streak.intensity == CelebrationIntensity.MYTHIC
    assert "Share" not in streak.next_hook
    assert loot.color != 0
    social = SocialViralService()
    card = social.rare_drop_card("Nova", "Omega Halo", "mythic")
    assert card.card_type == SocialCardType.RARE_DROP
    assert "Inspect" in " ".join(card.compare_lines)
    assert social.recommended_connections(1, [2, 3], [3, 4]) == [3, 4, 2]


def test_premium_factory_renders_living_world_reward_and_social_embeds():
    factory = PremiumEmbedFactory()
    snapshot = LivingWorldService().snapshot(seed=2)
    world_embed = factory.living_world(snapshot, LivingWorldService().dashboard_lines(snapshot))
    reward_embed = factory.reward_reveal(DopamineService().streak_reveal(7, 250, 200, 10))
    social_embed = factory.social_share_card(SocialViralService().achievement_card("Nova", "First Mythic Clear"))
    assert "Living World" in world_embed.title
    assert reward_embed.fields[0].name == "Share Prompt"
    assert social_embed.fields
    assert len(world_embed.description) < 1200


def test_combat_log_adds_cinematic_impact_markers():
    dungeon = {
        "room_index": 0,
        "rooms": [{"theme": "Frost Rift", "enemy": {"name": "Rift Knight", "hp": 80, "max_hp": 100}, "boss_room": False}],
        "combat_log": ["Nova landed a critical strike", "Shield absorbed the blow", "Room cleared"],
        "loot": [{"item_id": "frost_rune", "rarity": "rare", "name": "Frost Rune"}],
    }
    embed = DungeonCombatView.combat_embed(dungeon, "session-1")
    assert "💥 **CRITICAL**" in embed.description
    assert "🛡️ Guarded" in embed.description
    assert any(field.name == "Encounter Read" for field in embed.fields)


def test_starter_home_remains_compact_after_polish_expansion():
    embed = PremiumEmbedFactory().home(starter_home("Nova"))
    assert len(embed.fields) <= 7
    assert all(len(field.value) < 1024 for field in embed.fields)
