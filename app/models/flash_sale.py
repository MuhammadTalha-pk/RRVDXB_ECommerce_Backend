from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Decimal, Boolean, 
    TIMESTAMP, ARRAY, ForeignKey
)
from sqlalchemy.sql import func
from database import Base


class FlashSale(Base):
    __tablename__ = "flash_sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    flash_price = Column(Decimal(10, 2), nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())