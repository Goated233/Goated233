from random import randint
from engines.base.engine import BaseGameEngine
from engines.base.types import EngineSession


class CardEngine(BaseGameEngine):
    async def handle_action(self, session: EngineSession, actor_discord_id: int, action: str) -> EngineSession:
        actor = next(player for player in session.players if player.discord_id == actor_discord_id)
        hand = int(actor.metadata.get("hand", 0))
        if action == "hit":
            hand += randint(1, 11)
            actor.metadata["hand"] = hand
        elif action == "stand":
            actor.metadata["stood"] = True
        actor.metadata["won"] = 18 <= hand <= 21
        session.round_number += 1
        await self.sessions.save(session.id, self.serialize(session))
        return session
