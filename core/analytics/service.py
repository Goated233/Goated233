from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.analytics import AnalyticsRepository


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.repository = AnalyticsRepository(session)

    async def record_button(self, custom_id: str, actor_discord_id: int) -> None:
        await self.repository.record(
            "button_click", custom_id, {"surface": "discord_view"}, actor_discord_id
        )
