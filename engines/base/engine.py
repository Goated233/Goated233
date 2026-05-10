from abc import ABC, abstractmethod
from engines.base.types import EngineSession, GameDefinition, GamePlayer
from infra.redis.sessions import SessionStore


class BaseGameEngine(ABC):
    def __init__(self, definition: GameDefinition, sessions: SessionStore):
        self.definition = definition
        self.sessions = sessions

    async def start(self, players: list[GamePlayer], mode: str = "casual") -> EngineSession:
        session = EngineSession.create(self.definition, players, mode)
        await self.sessions.save(session.id, self.serialize(session))
        return session

    @abstractmethod
    async def handle_action(self, session: EngineSession, actor_discord_id: int, action: str) -> EngineSession:
        raise NotImplementedError

    async def rewards(self, session: EngineSession) -> list[dict]:
        rewards = []
        for index, player in enumerate(session.players):
            won = index == 0 or bool(player.metadata.get("won"))
            multiplier = self.definition.reward_rule.win_multiplier if won else 0.5
            rewards.append(
                {
                    "user_id": player.user_id,
                    "xp": round(self.definition.reward_rule.base_xp * multiplier),
                    "coins": round(self.definition.reward_rule.base_coins * multiplier),
                    "items": self.definition.reward_rule.drops if won else [],
                }
            )
        return rewards

    def serialize(self, session: EngineSession) -> dict:
        return {
            "id": session.id,
            "game_id": self.definition.id,
            "mode": session.mode,
            "round": session.round_number,
            "players": [player.__dict__ for player in session.players],
            "state": session.state,
        }
