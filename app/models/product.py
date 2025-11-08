from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base, GUID


class Product(Base):
    __tablename__ = "products"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    unit = Column(String(50), default='piece')
    category = Column(String(100))
    shop_id = Column(GUID, ForeignKey("shops.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    cost_price = Column(Numeric(10, 2), nullable=True)
    min_stock_level = Column(Integer, default=0)
    sku = Column(String(100), unique=True, nullable=True)

    # Relationships
    shop = relationship("Shop", back_populates="products")
    bill_items = relationship("BillItem", back_populates="product")
