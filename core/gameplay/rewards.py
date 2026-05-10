from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.inventory import InventoryItem, Item
from database.models.platform import EconomyTransaction
from database.models.player import Profile, User
from core.economy.anti_abuse import EconomyGuard
from core.economy.balancing import EconomyBalancer
from core.profiles.progression import ProgressionService


class RewardPersistenceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.progression = ProgressionService()
        self.economy = EconomyBalancer()
        self.guard = EconomyGuard()

    async def apply_dungeon_rewards(
        self,
        *,
        discord_id: int,
        xp: int,
        coins: int,
        drops: list[dict],
        nonce: str,
    ) -> dict:
        user_result = await self.session.execute(select(User).where(User.discord_id == discord_id))
        user = user_result.scalar_one_or_none()
        if user is None:
            user = User(discord_id=discord_id, username_cache=str(discord_id))
            self.session.add(user)
            await self.session.flush()
            profile = Profile(user_id=user.id)
            self.session.add(profile)
            await self.session.flush()
            user.profile = profile
        profile_result = await self.session.execute(select(Profile).where(Profile.user_id == user.id))
        profile = profile_result.scalar_one()
        if xp <= 0 or coins < 0:
            raise ValueError("Dungeon rewards must be positive server-generated values")
        capped_coins = self.economy.reward_cap(profile.level, "dungeon_raid", coins)
        xp_key = self.economy.idempotency_key(user.id, "xp", nonce + ":xp")
        coin_key = self.economy.idempotency_key(user.id, "coins", nonce + ":coins")
        await self._assert_unique_transaction(xp_key)
        await self._assert_unique_transaction(coin_key)
        self.guard.validate_transaction(user.id, "xp", xp, profile.xp, xp_key)
        self.guard.validate_transaction(user.id, "coins", capped_coins, profile.coins, coin_key)
        capped_coins = self.economy.reward_cap(profile.level, "dungeon_raid", coins)
        progress = self.progression.apply_xp(profile.xp, xp, profile.level)
        profile.xp = progress.total_xp
        profile.level = progress.level
        profile.coins += capped_coins
        await self._transaction(user.id, "xp", xp, profile.xp, nonce + ":xp")
        await self._transaction(user.id, "coins", capped_coins, profile.coins, nonce + ":coins")
        for drop in drops:
            await self._grant_drop(user.id, drop)
        return {"level": profile.level, "xp": xp, "coins": capped_coins, "drops": drops, "titles": progress.unlocked_titles}

    async def _assert_unique_transaction(self, idempotency_key: str) -> None:
        existing = await self.session.execute(select(EconomyTransaction).where(EconomyTransaction.idempotency_key == idempotency_key))
        if existing.scalar_one_or_none() is not None:
            raise ValueError("Duplicate reward prevented")

    async def _transaction(self, user_id: int, currency: str, amount: int, balance_after: int, key: str) -> None:
        idempotency = self.economy.idempotency_key(user_id, currency, key)
        self.session.add(
            EconomyTransaction(
                user_id=user_id,
                currency=currency,
                amount=amount,
                balance_after=balance_after,
                reason="dungeon_raid_reward",
                idempotency_key=idempotency,
                metadata_json={"source": "DungeonRewardView"},
            )
        )

    async def _grant_drop(self, user_id: int, drop: dict) -> None:
        quantity = int(drop.get("quantity", 1))
        if quantity <= 0 or quantity > 100:
            raise ValueError("Invalid drop quantity")
        item_id = str(drop["item_id"])
        item = await self.session.get(Item, item_id)
        if item is None:
            item = Item(
                id=item_id,
                name=str(drop.get("name", item_id.replace("_", " ").title())),
                description="Discovered during Dungeon Raid.",
                rarity=str(drop.get("rarity", "common")),
                item_type="loot",
                stackable=True,
                metadata_json={"source": "dungeon_raid"},
            )
            self.session.add(item)
            await self.session.flush()
        inventory_result = await self.session.execute(
            select(InventoryItem).where(InventoryItem.user_id == user_id, InventoryItem.item_id == item_id)
        )
        inventory = inventory_result.scalar_one_or_none()
        if inventory is None:
            self.session.add(InventoryItem(user_id=user_id, item_id=item_id, quantity=quantity))
        else:
            inventory.quantity += quantity
            self.session.add(InventoryItem(user_id=user_id, item_id=item_id, quantity=int(drop.get("quantity", 1))))
        else:
            inventory.quantity += int(drop.get("quantity", 1))
