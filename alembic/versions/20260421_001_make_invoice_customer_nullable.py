"""make invoice customer nullable for walk-in bills

Revision ID: 20260421_001
Revises: 20260417_002
Create Date: 2026-04-21 20:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260421_001"
down_revision: Union[str, None] = "20260417_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "invoices",
        "customer_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "invoices",
        "customer_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
