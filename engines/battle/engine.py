from engines.base.engine import BaseGameEngine
from engines.base.types import EngineSession


class BattleEngine(BaseGameEngine):
    async def handle_action(self, session: EngineSession, actor_discord_id: int, action: str) -> EngineSession:
        actor = next(player for player in session.players if player.discord_id == actor_discord_id)
        damage = 35 if action == "ultimate" else 18
        actor.score += damage
        session.state["boss_hp"] = max(0, int(session.state.get("boss_hp", 500)) - damage)
        session.round_number += 1
        if session.state["boss_hp"] == 0:
            actor.metadata["won"] = True
        await self.sessions.save(session.id, self.serialize(session))
        return session
