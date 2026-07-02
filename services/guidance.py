from __future__ import annotations

import re

TAG_RULES: dict[str, tuple[str, ...]] = {
    "call": ("call", "voice", "facetime"),
    "date": ("date", "movie", "dinner", "walk"),
    "repair": ("sorry", "apolog", "forgive", "fixed"),
    "sweet": ("love", "cute", "miss", "hug", "kiss"),
    "milestone": ("anniversary", "first", "finally", "met"),
    "gaming": ("game", "minecraft", "roblox", "valorant", "fortnite"),
}


class GuidanceService:
    """Provides non-AI validation, tag suggestions, and guided conversation copy."""

    def suggest_memory_tags(self, text: str) -> list[str]:
        lowered = text.lower()
        tags = [tag for tag, words in TAG_RULES.items() if any(word in lowered for word in words)]
        if not tags:
            tags.append("everyday")
        return tags[:5]

    def validate_text(self, text: str, *, min_len: int = 3, max_len: int = 1500) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if len(cleaned) < min_len:
            raise ValueError(f"Please share at least {min_len} meaningful characters so I can help properly.")
        if len(cleaned) > max_len:
            raise ValueError(f"Please keep this under {max_len} characters. You can split it into multiple entries.")
        return cleaned
