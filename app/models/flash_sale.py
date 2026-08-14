from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Integer, Boolean, TIMESTAMP, ForeignKey, Numeric
from sqlalchemy.sql import func

from app.core.database import Base


class FlashSale(Base):
    __tablename__ = "flash_sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    flash_price = Column(Numeric(10, 2), nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())