from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, seoul_now


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=seoul_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=seoul_now,
        onupdate=seoul_now,
        nullable=False,
    )


class WorkDivision(TimestampMixin, Base):
    __tablename__ = "work_division"

    code: Mapped[str] = mapped_column(String(1), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    classification_nodes: Mapped[list[ClassificationNode]] = relationship(
        back_populates="work_division",
    )
    quantity_items: Mapped[list[QuantityItem]] = relationship(
        back_populates="work_division",
    )


class Unit(TimestampMixin, Base):
    __tablename__ = "unit"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class ClassificationNode(TimestampMixin, Base):
    __tablename__ = "classification_node"
    __table_args__ = (
        UniqueConstraint(
            "work_division_cd",
            "level",
            "code",
            name="uq_classification_node_division_level_code",
        ),
        Index("ix_classification_node_parent_id", "parent_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    work_division_cd: Mapped[str] = mapped_column(
        ForeignKey("work_division.code"),
        nullable=False,
    )
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("classification_node.id"),
    )

    work_division: Mapped[WorkDivision] = relationship(
        back_populates="classification_nodes",
    )
    parent: Mapped[ClassificationNode | None] = relationship(
        remote_side="ClassificationNode.id",
    )
    quantity_items: Mapped[list[QuantityItem]] = relationship(
        back_populates="leaf_node",
    )


class QuantityItem(TimestampMixin, Base):
    __tablename__ = "quantity_item"
    __table_args__ = (
        Index("ix_quantity_item_work_division_cd", "work_division_cd"),
        Index("ix_quantity_item_name", "name"),
        Index(
            "ix_quantity_item_classification_filter",
            "work_division_cd",
            "lvl1_code",
            "lvl2_code",
            "lvl3_code",
            "lvl4_code",
            "lvl5_code",
        ),
    )

    qty_calc_ctycl_cd: Mapped[str] = mapped_column(String(32), primary_key=True)
    work_division_cd: Mapped[str] = mapped_column(
        ForeignKey("work_division.code"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    spec: Mapped[str | None] = mapped_column(Text)
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("unit.id"))
    raw_unit: Mapped[str | None] = mapped_column(String(100))
    leaf_node_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("classification_node.id"),
    )
    lvl1_code: Mapped[str | None] = mapped_column(String(32))
    lvl2_code: Mapped[str | None] = mapped_column(String(32))
    lvl3_code: Mapped[str | None] = mapped_column(String(32))
    lvl4_code: Mapped[str | None] = mapped_column(String(32))
    lvl5_code: Mapped[str | None] = mapped_column(String(32))

    work_division: Mapped[WorkDivision] = relationship(back_populates="quantity_items")
    leaf_node: Mapped[ClassificationNode | None] = relationship(
        back_populates="quantity_items",
    )
    unit: Mapped[Unit | None] = relationship()
    market_price: Mapped[MarketPrice | None] = relationship(
        back_populates="quantity_item",
        uselist=False,
    )


class MarketPrice(TimestampMixin, Base):
    __tablename__ = "market_price"

    qty_calc_ctycl_cd: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("quantity_item.qty_calc_ctycl_cd"),
        primary_key=True,
    )
    product_name: Mapped[str | None] = mapped_column(String(500))
    spec: Mapped[str | None] = mapped_column(Text)
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("unit.id"))
    raw_unit: Mapped[str | None] = mapped_column(String(100))
    material_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    labor_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    expense_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    published_date: Mapped[date | None] = mapped_column(Date)
    apply_condition: Mapped[str | None] = mapped_column(Text)

    quantity_item: Mapped[QuantityItem] = relationship(back_populates="market_price")
    unit: Mapped[Unit | None] = relationship()
