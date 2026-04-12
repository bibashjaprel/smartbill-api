from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..core.database import Base, GUID
from .enums import StockMovementType


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    shop_id = Column(GUID, ForeignKey("shops.id"), nullable=False, index=True)
    product_id = Column(GUID, ForeignKey("products.id"), nullable=False, index=True)
    actor_user_id = Column(GUID, ForeignKey("users.id"), nullable=True, index=True)

    movement_type = Column(Enum(StockMovementType, name="stock_movement_type_enum"), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)

    reason = Column(Text, nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(String(120), nullable=True)

    unit_cost = Column(Numeric(10, 2), nullable=True)
    total_cost_impact = Column(Numeric(12, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    shop = relationship("Shop", back_populates="stock_movements")
    product = relationship("Product", back_populates="stock_movements")
    actor = relationship("User", back_populates="stock_movements")
