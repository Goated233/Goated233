from dataclasses import dataclass
from enum import StrEnum

from games.registry import ALL_GAMES


class GameTag(StrEnum):
    SOLO = "solo"
    COOP = "co-op"
    PVP = "pvp"
    EVENT = "event"
    SEASONAL = "seasonal"
    CLAN = "clan"
    TRENDING = "trending"


@dataclass(frozen=True)
class GameBrowserCard:
    id: str
    name: str
    genre: str
    description: str
    difficulty: int
    tags: tuple[GameTag, ...]
    queue_size: int
    recommendation_score: int


@dataclass(frozen=True)
class GameBrowserPage:
    cards: list[GameBrowserCard]
    page: int
    total_pages: int
    filter_tag: GameTag | None
    query: str | None


class GameBrowserService:
    def cards(self, recently_played: set[str] | None = None, favorites: set[str] | None = None) -> list[GameBrowserCard]:
        recent = recently_played or set()
        favs = favorites or set()
        cards = []
        for index, game in enumerate(ALL_GAMES):
            tags = self._tags_for(game.id, game.category, game.min_players, game.max_players)
            score = 50 + (30 if game.id in favs else 0) + (15 if game.id in recent else 0) + (10 if GameTag.TRENDING in tags else 0)
            cards.append(
                GameBrowserCard(
                    game.id,
                    game.name,
                    game.category,
                    game.description,
                    min(5, max(1, int(getattr(game, "config", {}).get("recommended_level", max(1, game.estimated_minutes // 5))) // 5 + 1)),
                    tags,
                    queue_size=(index * 17 + len(game.id)) % 240,
                    recommendation_score=score,
                )
            )
        return sorted(cards, key=lambda card: (card.recommendation_score, card.queue_size), reverse=True)

    def page(self, *, page: int = 1, page_size: int = 6, tag: GameTag | None = None, query: str | None = None, recently_played: set[str] | None = None, favorites: set[str] | None = None) -> GameBrowserPage:
        cards = self.cards(recently_played, favorites)
        if tag:
            cards = [card for card in cards if tag in card.tags]
        if query:
            lowered = query.lower()
            cards = [card for card in cards if lowered in card.name.lower() or lowered in card.description.lower() or lowered in card.genre.lower()]
        total_pages = max(1, (len(cards) + page_size - 1) // page_size)
        safe_page = min(max(1, page), total_pages)
        start = (safe_page - 1) * page_size
        return GameBrowserPage(cards[start : start + page_size], safe_page, total_pages, tag, query)

    def recommended_next(self, level: int, prefers_pvp: bool = False, has_clan: bool = False) -> list[GameBrowserCard]:
        cards = self.cards()
        if level < 5:
            return [card for card in cards if GameTag.SOLO in card.tags][:3]
        if prefers_pvp:
            return [card for card in cards if GameTag.PVP in card.tags][:3]
        if has_clan:
            return [card for card in cards if GameTag.CLAN in card.tags or GameTag.COOP in card.tags][:3]
        return cards[:3]

    def _tags_for(self, game_id: str, category: str, min_players: int, max_players: int) -> tuple[GameTag, ...]:
        tags = {GameTag.SOLO if min_players == 1 else GameTag.COOP}
        if max_players > 1:
            tags.add(GameTag.COOP)
        if any(token in game_id for token in ("duel", "mafia", "blackjack")):
            tags.add(GameTag.PVP)
        if any(token in game_id for token in ("boss", "raid", "cup")):
            tags.add(GameTag.EVENT)
        if category.lower() in {"strategy", "battle", "dungeon"}:
            tags.add(GameTag.CLAN)
        if game_id in {"dungeon_raid", "anime_duel", "boss_battle", "cosmic_fishing"}:
            tags.add(GameTag.TRENDING)
        if "season" in game_id or "cup" in game_id:
            tags.add(GameTag.SEASONAL)
        return tuple(sorted(tags, key=lambda tag: tag.value))
