import enum


class BillingCycle(str, enum.Enum):
    monthly = "monthly"
    yearly = "yearly"


class SubscriptionStatus(str, enum.Enum):
    trial = "trial"
    active = "active"
    past_due = "past_due"
    canceled = "canceled"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded"


class PaymentProvider(str, enum.Enum):
    esewa = "esewa"
    khalti = "khalti"
    stripe_future = "stripe_future"


class InvoiceStatus(str, enum.Enum):
    paid = "paid"
    partial = "partial"
    unpaid = "unpaid"


class StockMovementType(str, enum.Enum):
    sale = "sale"
    purchase = "purchase"
    adjustment = "adjustment"
    return_ = "return"


class ShopRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    staff = "staff"


class NotificationType(str, enum.Enum):
    system = "system"
    billing = "billing"
    inventory = "inventory"
    subscription = "subscription"


class AuditAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
