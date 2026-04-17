"""saas multitenant refactor

Revision ID: 20260412_001
Revises: 
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260412_001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


billing_cycle_enum = postgresql.ENUM("monthly", "yearly", name="billing_cycle_enum", create_type=False)
subscription_status_enum = postgresql.ENUM("trial", "active", "past_due", "canceled", name="subscription_status_enum", create_type=False)
payment_status_enum = postgresql.ENUM("pending", "succeeded", "failed", "refunded", name="payment_status_enum", create_type=False)
payment_provider_enum = postgresql.ENUM("esewa", "khalti", "stripe_future", name="payment_provider_enum", create_type=False)
invoice_status_enum = postgresql.ENUM("paid", "partial", "unpaid", name="invoice_status_enum", create_type=False)
stock_movement_type_enum = postgresql.ENUM("sale", "purchase", "adjustment", "return", name="stock_movement_type_enum", create_type=False)
shop_role_enum = postgresql.ENUM("owner", "admin", "staff", name="shop_role_enum", create_type=False)
notification_type_enum = postgresql.ENUM("system", "billing", "inventory", "subscription", name="notification_type_enum", create_type=False)
audit_action_enum = postgresql.ENUM("create", "update", "delete", name="audit_action_enum", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    billing_cycle_enum.create(bind, checkfirst=True)
    subscription_status_enum.create(bind, checkfirst=True)
    payment_status_enum.create(bind, checkfirst=True)
    payment_provider_enum.create(bind, checkfirst=True)
    invoice_status_enum.create(bind, checkfirst=True)
    stock_movement_type_enum.create(bind, checkfirst=True)
    shop_role_enum.create(bind, checkfirst=True)
    notification_type_enum.create(bind, checkfirst=True)
    audit_action_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("role", sa.String(length=50), nullable=False, server_default=sa.text("'employee'")),
        sa.Column("google_id", sa.String(length=255), nullable=True, unique=True),
        sa.Column("profile_picture", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "shops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("subscription_plan", sa.String(length=50), nullable=False, server_default=sa.text("'trial'")),
        sa.Column("subscription_status", sa.String(length=30), nullable=False, server_default=sa.text("'active'")),
        sa.Column("billing_cycle", sa.String(length=20), nullable=False, server_default=sa.text("'monthly'")),
        sa.Column("manual_billing_amount", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("next_billing_date", sa.DateTime(), nullable=True),
        sa.Column("subscription_started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("subscription_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("udharo_balance", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("unit", sa.String(length=50), nullable=False, server_default=sa.text("'piece'")),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("cost_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("min_stock_level", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("sku", sa.String(length=100), nullable=True),
        sa.UniqueConstraint("shop_id", "sku", name="uq_products_shop_sku"),
    )

    op.create_table(
        "user_shop_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("role", shop_role_enum, nullable=False, server_default=sa.text("'staff'")),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "shop_id", name="uq_user_shop_roles_user_shop"),
    )

    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("billing_cycle", billing_cycle_enum, nullable=False),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_plans_created_at", "plans", ["created_at"])

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("status", subscription_status_enum, nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_shop_id", "subscriptions", ["shop_id"])
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"])
    op.create_index("ix_subscriptions_created_at", "subscriptions", ["created_at"])
    op.create_index("ix_subscriptions_shop_status", "subscriptions", ["shop_id", "status"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", payment_status_enum, nullable=False),
        sa.Column("provider", payment_provider_enum, nullable=False),
        sa.Column("transaction_ref", sa.String(length=255), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_payments_subscription_id", "payments", ["subscription_id"])
    op.create_index("ix_payments_created_at", "payments", ["created_at"])
    op.create_index("ix_payments_transaction_ref", "payments", ["transaction_ref"])

    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("status", invoice_status_enum, nullable=False, server_default="unpaid"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_invoices_shop_id", "invoices", ["shop_id"])
    op.create_index("ix_invoices_customer_id", "invoices", ["customer_id"])
    op.create_index("ix_invoices_created_at", "invoices", ["created_at"])
    op.create_index("ix_invoices_shop_status", "invoices", ["shop_id", "status"])

    op.create_table(
        "invoice_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_invoice_items_invoice_id", "invoice_items", ["invoice_id"])
    op.create_index("ix_invoice_items_product_id", "invoice_items", ["product_id"])
    op.create_index("ix_invoice_items_created_at", "invoice_items", ["created_at"])

    op.create_table(
        "invoice_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("method", sa.String(length=50), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_invoice_payments_invoice_id", "invoice_payments", ["invoice_id"])
    op.create_index("ix_invoice_payments_created_at", "invoice_payments", ["created_at"])

    op.create_table(
        "inventory_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("threshold_quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_inventory_alerts_shop_id", "inventory_alerts", ["shop_id"])
    op.create_index("ix_inventory_alerts_product_id", "inventory_alerts", ["product_id"])
    op.create_index("ix_inventory_alerts_created_at", "inventory_alerts", ["created_at"])
    op.create_index("ix_inventory_alerts_shop_product", "inventory_alerts", ["shop_id", "product_id"], unique=True)

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", notification_type_enum, nullable=False),
        sa.Column("message", sa.String(length=1000), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", audit_action_enum, nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    inspector = sa.inspect(bind)
    legacy_tables = inspector.get_table_names()
    if "udharo_transactions" in legacy_tables:
        op.drop_table("udharo_transactions")
    if "bill_items" in legacy_tables:
        op.drop_table("bill_items")
    if "bills" in legacy_tables:
        op.drop_table("bills")



def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_inventory_alerts_shop_product", table_name="inventory_alerts")
    op.drop_index("ix_inventory_alerts_created_at", table_name="inventory_alerts")
    op.drop_index("ix_inventory_alerts_product_id", table_name="inventory_alerts")
    op.drop_index("ix_inventory_alerts_shop_id", table_name="inventory_alerts")
    op.drop_table("inventory_alerts")

    op.drop_index("ix_invoice_payments_created_at", table_name="invoice_payments")
    op.drop_index("ix_invoice_payments_invoice_id", table_name="invoice_payments")
    op.drop_table("invoice_payments")

    op.drop_index("ix_invoice_items_created_at", table_name="invoice_items")
    op.drop_index("ix_invoice_items_product_id", table_name="invoice_items")
    op.drop_index("ix_invoice_items_invoice_id", table_name="invoice_items")
    op.drop_table("invoice_items")

    op.drop_index("ix_invoices_shop_status", table_name="invoices")
    op.drop_index("ix_invoices_created_at", table_name="invoices")
    op.drop_index("ix_invoices_customer_id", table_name="invoices")
    op.drop_index("ix_invoices_shop_id", table_name="invoices")
    op.drop_table("invoices")

    op.drop_index("ix_payments_transaction_ref", table_name="payments")
    op.drop_index("ix_payments_created_at", table_name="payments")
    op.drop_index("ix_payments_subscription_id", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_subscriptions_shop_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_created_at", table_name="subscriptions")
    op.drop_index("ix_subscriptions_plan_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_shop_id", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("ix_plans_created_at", table_name="plans")
    op.drop_table("plans")

    bind = op.get_bind()
    audit_action_enum.drop(bind, checkfirst=True)
    notification_type_enum.drop(bind, checkfirst=True)
    shop_role_enum.drop(bind, checkfirst=True)
    stock_movement_type_enum.drop(bind, checkfirst=True)
    invoice_status_enum.drop(bind, checkfirst=True)
    payment_provider_enum.drop(bind, checkfirst=True)
    payment_status_enum.drop(bind, checkfirst=True)
    subscription_status_enum.drop(bind, checkfirst=True)
    billing_cycle_enum.drop(bind, checkfirst=True)
