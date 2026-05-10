from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4


class EngineType(StrEnum):
    BATTLE = "battle"
    CARD = "card"
    STRATEGY = "strategy"
    REACTION = "reaction"
    STORY = "story"
    SOCIAL_DEDUCTION = "social_deduction"
    ECONOMY = "economy"


@dataclass(frozen=True)
class RewardRule:
    base_xp: int
    base_coins: int
    win_multiplier: float
    drops: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class GameDefinition:
    id: str
    name: str
    description: str
    engine_type: EngineType
    category: str
    min_players: int
    max_players: int
    estimated_minutes: int
    reward_rule: RewardRule
    config: dict


@dataclass
class GamePlayer:
    user_id: int
    discord_id: int
    display_name: str
    score: int = 0
    hp: int = 100
    metadata: dict = field(default_factory=dict)


@dataclass
class EngineSession:
    id: str
    definition: GameDefinition
    players: list[GamePlayer]
    mode: str
    round_number: int = 1
    state: dict = field(default_factory=dict)

    @classmethod
    def create(cls, definition: GameDefinition, players: list[GamePlayer], mode: str) -> "EngineSession":
        return cls(id=str(uuid4()), definition=definition, players=players, mode=mode)
