"""make product sku unique per shop

Revision ID: 20260417_002
Revises: 20260417_001
Create Date: 2026-04-17 00:00:01.000000

"""
import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260417_002"
down_revision: Union[str, None] = "20260417_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger(__name__)


def _can_alter_products_table(bind) -> bool:
    row = bind.execute(
        sa.text(
            """
            SELECT r.rolname = current_user AS is_owner
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_roles r ON r.oid = c.relowner
            WHERE n.nspname = current_schema()
              AND c.relname = 'products'
              AND c.relkind = 'r'
            """
        )
    ).first()
    return bool(row and row.is_owner)


def _drop_existing_sku_uniques(bind) -> None:
    if not _can_alter_products_table(bind):
        logger.warning(
            "Skipping products SKU constraint migration because current DB role does not own the products table"
        )
        return

    inspector = sa.inspect(bind)
    uniques = inspector.get_unique_constraints("products")
    for uq in uniques:
        cols = uq.get("column_names") or []
        if cols == ["sku"]:
            op.drop_constraint(uq["name"], "products", type_="unique")


def upgrade() -> None:
    bind = op.get_bind()
    _drop_existing_sku_uniques(bind)

    if not _can_alter_products_table(bind):
        return

    inspector = sa.inspect(bind)
    existing_uniques = {uq["name"] for uq in inspector.get_unique_constraints("products") if uq.get("name")}
    if "uq_products_shop_sku" not in existing_uniques:
        op.create_unique_constraint("uq_products_shop_sku", "products", ["shop_id", "sku"])


def downgrade() -> None:
    bind = op.get_bind()
    if not _can_alter_products_table(bind):
        logger.warning(
            "Skipping downgrade of products SKU constraint because current DB role does not own the products table"
        )
        return

    inspector = sa.inspect(bind)
    existing_uniques = {uq["name"] for uq in inspector.get_unique_constraints("products") if uq.get("name")}

    if "uq_products_shop_sku" in existing_uniques:
        op.drop_constraint("uq_products_shop_sku", "products", type_="unique")

    # Restore old global unique behavior for backward compatibility
    existing_uniques = {uq["name"] for uq in inspector.get_unique_constraints("products") if uq.get("name")}
    if "uq_products_sku" not in existing_uniques:
        op.create_unique_constraint("uq_products_sku", "products", ["sku"])
