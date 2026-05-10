from dataclasses import dataclass
from enum import StrEnum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.inventory import InventoryItem, Item


class EquipmentSlot(StrEnum):
    WEAPON = "weapon"
    ARMOR = "armor"
    TRINKET = "trinket"
    COSMETIC = "cosmetic"
    PET = "pet"


@dataclass(frozen=True)
class InventoryFilter:
    rarity: str | None = None
    item_type: str | None = None
    equipped: bool | None = None
    search: str | None = None
    sort: str = "rarity"
    page: int = 1
    page_size: int = 8


@dataclass(frozen=True)
class InventoryEntry:
    inventory_id: int
    item_id: str
    name: str
    description: str
    rarity: str
    item_type: str
    quantity: int
    equipped: bool
    slot: str | None


class InventoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_items(self, user_id: int, filters: InventoryFilter) -> list[InventoryEntry]:
        stmt = select(InventoryItem, Item).join(Item, Item.id == InventoryItem.item_id).where(InventoryItem.user_id == user_id)
        if filters.rarity:
            stmt = stmt.where(Item.rarity == filters.rarity)
        if filters.item_type:
            stmt = stmt.where(Item.item_type == filters.item_type)
        if filters.equipped is not None:
            stmt = stmt.where(InventoryItem.equipped == filters.equipped)
        if filters.search:
            stmt = stmt.where(Item.name.ilike(f"%{filters.search}%"))
        if filters.sort == "name":
            stmt = stmt.order_by(Item.name.asc())
        elif filters.sort == "quantity":
            stmt = stmt.order_by(InventoryItem.quantity.desc())
        else:
            stmt = stmt.order_by(Item.rarity.desc(), Item.name.asc())
        offset = max(0, filters.page - 1) * filters.page_size
        rows = await self.session.execute(stmt.offset(offset).limit(filters.page_size))
        return [self._entry(inventory, item) for inventory, item in rows.all()]

    async def grant_item(self, user_id: int, item: Item, quantity: int, metadata: dict | None = None) -> InventoryItem:
        existing = await self.session.execute(
            select(InventoryItem).where(InventoryItem.user_id == user_id, InventoryItem.item_id == item.id)
        )
        inventory_item = existing.scalar_one_or_none()
        if inventory_item and item.stackable:
            inventory_item.quantity += quantity
        elif inventory_item:
            inventory_item.quantity += quantity
        else:
            inventory_item = InventoryItem(user_id=user_id, item_id=item.id, quantity=quantity, metadata_json=metadata or {})
            self.session.add(inventory_item)
        return inventory_item

    async def equip(self, user_id: int, inventory_id: int) -> InventoryEntry:
        inventory_item = await self.session.get(InventoryItem, inventory_id)
        if inventory_item is None or inventory_item.user_id != user_id:
            raise ValueError("Inventory item not found")
        item = await self.session.get(Item, inventory_item.item_id)
        if item is None:
            raise ValueError("Item definition missing")
        slot = item.metadata_json.get("slot")
        if slot:
            rows = await self.session.execute(
                select(InventoryItem, Item).join(Item, Item.id == InventoryItem.item_id).where(InventoryItem.user_id == user_id)
            )
            for equipped_item, definition in rows.all():
                if definition.metadata_json.get("slot") == slot:
                    equipped_item.equipped = False
        inventory_item.equipped = True
        return self._entry(inventory_item, item)

    async def unequip(self, user_id: int, inventory_id: int) -> None:
        inventory_item = await self.session.get(InventoryItem, inventory_id)
        if inventory_item is None or inventory_item.user_id != user_id:
            raise ValueError("Inventory item not found")
        inventory_item.equipped = False

    def _entry(self, inventory: InventoryItem, item: Item) -> InventoryEntry:
        return InventoryEntry(
            inventory_id=inventory.id,
            item_id=item.id,
            name=item.name,
            description=item.description,
            rarity=item.rarity,
            item_type=item.item_type,
            quantity=inventory.quantity,
            equipped=inventory.equipped,
            slot=item.metadata_json.get("slot"),
        )
