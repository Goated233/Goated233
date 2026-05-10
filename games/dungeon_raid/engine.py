from engines.battle.engine import BattleEngine
from engines.base.types import EngineSession
from games.dungeon_raid.runtime import DungeonRaidDirector, dungeon_from_dict, dungeon_to_dict


class DungeonRaidEngine(BattleEngine):
    def __init__(self, definition, sessions):
        super().__init__(definition, sessions)
        self.director = DungeonRaidDirector()

    async def handle_action(self, session: EngineSession, actor_discord_id: int, action: str) -> EngineSession:
        dungeon = session.state.get("dungeon")
        if dungeon is None:
            run = self.director.generate_run([player.discord_id for player in session.players], int(session.state.get("tier", 1)))
        else:
            run = dungeon_from_dict(dungeon)
        run = self.director.player_action(run, actor_discord_id, action)
        session.state["dungeon"] = dungeon_to_dict(run)
        session.state["combat_log"] = run.combat_log
        session.state["loot"] = run.loot
        session.round_number += 1
        await self.sessions.save(session.id, self.serialize(session))
        return session
