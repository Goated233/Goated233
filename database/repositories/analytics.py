from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.platform import AnalyticsEvent


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(
        self, event_type: str, subject: str, metadata: dict, actor_discord_id: int | None = None
    ) -> AnalyticsEvent:
        event = AnalyticsEvent(
            actor_discord_id=actor_discord_id,
            event_type=event_type,
            subject=subject,
            metadata_json=metadata,
        )
        self.session.add(event)
        return event

    async def top_events(self, limit: int = 8) -> list[tuple[str, int]]:
        result = await self.session.execute(
            select(AnalyticsEvent.event_type, func.count())
            .group_by(AnalyticsEvent.event_type)
            .order_by(desc(func.count()))
            .limit(limit)
        )
        return [(str(row[0]), int(row[1])) for row in result.all()]
