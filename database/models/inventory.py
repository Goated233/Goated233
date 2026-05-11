from sqlalchemy import JSON, BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import Base, TimestampMixin, json_default


class Item(Base, TimestampMixin):
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(512))
    rarity: Mapped[str] = mapped_column(String(32), index=True)
    item_type: Mapped[str] = mapped_column(String(64), index=True)
    stackable: Mapped[bool] = mapped_column(default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)


class InventoryItem(Base, TimestampMixin):
    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    equipped: Mapped[bool] = mapped_column(default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)

    __table_args__ = (UniqueConstraint("user_id", "item_id", name="uq_inventory_user_item"),)


class Cosmetic(Base, TimestampMixin):
    __tablename__ = "cosmetics"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    slot: Mapped[str] = mapped_column(String(64))
    rarity: Mapped[str] = mapped_column(String(32))
    price_gems: Mapped[int] = mapped_column(BigInteger, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=json_default)
