from core.game_browser import GameBrowserService, GameTag
from core.help import HelpCategory, HelpCodexService
from core.onboarding import OnboardingService, StarterClass
from ui.embeds.premium import PremiumEmbedFactory, PlayerSnapshot, starter_home
from ui.views.game_launcher import GameBrowserView
from ui.views.home import build_home_embed


def test_premium_home_panel_contains_player_world_and_next_actions():
    embed = build_home_embed("owner", "Nova")
    assert "ALPHA OMEGA ARCADE" in embed.title
    field_names = [field.name for field in embed.fields]
    assert "👤 Player Command Center" in field_names
    assert "🌍 Live World Pulse" in field_names
    assert "✨ Continue Adventure" in field_names
    assert "!help" in embed.footer.text


def test_help_codex_covers_major_mmo_features_and_searches():
    service = HelpCodexService()
    categories = set(service.categories())
    assert {HelpCategory.START, HelpCategory.CLANS, HelpCategory.EVENTS, HelpCategory.MATCHMAKING, HelpCategory.RECOVERY}.issubset(categories)
    assert len(service.topics) >= 10
    results = service.search("recover dungeon rewards")
    assert results
    assert any(result.topic.category in {HelpCategory.RECOVERY, HelpCategory.DUNGEON, HelpCategory.REWARDS} for result in results)
    recommendations = service.recommendations(level=2, has_clan=False, active_session=True)
    assert recommendations[0].startswith("Recover")


def test_onboarding_flow_has_classes_rewards_and_next_actions():
    service = OnboardingService()
    flow = service.cinematic_flow()
    assert len(flow) == 4
    assert flow[0].action_label == "Start Adventure"
    loadout = service.loadout(StarterClass.RIFTWALKER)
    assert loadout.rewards["coins"] > 0
    assert any("Banner" in cosmetic for cosmetic in loadout.cosmetics)
    assert service.next_actions(set(), active_session_id="abc")[0] == "Recover session abc"


def test_game_browser_exposes_full_directory_filters_and_recommendations():
    browser = GameBrowserService()
    all_cards = browser.cards(favorites={"dungeon_raid"})
    assert len(all_cards) >= 20
    page = browser.page(tag=GameTag.TRENDING, page_size=4)
    assert page.cards
    assert all(GameTag.TRENDING in card.tags for card in page.cards)
    assert browser.page(query="dungeon").cards[0].name
    assert browser.recommended_next(level=1)


def test_game_browser_view_and_profile_embeds_are_mobile_compact():
    view = GameBrowserView(session_manager=None)
    embed = view.embed()
    assert "Omega Game Browser" in embed.title
    assert len(embed.description) < 4096
    profile = PremiumEmbedFactory().profile_card(PlayerSnapshot(username="Nova", level=9, xp=100, next_level_xp=200))
    assert len(profile.fields) >= 3
    home = PremiumEmbedFactory().home(starter_home("Nova"))
    assert len(home.fields) >= 5
