from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.player import Profile, User


class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_user(self, discord_id: int, username: str, avatar_url: str | None) -> User:
        result = await self.session.execute(select(User).where(User.discord_id == discord_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(discord_id=discord_id, username_cache=username, avatar_url=avatar_url)
            self.session.add(user)
            await self.session.flush()
            profile = Profile(user_id=user.id)
            self.session.add(profile)
            await self.session.flush()
            user.profile = profile
        else:
            user.username_cache = username
            user.avatar_url = avatar_url
        return user

    async def get_by_discord_id(self, discord_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.discord_id == discord_id))
        return result.scalar_one_or_none()
