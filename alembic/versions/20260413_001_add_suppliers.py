"""add suppliers table

Revision ID: 20260413_001
Revises: 20260412_001
Create Date: 2026-04-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260413_001"
down_revision: Union[str, None] = "20260412_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "suppliers" not in inspector.get_table_names():
        op.create_table(
            "suppliers",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("shop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shops.id"), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("contact_person", sa.String(length=255), nullable=True),
            sa.Column("phone", sa.String(length=30), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("suppliers")}
    if "ix_suppliers_shop_id" not in existing_indexes:
        op.create_index("ix_suppliers_shop_id", "suppliers", ["shop_id"])
    if "ix_suppliers_name" not in existing_indexes:
        op.create_index("ix_suppliers_name", "suppliers", ["name"])
    if "ix_suppliers_is_active" not in existing_indexes:
        op.create_index("ix_suppliers_is_active", "suppliers", ["is_active"])
    if "ix_suppliers_created_at" not in existing_indexes:
        op.create_index("ix_suppliers_created_at", "suppliers", ["created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "suppliers" in inspector.get_table_names():
        existing_indexes = {idx["name"] for idx in inspector.get_indexes("suppliers")}
        if "ix_suppliers_created_at" in existing_indexes:
            op.drop_index("ix_suppliers_created_at", table_name="suppliers")
        if "ix_suppliers_is_active" in existing_indexes:
            op.drop_index("ix_suppliers_is_active", table_name="suppliers")
        if "ix_suppliers_name" in existing_indexes:
            op.drop_index("ix_suppliers_name", table_name="suppliers")
        if "ix_suppliers_shop_id" in existing_indexes:
            op.drop_index("ix_suppliers_shop_id", table_name="suppliers")
        op.drop_table("suppliers")
