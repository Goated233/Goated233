from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from database.repository import Repository

LOVE_LANGUAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "words": ("appreciate", "proud", "love you", "thank", "kind", "beautiful"),
    "quality_time": ("call", "movie", "game", "date", "together", "watch"),
    "acts": ("help", "fix", "support", "remind", "plan", "make"),
    "gifts": ("gift", "buy", "present", "surprise", "wishlist"),
    "touch": ("hug", "cuddle", "kiss", "hold"),
}


class RelationshipAnalyticsService:
    """Calculates relationship streaks, communication stats, and love-language signals."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    async def streak_days(self, couple_id: str) -> int:
        moods = await self.repo.list_recent("moods", couple_id, 90)
        days = {doc["created_at"].date() for doc in moods if "created_at" in doc}
        streak = 0
        today = datetime.now(timezone.utc).date()
        while today - timedelta(days=streak) in days:
            streak += 1
        return streak

    async def communication_stats(self, couple_id: str) -> dict[str, int]:
        stats = await self.repo.stats(couple_id)
        stats["checkins"] = await self.repo.db.checkins.count_documents({"couple_id": couple_id})
        stats["reviews"] = await self.repo.db.weekly_reviews.count_documents({"couple_id": couple_id})
        return stats

    async def love_language_scores(self, couple_id: str) -> dict[str, int]:
        texts: list[str] = []
        for collection in ("memories", "journals", "gifts", "promises", "bucket_items"):
            texts.extend(str(doc.get("text") or doc.get("body") or doc.get("description") or doc.get("title") or "") for doc in await self.repo.list_recent(collection, couple_id, 100))
        joined = "\n".join(texts).lower()
        return {name: sum(joined.count(keyword) for keyword in keywords) for name, keywords in LOVE_LANGUAGE_KEYWORDS.items()}

    async def mood_correlation(self, couple_id: str) -> dict[str, Any]:
        moods = await self.repo.list_recent("moods", couple_id, 30)
        if not moods:
            return {"average": 0, "entries": 0}
        scores = [int(doc.get("score", 0)) for doc in moods]
        return {"average": round(sum(scores) / len(scores), 2), "entries": len(scores), "latest": scores[0]}

    async def top_memory_tags(self, couple_id: str) -> list[tuple[str, int]]:
        memories = await self.repo.list_recent("memories", couple_id, 100)
        counter: Counter[str] = Counter(tag for doc in memories for tag in doc.get("tags", []))
        return counter.most_common(8)
