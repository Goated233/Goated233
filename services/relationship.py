from datetime import datetime, timezone
from typing import Any
from database.repository import Repository


class RelationshipService:
    """Business rules for couple linking and active relationship lookup."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    async def link_request(self, guild_id: int, author_id: int, partner_id: int) -> str:
        existing = await self.repo.get_couple_for_user(guild_id, author_id)
        if existing:
            return str(existing['_id'])
        return await self.repo.create('couples', {'guild_id': guild_id, 'partner_a_id': author_id, 'partner_b_id': partner_id, 'status': 'pending'})

    async def accept(self, guild_id: int, user_id: int) -> bool:
        result = await self.repo.db.couples.update_one({'guild_id': guild_id, 'partner_b_id': user_id, 'status': 'pending'}, {'$set': {'status': 'active', 'linked_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc)}})
        return result.modified_count == 1

    async def require_couple(self, guild_id: int, user_id: int) -> dict[str, Any]:
        couple = await self.repo.get_couple_for_user(guild_id, user_id)
        if not couple or couple.get('status') != 'active':
            raise ValueError('You need an active couple link first. Use `,couple link @partner` and have them run `,couple accept`.')
        return couple
