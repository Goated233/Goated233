import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")


def test_inventory_service_imports_when_sqlalchemy_available():
    from core.inventory.service import InventoryFilter

    filters = InventoryFilter(rarity="rare", page=2, page_size=4)
    assert filters.rarity == "rare"
    assert filters.page == 2


def test_leaderboard_service_imports_when_sqlalchemy_available():
    from core.leaderboards.service import LeaderboardService

    assert LeaderboardService.rank_icon(None, 1) == "🥇"
    assert LeaderboardService.rank_icon(None, 9) == "🔹"
