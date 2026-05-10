import asyncio
from sqlalchemy import select
from app.config import get_settings
from database.models.admin import AdminAssignment, AdminRole
from database.models.player import Profile, User
from database.session import create_engine, create_session_factory


async def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)
    async with factory() as session:
        result = await session.execute(select(User).where(User.discord_id == settings.owner_user_id))
        owner = result.scalar_one_or_none()
        if owner is None:
            owner = User(discord_id=settings.owner_user_id, username_cache=settings.owner_display)
            session.add(owner)
            await session.flush()
            session.add(Profile(user_id=owner.id, title="Platform Owner"))
        role_result = await session.execute(select(AdminRole).where(AdminRole.name == "owner"))
        role = role_result.scalar_one_or_none()
        if role is None:
            role = AdminRole(name="owner", hierarchy=10_000, description="Platform owner", managed=True)
            session.add(role)
            await session.flush()
        exists = await session.execute(select(AdminAssignment).where(AdminAssignment.user_id == owner.id, AdminAssignment.role_id == role.id))
        if exists.scalar_one_or_none() is None:
            session.add(AdminAssignment(user_id=owner.id, role_id=role.id, assigned_by_discord_id=settings.owner_user_id, reason="owner bootstrap"))
        await session.commit()
    await engine.dispose()
    print(f"Bootstrapped owner {settings.owner_display} ({settings.owner_user_id}).")


if __name__ == "__main__":
    asyncio.run(main())
