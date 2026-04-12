import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base, GUID


class InventoryAlert(Base):
    __tablename__ = "inventory_alerts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    shop_id = Column(GUID, ForeignKey("shops.id"), nullable=False, index=True)
    product_id = Column(GUID, ForeignKey("products.id"), nullable=False, index=True)
    threshold_quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    shop = relationship("Shop", back_populates="inventory_alerts")
    product = relationship("Product", back_populates="inventory_alert")

    __table_args__ = (
        Index("ix_inventory_alerts_shop_product", "shop_id", "product_id", unique=True),
    )
