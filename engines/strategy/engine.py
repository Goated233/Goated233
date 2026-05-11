from engines.base.engine import BaseGameEngine
from engines.base.types import EngineSession


class StrategyEngine(BaseGameEngine):
    async def handle_action(self, session: EngineSession, actor_discord_id: int, action: str) -> EngineSession:
        session.state["last_action"] = {"actor": actor_discord_id, "action": action}
        session.round_number += 1
        await self.sessions.save(session.id, self.serialize(session))
        return session
