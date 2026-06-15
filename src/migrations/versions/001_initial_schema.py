"""Initial schema for Phase 2."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "work_division",
        sa.Column("code", sa.String(length=1), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "unit",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "classification_node",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("work_division_cd", sa.String(length=1), nullable=False),
        sa.Column("level", sa.SmallInteger(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["classification_node.id"]),
        sa.ForeignKeyConstraint(["work_division_cd"], ["work_division.code"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "work_division_cd",
            "level",
            "code",
            name="uq_classification_node_division_level_code",
        ),
    )
    op.create_index(
        "ix_classification_node_parent_id",
        "classification_node",
        ["parent_id"],
        unique=False,
    )
    op.create_table(
        "quantity_item",
        sa.Column("qty_calc_ctycl_cd", sa.String(length=32), nullable=False),
        sa.Column("work_division_cd", sa.String(length=1), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("spec", sa.Text(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("raw_unit", sa.String(length=100), nullable=True),
        sa.Column("leaf_node_id", sa.BigInteger(), nullable=True),
        sa.Column("lvl1_code", sa.String(length=32), nullable=True),
        sa.Column("lvl2_code", sa.String(length=32), nullable=True),
        sa.Column("lvl3_code", sa.String(length=32), nullable=True),
        sa.Column("lvl4_code", sa.String(length=32), nullable=True),
        sa.Column("lvl5_code", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["leaf_node_id"], ["classification_node.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["unit.id"]),
        sa.ForeignKeyConstraint(["work_division_cd"], ["work_division.code"]),
        sa.PrimaryKeyConstraint("qty_calc_ctycl_cd"),
    )
    op.create_index(
        "ix_quantity_item_classification_filter",
        "quantity_item",
        [
            "work_division_cd",
            "lvl1_code",
            "lvl2_code",
            "lvl3_code",
            "lvl4_code",
            "lvl5_code",
        ],
        unique=False,
    )
    op.create_index(
        "ix_quantity_item_name",
        "quantity_item",
        ["name"],
        unique=False,
    )
    op.create_index(
        "ix_quantity_item_work_division_cd",
        "quantity_item",
        ["work_division_cd"],
        unique=False,
    )
    op.create_table(
        "market_price",
        sa.Column("qty_calc_ctycl_cd", sa.String(length=32), nullable=False),
        sa.Column("product_name", sa.String(length=500), nullable=True),
        sa.Column("spec", sa.Text(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("raw_unit", sa.String(length=100), nullable=True),
        sa.Column("material_cost", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("labor_cost", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("expense_cost", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("apply_condition", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["qty_calc_ctycl_cd"], ["quantity_item.qty_calc_ctycl_cd"]),
        sa.ForeignKeyConstraint(["unit_id"], ["unit.id"]),
        sa.PrimaryKeyConstraint("qty_calc_ctycl_cd"),
    )


def downgrade() -> None:
    op.drop_table("market_price")
    op.drop_index("ix_quantity_item_work_division_cd", table_name="quantity_item")
    op.drop_index("ix_quantity_item_name", table_name="quantity_item")
    op.drop_index("ix_quantity_item_classification_filter", table_name="quantity_item")
    op.drop_table("quantity_item")
    op.drop_index("ix_classification_node_parent_id", table_name="classification_node")
    op.drop_table("classification_node")
    op.drop_table("unit")
    op.drop_table("work_division")
