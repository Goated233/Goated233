import asyncio

import pytest

from services.guidance import GuidanceService
from utils.embeds import progress_bar


def test_memory_tag_suggestions_are_specific_and_safe():
    service = GuidanceService()
    tags = service.suggest_memory_tags("Our movie date after the apology call was so cute")
    assert "date" in tags
    assert "repair" in tags
    assert "call" in tags


def test_text_validation_normalizes_and_rejects_empty_entries():
    service = GuidanceService()
    assert service.validate_text("  I   miss   you  ") == "I miss you"
    with pytest.raises(ValueError, match="at least 3"):
        service.validate_text("x", min_len=3)


def test_progress_bar_caps_values():
    assert progress_bar(15, 10, width=5).startswith("▰▰▰▰▰")
    assert progress_bar(-1, 10, width=5).startswith("▱▱▱▱▱")


def test_card_service_generates_png_bytes_when_pillow_is_available():
    pytest.importorskip("PIL")
    from services.cards import CardService

    card = asyncio.run(CardService().mood_summary_card(7.5, 4, 8))
    assert card.getvalue().startswith(b"\x89PNG")
