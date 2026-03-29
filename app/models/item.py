import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDType


class Category(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    items: Mapped[list["Item"]] = relationship(back_populates="category")


class Item(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    category: Mapped[Category | None] = relationship(back_populates="items")
