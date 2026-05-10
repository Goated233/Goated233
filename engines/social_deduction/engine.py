from engines.base.engine import BaseGameEngine
from engines.base.types import EngineSession


class SocialDeductionEngine(BaseGameEngine):
    async def handle_action(self, session: EngineSession, actor_discord_id: int, action: str) -> EngineSession:
        votes = session.state.setdefault("votes", {})
        if action.startswith("vote:"):
            votes[str(actor_discord_id)] = action.removeprefix("vote:")
        session.state["phase"] = "day" if session.round_number % 2 == 0 else "night"
        session.round_number += 1
        await self.sessions.save(session.id, self.serialize(session))
        return session
